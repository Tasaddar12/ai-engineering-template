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
from . import verification_successors as successors

STORE = ".planning/verification-receipts"
SCHEMA = 1
FIELDS = {"command", "sources", "environment", "independent", "resources", "timeout", "revision", "reuse", "successor_independence"}


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
        if "successor_independence" in item:
            contract = item["successor_independence"]
            if (not isinstance(contract, dict)
                    or set(contract) != {"schema", "report_paths", "protected_inputs", "revision_semantics"}
                    or type(contract.get("schema")) is not int or contract["schema"] != 1
                    or contract.get("protected_inputs") != "all-other-inputs"
                    or contract.get("revision_semantics") != "provenance-only"):
                bad("invalid successor_independence contract")
            reports = contract.get("report_paths")
            if (not isinstance(reports, list) or not reports
                    or any(not isinstance(v, str) for v in reports) or len(set(reports)) != len(reports)):
                bad("successor report_paths must be nonempty exact unique paths")
            try:
                for report in reports:
                    successors.literal_path(report)
            except ValueError as exc:
                bad(str(exc))
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


def source_paths(root, sources=None):
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
    return paths


def snapshot(root, sources=None, guarded=False):
    return fingerprint(root, source_paths(root, sources), guarded)


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
        if result["passed"] is not True or (type(result["exit_code"]) is not int or result["exit_code"] != 0) or result.get("error"):
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


def runtime_identity():
    directory = Path(__file__).parent
    implementation = sorted(directory.glob("*.py")) + [directory.parent / "phase.py"]
    return {"python": sys.version, "executable": sys.executable,
            "platform": platform.platform(), "schema": SCHEMA,
            "implementation": digest([[p.name, file_digest(p)] for p in implementation])}


def capture_inputs(root, commands, configuration, timeout, revision, environment):
    environment_inputs = ({name.upper(): value for name, value in environment.items()}
                          if os.name == "nt" else environment)
    runtime = runtime_identity()
    specifications = [entry if isinstance(entry, dict) else {"command": entry} for entry in commands]
    order = digest(specifications)
    identities = {}
    inputs_list = []
    for index, item in enumerate(specifications):
        executable = item["command"][0]
        if executable not in identities:
            identities[executable] = tool_identity(root, item["command"], environment)
        relevant_env = environment_inputs if "environment" not in item else {
            name: environment_inputs.get(name) for name in item["environment"]}
        inputs = {"command": item["command"], "configuration": digest(configuration),
                  "specification": item, "source": safe_snapshot(root, item.get("sources")),
                  "environment": digest(relevant_env), "runtime": runtime,
                  "tool": identities[executable], "root": str(root),
                  "timeout": item.get("timeout", timeout), "index": index, "order": order}
        if item.get("revision"):
            inputs["revision"] = revision
        if "successor_independence" in item:
            try:
                inputs["successor"] = successors.capture_bundle(
                    root, revision, item["successor_independence"], inventory(root),
                    source_paths(root, item.get("sources")), digest(configuration), order, index)
            except (OSError, ValueError, subprocess.SubprocessError):
                inputs["successor"] = None  # Checks still run; unavailable proof never qualifies.
        inputs_list.append(inputs)
    return specifications, inputs_list


def selected_indices(only_checks, count):
    if only_checks is None:
        return list(range(count))
    if not isinstance(only_checks, list) or not only_checks:
        bad("only-checks requires nonempty zero-based indices")
    result = []
    for value in only_checks:
        if isinstance(value, bool) or not str(value).isascii() or not str(value).isdigit():
            bad("only-checks requires zero-based integer indices")
        index = int(value)
        if index >= count or index in result:
            bad("only-checks has duplicate or out-of-range indices")
        result.append(index)
    if result != sorted(result):
        bad("only-checks indices must follow configuration order")
    return result


def run(workspace, commands, configuration, timeout, only_checks=None):
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
    frozen = safe_snapshot(root, guarded=True)
    try:
        revision = git(root, "rev-parse", "HEAD").decode().strip()
    except (OSError, subprocess.SubprocessError):
        revision = None
    specifications, all_inputs = capture_inputs(root, commands, configuration, timeout, revision, environment)
    indices = selected_indices(only_checks, len(commands))
    plans = []
    source_guards = {}
    for index in indices:
        item, inputs = specifications[index], all_inputs[index]
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
                  "reused": False, "tested_revision": revision, "full_index": inputs["index"],
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
    result = {"configured": True, "checks": results, "passed": all(r["passed"] for r in results),
              "snapshot_valid": stable, "tested_revision": revision}
    if only_checks is not None:
        partial = len(indices) != len(commands)
        result.update(partial=partial, selected_indices=indices,
                      full_configuration_sha256=digest(configuration),
                      full_order_sha256=digest(specifications), selected_passed=result["passed"])
        if partial:
            result["passed"] = False
    return result

def read_evidence(path):
    """Read external JSON without following links or treating it as authority."""
    path = Path(path).absolute()
    successors.safe_path(Path(path.anchor), path.relative_to(path.anchor).as_posix())
    with path.open(encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("evidence must be an object")
    return value


def authentic_result(root, row):
    if not isinstance(row, dict):
        raise ValueError("invalid check result")
    reference = row.get("receipt")
    if (not isinstance(reference, str) or not reference.startswith(STORE + "/")
            or len(reference.split('/')) != 3):
        raise ValueError("invalid receipt reference")
    path = successors.safe_path(root, reference)
    envelope = json.loads(path.read_text(encoding="utf-8"))
    receipt = envelope["receipt"]
    inputs = receipt["inputs"]
    key = digest(inputs)
    if (type(receipt.get("schema")) is not int or receipt["schema"] != SCHEMA
            or receipt.get("key") != key or path.name != key + '.json'
            or envelope.get("sha256") != digest(receipt)):
        raise ValueError("receipt envelope/key/input mismatch")
    stored = receipt["result"]
    if (digest(stored) != digest(row) or stored.get("passed") is not True
            or type(stored.get("exit_code")) is not int or stored["exit_code"] != 0
            or stored.get("snapshot_valid") is not True or stored.get("reused") is not False
            or stored.get("error") or stored.get("command") != inputs.get("command")
            or type(stored.get("full_index")) is not int
            or type(inputs.get("index")) is not int
            or stored["full_index"] != inputs.get("index")):
        raise ValueError("original fresh passing stored result required")
    for stream in ("stdout", "stderr"):
        log_record = receipt[stream]
        name = log_record["file"]
        if not isinstance(name, str) or Path(name).name != name or not name.endswith('.' + stream + '.log'):
            raise ValueError("invalid log reference")
        log_ref = STORE + '/' + name
        log = successors.safe_path(root, log_ref)
        if (stored.get(stream + '_log') != log_ref
                or file_digest(log) != log_record["sha256"]
                or stored.get(stream + '_tail') != tail(log)):
            raise ValueError("log/result hash or content mismatch")
    return inputs


def equivalent_current_inputs(original, current):
    # Only the explicit dependency contract can subsequently bridge these fields.
    ignored = {"source", "revision", "successor"}
    return (digest({k: v for k, v in original.items() if k not in ignored})
            == digest({k: v for k, v in current.items() if k not in ignored})
            and original.get("source") is not None and current.get("source") is not None
            and original.get("tool") is not None and current.get("tool") is not None)


def independent_successor(root, tested, original, current, approved):
    bundle = original.get("successor")
    contract = current["specification"].get("successor_independence")
    if not contract or not isinstance(bundle, dict) or current.get("successor") is None:
        raise ValueError("no original prospective independence/input contract")
    if not set(approved) <= set(contract["report_paths"]):
        raise ValueError("report not covered by this check's original independence contract")
    expected = {"schema", "contract", "source_manifest", "protected_manifest", "reports",
                "configuration_sha256", "order_sha256", "index", "source_sha256", "protected_sha256"}
    if (set(bundle) != expected or type(bundle["schema"]) is not int or bundle["schema"] != 1
            or bundle["contract"] != contract or bundle["index"] != original["index"]
            or type(bundle["index"]) is not int
            or bundle["configuration_sha256"] != current["configuration"]
            or bundle["order_sha256"] != current["order"]
            or bundle["source_sha256"] != digest(bundle["source_manifest"])
            or bundle["source_sha256"] != original["source"]
            or bundle["protected_sha256"] != digest(bundle["protected_manifest"])):
        raise ValueError("baseline input manifest binding is invalid")
    successors.validate_manifest(root, tested, bundle["source_manifest"])
    successors.validate_manifest(root, tested, bundle["protected_manifest"])
    reports = {name: successors.tree_entry(root, tested, name) for name in contract["report_paths"]}
    if bundle["reports"] != reports:
        raise ValueError("baseline report blobs/modes changed")
    if bundle["protected_manifest"] != current["successor"]["protected_manifest"]:
        raise ValueError("protected inputs changed")
    # Current source membership/content must match, allowing only these original
    # declared reports. The full protected inventory also covers undeclared code.
    report_set = set(contract["report_paths"])
    old = [row for row in bundle["source_manifest"] if row[0] not in report_set]
    new = [row for row in current["successor"]["source_manifest"] if row[0] not in report_set]
    if old != new:
        raise ValueError("declared source inputs changed")
    if "revision" in original and original["revision"] != tested:
        raise ValueError("original revision provenance mismatch")


def validate_successor(workspace, evidence, approved_paths, expected_head, commands, configuration,
                       timeout, fresh_evidence=None):
    """Schema-1 adapter: attest H separately; never rewrite R receipts/results."""
    root = workspace.root.resolve()
    count = len(commands)
    tested = evidence.get("tested_revision") if isinstance(evidence, dict) else None
    result = {"qualified": False, "tested_revision": tested, "qualified_revision": expected_head,
              "approved_paths": approved_paths, "checked_commits": [], "checks": [],
              "original_receipts": [], "qualifications": [], "fresh_required": list(range(count))}
    try:
        guard = safe_snapshot(root, guarded=True)
        if guard is None:
            raise ValueError("current source proof unavailable")
        if (not count or not isinstance(evidence, dict)
                or evidence.get("ok", True) is not True
                or evidence.get("configured") is not True or evidence.get("passed") is not True
                or evidence.get("snapshot_valid") is not True or evidence.get("partial", False) is not False
                or not isinstance(evidence.get("checks"), list) or len(evidence["checks"]) != count):
            raise ValueError("complete passing original baseline aggregate required")
        original_inputs = [authentic_result(root, row) for row in evidence["checks"]]
        source_guards = [safe_snapshot(root, (item if isinstance(item, dict) else {}).get("sources"), guarded=True)
                         for item in commands]
        if any(value is None for value in source_guards):
            raise ValueError("declared source guard unavailable")
        identity_guard = runtime_identity()
        history = successors.prove_report_only_successor(root, tested, expected_head, approved_paths)
        result["checked_commits"] = history["checked_commits"]
        if history["qualified"] is not True:
            raise ValueError(history["reason"])
        specs, current_inputs = capture_inputs(root, commands, configuration, timeout,
                                               expected_head, os.environ.copy())
        for index, (row, current, original) in enumerate(zip(evidence["checks"], current_inputs, original_inputs)):
            if (row.get("tested_revision") != tested or row.get("full_index") != index
                    or not equivalent_current_inputs(original, current)):
                raise ValueError("original check order/configuration/current input identity mismatch")
        # An invalid baseline is never selectively rehabilitated with fresh rows.
        result["original_receipts"] = [row["receipt"] for row in evidence["checks"]]
        result["checks"] = list(evidence["checks"])
        required = []
        for index, (original, current) in enumerate(zip(original_inputs, current_inputs)):
            try:
                independent_successor(root, tested, original, current, approved_paths)
                reason, qualified = "original receipt independently covers successor", True
            except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
                reason, qualified = str(exc), False
                required.append(index)
            result["qualifications"].append({"index": index, "qualified": qualified,
                                              "reason": reason, "evidence_revision": tested})
        result["fresh_required"] = list(required)
        if fresh_evidence is not None:
            if (not isinstance(fresh_evidence, dict)
                    or fresh_evidence.get("configured") is not True
                    or fresh_evidence.get("snapshot_valid") is not True
                    or fresh_evidence.get("tested_revision") != expected_head
                    or fresh_evidence.get("selected_indices") != required
                    or any(type(v) is not int for v in fresh_evidence.get("selected_indices", []))
                    or fresh_evidence.get("full_configuration_sha256") != digest(configuration)
                    or fresh_evidence.get("full_order_sha256") != digest(specs)
                    or fresh_evidence.get("selected_passed") is not True
                    or fresh_evidence.get("partial") is not (len(required) != count)
                    or fresh_evidence.get("passed") is not (len(required) == count)
                    or not isinstance(fresh_evidence.get("checks"), list)
                    or len(fresh_evidence["checks"]) != len(required) or not required):
                raise ValueError("fresh evidence must exactly account for ordered fresh-required indices")
            for index, row in zip(required, fresh_evidence["checks"]):
                actual = authentic_result(root, row)
                if (row.get("tested_revision") != expected_head or row.get("full_index") != index
                        or actual != current_inputs[index]):
                    raise ValueError("fresh receipt is not the exact current-H configured check")
                result["checks"][index] = row
                result["qualifications"][index] = {"index": index, "qualified": True,
                    "reason": "genuine fresh current-H evidence", "evidence_revision": expected_head}
            result["fresh_required"] = []
        # Repeat both source and Git guards after receipt/log and fresh validation.
        if (safe_snapshot(root, guarded=True) != guard or runtime_identity() != identity_guard
                or any(safe_snapshot(root, spec.get("sources"), guarded=True) != source_guard
                       for spec, source_guard in zip(specs, source_guards))
                or any(tool_identity(root, spec["command"], os.environ.copy()) != current["tool"]
                       for spec, current in zip(specs, current_inputs))):
            raise ValueError("inputs moved during qualification")
        again = successors.prove_report_only_successor(root, tested, expected_head, approved_paths)
        if again != history:
            raise ValueError("history/worktree changed during qualification")
        result["qualified"] = not result["fresh_required"]
        result["reason"] = "complete ordered evidence covers H" if result["qualified"] else "fresh checks required"
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError, subprocess.SubprocessError) as exc:
        result.update(qualified=False, fresh_required=list(range(count)), reason=str(exc))
    return result
