"""Local check evidence and bounded scheduling; no phase/report acceptance policy."""
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import stat
import subprocess
import sys
import uuid

from .results import VerbError

STORE = ".planning/verification-receipts"
SCHEMA = 1
FIELDS = {"command", "sources", "environment", "independent", "resources", "timeout", "revision", "reuse", "purpose"}


def bad(message):
    raise VerbError(message, "bad-config")


def argv(command):
    if isinstance(command, str):
        command = command.split()  # Preserve the legacy string interpretation (no shell).
    elif isinstance(command, (list, tuple)):
        command = [str(part) for part in command]
    else:
        bad("verification command must be a string or argv list")
    if not command or not command[0] or any("\0" in part for part in command):
        bad("verification command must contain a nonempty executable and no NUL")
    return command


def names(value, field, nonempty=False):
    if not isinstance(value, list) or any(not isinstance(v, str) or not v for v in value):
        bad("verification " + field + " must be a list of nonempty strings")
    if nonempty and not value:
        bad("verification " + field + " must not be empty")
    if field == "environment" and os.name == "nt":
        value = [name.upper() for name in value]
    return sorted(set(value))


def normalise(commands, timeout):
    if not isinstance(commands, list):
        bad("verification.commands must be a list")
    result = []
    for entry in commands:
        if not isinstance(entry, dict):
            result.append(argv(entry))
            continue
        if set(entry) - FIELDS or "command" not in entry:
            bad("verification check mapping has unknown keys or no command")
        item = dict(entry, command=argv(entry["command"]))
        if "purpose" in item and (not isinstance(item["purpose"], str) or not item["purpose"].strip()):
            bad("verification purpose must be a nonempty string")
        for field in ("independent", "revision", "reuse"):
            if field in item and not isinstance(item[field], bool):
                bad("verification " + field + " must be boolean")
        for field in ("sources", "environment", "resources"):
            if field in item:
                item[field] = names(item[field], field, nonempty=field == "sources")
        for source in item.get("sources", []):
            path = PurePosixPath(source)
            if path.is_absolute() or ".." in path.parts or ":" in source or "\\" in source:
                bad("verification sources must be literal repository-relative paths")
            if any(part in {".git", "verification-receipts"} for part in path.parts):
                bad("verification sources must not include Git metadata or receipt storage")
        limit = item.get("timeout", timeout)
        if isinstance(limit, bool) or not isinstance(limit, (int, float)) or not math.isfinite(limit) or limit <= 0:
            bad("verification timeout must be a positive finite number")
        result.append(item)
    return result


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True).encode()).hexdigest()


def file_digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def git(root, *args):
    return subprocess.run(["git", *args], cwd=str(root), capture_output=True,
                          timeout=30, check=True).stdout


def inventory(root):
    # Tracked files remain relevant even if a later ignore rule matches them.
    raw = git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    return sorted({os.fsdecode(v) for v in raw.split(b"\0") if v
                   and os.fsdecode(v) != STORE and not os.fsdecode(v).startswith(STORE + "/")})


def fingerprint(root, paths, guarded=False):
    entries = []
    for name in paths:
        path = root / name
        path.resolve().relative_to(root)
        try:
            info = path.lstat()
        except FileNotFoundError:
            entries.append([name, "missing"])
            continue
        if stat.S_ISLNK(info.st_mode):
            # External symlink inputs cannot be inferred safely. Fail closed.
            target = path.resolve(strict=True)
            target.relative_to(root)
            if not target.is_file():
                raise ValueError("directory symlink input: " + name)
            entries.append([name, "symlink", os.readlink(path), file_digest(target)])
            if guarded:
                target_info = target.stat()
                entries.append([name, "target", target_info.st_mtime_ns,
                                target_info.st_ctime_ns, target_info.st_ino])
        elif stat.S_ISREG(info.st_mode):
            entries.append([name, stat.S_IMODE(info.st_mode), file_digest(path)])
        else:
            # Gitlinks and special files need an explicit project check strategy.
            raise ValueError("unsupported source input: " + name)
        if guarded:
            # Content keys permit reuse after a same-content edit between runs;
            # execution guards also catch rewrites/restores during this run.
            entries.append([name, info.st_mtime_ns, info.st_ctime_ns, info.st_ino])
    return digest(entries)


def snapshot(root, sources=None, guarded=False):
    if sources is None:
        paths = inventory(root)
    else:
        paths = set()
        for name in sources:
            path = root / name
            path.resolve().relative_to(root)
            if path.is_dir():
                for child in path.rglob("*"):
                    relative = child.relative_to(root).as_posix()
                    if ".git" in child.relative_to(root).parts or relative.startswith(STORE + "/"):
                        continue
                    if child.is_symlink() and child.is_dir():
                        raise ValueError("directory symlink input: " + relative)
                    if not child.is_dir():
                        paths.add(relative)
            else:
                paths.add(name)
        paths = sorted(paths)
    return fingerprint(root, paths, guarded)


def safe_snapshot(root, sources=None, guarded=False):
    try:
        return snapshot(root, sources, guarded)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def tail(path):
    with path.open("rb") as handle:
        handle.seek(max(0, path.stat().st_size - 8000))
        return handle.read().decode("utf-8", errors="replace")[-2000:]


def load_receipt(store, key, inputs):
    try:
        path = store / (key + ".json")
        if path.is_symlink():
            return None
        envelope = json.loads(path.read_text(encoding="utf-8"))
        receipt = envelope["receipt"]
        if envelope["sha256"] != digest(receipt) or receipt["schema"] != SCHEMA:
            return None
        if receipt["key"] != key or receipt["inputs"] != inputs:
            return None
        result = receipt["result"]
        if result["passed"] is not True or result["exit_code"] != 0 or result.get("error"):
            return None
        if result["snapshot_valid"] is not True or result["command"] != inputs["command"]:
            return None
        if not isinstance(result.get("tested_revision"), str) or not result["tested_revision"]:
            return None
        for stream in ("stdout", "stderr"):
            name = receipt[stream]["file"]
            if not isinstance(name, str) or Path(name).name != name or not name.endswith("." + stream + ".log"):
                return None
            log = store / name
            if log.is_symlink() or file_digest(log) != receipt[stream]["sha256"]:
                return None
            result[stream + "_tail"] = tail(log)
            result[stream + "_log"] = STORE + "/" + name
        return dict(result, reused=True, receipt=STORE + "/" + path.name)
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        return None


def save_receipt(store, key, inputs, result):
    receipt = {"schema": SCHEMA, "key": key, "inputs": inputs, "result": result,
               "recorded_at": datetime.now(timezone.utc).isoformat()}
    for stream in ("stdout", "stderr"):
        name = Path(result[stream + "_log"]).name
        receipt[stream] = {"file": name, "sha256": file_digest(store / name)}
    content = json.dumps({"receipt": receipt, "sha256": digest(receipt)}, sort_keys=True)
    temporary = store / (uuid.uuid4().hex + ".tmp")
    try:
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, store / (key + ".json"))
    finally:
        temporary.unlink(missing_ok=True)


def tool_identity(root, command, environment):
    executable = command[0]
    if os.path.dirname(executable):
        executable = str((root / executable).resolve())
    else:
        executable = shutil.which(executable, path=environment.get("PATH"))
    if not executable:
        return None
    try:
        path = Path(executable)
        if os.name == "nt" and os.path.normcase(str(path)) == os.path.normcase(sys.executable):
            # A Windows Store execution alias is not readable. Ask the OS for
            # this running interpreter's loaded executable, rather than guessing
            # a different installation or treating an unknown tool as reusable.
            import ctypes
            buffer = ctypes.create_unicode_buffer(32768)
            size = ctypes.windll.kernel32.GetModuleFileNameW(None, buffer, len(buffer))
            if not size or size >= len(buffer):
                return None
            path = Path(buffer.value)
        path = path.resolve(strict=True)
        return {"path": str(path), "sha256": file_digest(path)}
    except OSError:
        return None


def run(workspace, commands, configuration, timeout):
    root = workspace.root.resolve()
    store = root / STORE
    try:
        store.resolve().relative_to(root)
        if any(part.is_symlink() for part in (root / ".planning", store)):
            raise ValueError("receipt storage is a symlink")
        store.mkdir(parents=True, exist_ok=True)
        try:
            with (store / ".gitignore").open("x", encoding="utf-8") as ignore:
                ignore.write("*\n")
        except FileExistsError:
            pass
    except (OSError, ValueError) as exc:
        raise VerbError("cannot create verification receipt storage: " + str(exc), "verification-storage")
    workers = configuration.get("max_parallel", 4)
    if isinstance(workers, bool) or not isinstance(workers, int) or workers < 1:
        bad("verification.max_parallel must be a positive integer")
    reuse = configuration.get("reuse", True)
    if not isinstance(reuse, bool):
        bad("verification.reuse must be boolean")
    environment = os.environ.copy()  # Each process receives the same frozen environment.
    environment_inputs = ({name.upper(): value for name, value in environment.items()}
                          if os.name == "nt" else environment)
    frozen = safe_snapshot(root, guarded=True)
    try:
        revision = git(root, "rev-parse", "HEAD").decode().strip()
    except (OSError, subprocess.SubprocessError):
        revision = None
    runtime = {"python": sys.version, "executable": sys.executable,
               "platform": platform.platform(), "schema": SCHEMA,
               "implementation": digest([file_digest(Path(__file__)),
                                         file_digest(Path(__file__).with_name("verification.py"))])}
    specifications = [entry if isinstance(entry, dict) else {"command": entry} for entry in commands]
    identities = {}
    for item in specifications:
        executable = item["command"][0]
        if executable not in identities:
            identities[executable] = tool_identity(root, item["command"], environment)
    plans = []
    source_guards = {}
    for item in specifications:
        relevant_env = environment_inputs if "environment" not in item else {
            name: environment_inputs.get(name) for name in item["environment"]}
        inputs = {"command": item["command"], "configuration": digest(configuration),
                  "specification": item, "source": safe_snapshot(root, item.get("sources")),
                  "environment": digest(relevant_env), "runtime": runtime,
                  "tool": identities[item["command"][0]], "root": str(root),
                  "timeout": item.get("timeout", timeout)}
        if item.get("revision"):
            inputs["revision"] = revision
        key = digest(inputs)
        source_guards[key] = safe_snapshot(root, item.get("sources"), guarded=True)
        plans.append((item, inputs, key))

    def execute(plan):
        item, inputs, key = plan
        before = (frozen is not None and safe_snapshot(root, guarded=True) == frozen
                  and inputs["source"] is not None
                  and source_guards[key] is not None
                  and safe_snapshot(root, item.get("sources"), guarded=True) == source_guards[key])
        cacheable = before and inputs["source"] is not None and inputs["tool"] is not None and revision is not None
        if reuse and item.get("reuse", True) and cacheable:
            cached = load_receipt(store, key, inputs)
            if cached is not None:
                return cached, True
        identity = uuid.uuid4().hex
        logs = {stream: store / (identity + "." + stream + ".log") for stream in ("stdout", "stderr")}
        result = {"command": item["command"], "exit_code": None, "passed": False,
                  "reused": False, "tested_revision": revision,
                  "purpose": item.get("purpose"),
                  "receipt": STORE + "/" + key + ".json"}
        with logs["stdout"].open("xb") as stdout, logs["stderr"].open("xb") as stderr:
            try:
                completed = subprocess.run(item["command"], cwd=str(root), env=environment,
                                           stdout=stdout, stderr=stderr, timeout=item.get("timeout", timeout))
                result.update(exit_code=completed.returncode, passed=completed.returncode == 0)
            except (OSError, subprocess.TimeoutExpired) as exc:
                result["error"] = str(exc)
        for stream, path in logs.items():
            result[stream + "_log"] = STORE + "/" + path.name
            result[stream + "_tail"] = tail(path)
        stable = (before and safe_snapshot(root, guarded=True) == frozen
                  and safe_snapshot(root, item.get("sources"), guarded=True) == source_guards[key])
        return result, stable

    outcomes = [None] * len(plans)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        def independent(indices):
            pending = list(indices)
            active = {}
            held = set()
            while pending or active:
                for index in pending[:]:
                    resources = set(plans[index][0].get("resources", []))
                    if len(active) < workers and not resources & held:
                        active[executor.submit(execute, plans[index])] = (index, resources)
                        held.update(resources)
                        pending.remove(index)
                if active:
                    done, _ = wait(active, return_when=FIRST_COMPLETED)
                    for future in done:
                        index, resources = active.pop(future)
                        held.difference_update(resources)
                        outcomes[index] = future.result()
        block = []
        for index, (item, _, _) in enumerate(plans):
            if item.get("independent", False):
                block.append(index)
            else:
                independent(block)
                block = []
                outcomes[index] = execute(plans[index])
        independent(block)
    stable = (frozen is not None and safe_snapshot(root, guarded=True) == frozen
              and all(valid for _, valid in outcomes)
              and all(safe_snapshot(root, item.get("sources"), guarded=True) == source_guards[key]
                      for item, _, key in plans))
    if any(item.get("revision") for item, _, _ in plans):
        try:
            stable = stable and git(root, "rev-parse", "HEAD").decode().strip() == revision
        except (OSError, subprocess.SubprocessError):
            stable = False
    results = []
    for (_, inputs, key), (result, _) in zip(plans, outcomes):
        result["snapshot_valid"] = stable
        if not stable:
            result.update(passed=False, error="verification inputs changed or could not be fingerprinted")
        if not result["reused"]:
            save_receipt(store, key, inputs, result)  # Failure evidence is retained, never reused as pass.
        results.append(result)
    return {"configured": True, "checks": results, "passed": all(r["passed"] for r in results),
            "snapshot_valid": stable, "tested_revision": revision}
