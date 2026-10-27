"""Revision-bound verification reports and argv-only command receipts."""
from pathlib import Path
import json
import re
import subprocess
from . import config, records
from .core import Failure, digest, load_json, now, planning_lock, read, root, run, safe_path, write, write_json
from .text import join_frontmatter, split_frontmatter


def quick_dir(identifier):
    matches = list((records.planning()/"quick").glob(str(identifier).split("-")[0].zfill(3)+"-*/QUICK.md"))
    if len(matches) != 1:
        raise Failure("quick-not-found", str(identifier))
    metadata, _ = split_frontmatter(read(matches[0]))
    identity = str(metadata.get("id", ""))
    if identity != matches[0].parent.name and identity.zfill(3) != matches[0].parent.name.split("-")[0]:
        raise Failure("quick-identity-mismatch", "QUICK.md identity disagrees with its directory")
    return matches[0].parent


def resolve_file(value=None, quick=None):
    directory = quick_dir(quick) if quick is not None else records.phase_dir(value)
    matches = sorted(directory.glob("*-VERIFICATION.md"))
    return matches[0] if matches else directory/(directory.name.split("-")[0]+"-VERIFICATION.md")


def status(args):
    value = args.arg(0, args.get("phase"))
    path = resolve_file(value, args.get("quick"))
    metadata, body = split_frontmatter(read(path))
    state = metadata.get("status", "not_started")
    phase = path.parent.name.split("-")[0]
    routes = {"passed": ("ship", "Publish verified work", f"/ship {phase}"),
              "gaps_found": ("fix", "Close verification gaps", f"/plan-phase {phase} --gaps"),
              "human_needed": ("human", "Complete human verification", f"/verify-work {phase}")}
    route, action, command = routes.get(state, ("verify", "Verify phase goal", f"/verify-work {phase}"))
    if args.has("quick"):
        route, action, command = ({"passed": ("ship", "Publish verified quick task", f"engineer_run query pr.ready --quick {phase}"),
                                   "gaps_found": ("fix", "Close quick verification gaps", None),
                                   "human_needed": ("human", "Complete quick human verification", None)}
                                  .get(state, ("verify", "Verify the quick task's recorded goal", None)))
    return {**metadata, "status": state, "path": str(path), "exists": path.exists(), "route": route,
            "next_action": action, "next_command": command}


def phase_fingerprint(directory, extra=(), quick=None):
    report = resolve_file(directory, quick)
    paths = list(directory.glob("*-PLAN.md"))+list(directory.glob("*-SUMMARY.md"))
    if quick is not None:
        paths.extend(directory.glob("QUICK.md"))
    covered = list(extra)
    for path in list(paths):
        metadata, _ = split_frontmatter(read(path))
        covered.extend(metadata.get("files_modified", []))
        for artifact in metadata.get("must_haves", {}).get("artifacts", []):
            if isinstance(artifact, dict) and artifact.get("path"):
                covered.append(artifact["path"])
    paths.extend(safe_path(p) for p in covered)
    return digest([p for p in paths if p != report], root())


def current_evidence(value=None, quick=None):
    directory = quick_dir(quick) if quick is not None else records.phase_dir(value)
    report = resolve_file(directory, quick)
    metadata, body = split_frontmatter(read(report))
    head = run(["git", "rev-parse", "HEAD"], root()).stdout.strip()
    recorded = metadata.get("fingerprint")
    recorded_covered = metadata.get("covered_digest")
    covered = metadata.get("covered_files", [])
    expected = phase_fingerprint(directory, covered, quick)
    reasons = []
    if quick is not None and str(metadata.get("quick")).zfill(3) != directory.name.split("-")[0]:
        reasons.append("verification quick identity does not match the requested task")
    if quick is None:
        try:
            matching = records.number(metadata.get("phase", "")) == records.number(directory.name)
        except (ValueError, TypeError):
            matching = False
        if not matching:
            reasons.append("verification phase identity does not match the requested phase")
    if quick is not None and not isinstance(metadata.get("issue_refs"), list):
        reasons.append("quick verification lacks explicit issue declarations")
    if metadata.get("status") != "passed":
        reasons.append("verification has not passed")
    if not recorded or recorded != expected:
        reasons.append("verification fingerprint is absent or stale")
    if recorded_covered != "v4:sha256:"+expected:
        reasons.append("v4 covered_digest is absent, malformed or stale")
    revision = metadata.get("revision", metadata.get("verified_revision"))
    if not revision or run(["git", "merge-base", "--is-ancestor", str(revision), head], root(), check=False).returncode:
        reasons.append("verified revision is absent or outside current history")
    if revision and revision != head:
        # Only the final report may follow a completed actual-HEAD batch. Check
        # every intervening commit: a source edit subsequently reverted is stale.
        allowed = {report.relative_to(root()).as_posix()}
        commits = run(["git", "rev-list", "--reverse", str(revision)+".."+head], root(), check=False)
        changed = []
        for commit in commits.stdout.splitlines():
            delta = run(["git", "diff-tree", "--no-renames", "--no-commit-id", "--name-only", "-r", "-m", commit], root(), check=False)
            if delta.returncode:
                changed.append("<unreadable-commit>")
            changed.extend(delta.stdout.splitlines())
        if commits.returncode or any(path not in allowed for path in changed):
            reasons.append("source changed since the frozen verification revision")
    if run(["git", "status", "--porcelain"], root()).stdout:
        reasons.append("working tree is dirty")
    settings = config.lookup(config.load(), "verification.commands", [])
    if settings:
        receipt_status = check_status(None)
        names = {check["id"] for check in configured_checks()[1]}
        passed = {r["name"] for r in receipt_status["receipts"] if r["status"] == "passed"}
        if not names.issubset(passed):
            reasons.append("configured checks lack passing receipts at current HEAD")
    return {"current": not reasons, "reasons": reasons, "revision": head, "verified_revision": revision,
            "fingerprint": expected, "covered_digest": "v4:sha256:"+expected, "recorded_covered_digest": recorded_covered}


def fingerprint(args):
    quick = args.get("quick")
    directory = quick_dir(quick) if quick is not None else records.phase_dir(args.arg(0, args.get("phase")))
    report = resolve_file(directory, quick)
    covered = args.all("files") + args.all("covered-files")
    value = phase_fingerprint(directory, covered, quick)
    with planning_lock():
        metadata, body = split_frontmatter(read(report))
        metadata["fingerprint"] = value
        metadata["covered_digest"] = "v4:sha256:"+value
        metadata.setdefault("status", "not_started")
        metadata["covered_files"] = covered
        metadata["revision"] = run(["git", "rev-parse", "HEAD"], root()).stdout.strip()
        metadata.setdefault("quick" if quick is not None else "phase", directory.name.split("-")[0])
        if quick is not None:
            metadata.setdefault("issue_refs", [])
        write(report, join_frontmatter(metadata, body))
    return {"fingerprint": value, "covered_digest": "v4:sha256:"+value, "path": str(report)}


def append_audit(args):
    path = safe_path(args.need())
    heading = str(args.get("heading", args.arg(1, "Audit")))
    block = str(args.get("body", args.get("content", args.arg(2, "")))).strip()
    if args.has("file"):
        block = read(safe_path(args.get("file"))).strip()
    if not block:
        raise Failure("empty-audit", "Audit content cannot be empty", 2)
    section = "## "+heading+"\n\n"+block
    with planning_lock():
        content = read(path)
        sections = re.findall(r"(?ms)^## "+re.escape(heading)+r"\n(.*?)(?=^## |\Z)", content)
        if sections and sections[-1].strip() == block:
            return {"appended": False}
        write(path, content.rstrip()+"\n\n"+section+"\n")
    return {"appended": True, "path": str(path)}


def configured_checks():
    import shlex
    settings = config.lookup(config.load(), "verification", {})
    commands = settings.get("commands", [])
    if not isinstance(commands, list):
        raise Failure("bad-config", "verification.commands must be a list", 2)
    result = []
    allowed = {"id", "name", "argv", "command", "cwd", "timeout", "inputs", "sources", "environment", "revision", "reuse", "independent", "resources"}
    for index, item in enumerate(commands):
        check = dict(item) if isinstance(item, dict) else {"command": item}
        if set(check)-allowed:
            raise Failure("bad-config", "Unknown verification check fields", 2)
        argv = check.get("argv", check.get("command"))
        if isinstance(argv, str):
            argv = shlex.split(argv)
        if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x for x in argv):
            raise Failure("bad-config", "Checks require a nonempty argv string array", 2)
        check["argv"] = argv
        check["id"] = str(check.get("id", check.get("name", index+1)))
        for key in ("revision", "reuse", "independent"):
            if key in check and not isinstance(check[key], bool):
                raise Failure("bad-config", key+" must be boolean", 2)
        for key in ("sources", "inputs", "environment", "resources"):
            if key in check and (not isinstance(check[key], list) or any(not isinstance(x, str) for x in check[key]) or key in ("sources", "inputs") and not check[key]):
                raise Failure("bad-config", key+" requires an explicit string list", 2)
        if not isinstance(check.get("timeout", 300), (int, float)) or isinstance(check.get("timeout"), bool) or check.get("timeout", 300) <= 0:
            raise Failure("bad-config", "timeout must be positive", 2)
        for path in check.get("sources", check.get("inputs", [])):
            try:
                safe_path(path)
            except Failure as exc:
                raise Failure("bad-config", "Check inputs must remain inside the repository", 2) from exc
        safe_path(check.get("cwd", "."))
        result.append(check)
    if len({c["id"] for c in result}) != len(result):
        raise Failure("bad-config", "Check identities must be unique", 2)
    parallel = settings.get("max_parallel", 4)
    if not isinstance(parallel, int) or isinstance(parallel, bool) or parallel < 1:
        raise Failure("bad-config", "max_parallel must be a positive integer", 2)
    return settings, result


def source_paths(check=None):
    explicit = (check or {}).get("sources", (check or {}).get("inputs"))
    if explicit is None:
        names = run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], root()).stdout.splitlines()
        return [safe_path(p) for p in names if not p.startswith(".planning/")]
    paths = []
    for value in explicit:
        path = safe_path(value)
        paths.extend([path, *sorted(path.rglob("*"))] if path.is_dir() else [path])
    return paths


def stable_hash(value):
    import hashlib
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def source_snapshot(check=None):
    paths = source_paths(check)
    return {"digest": digest(paths, root()), "stats": [(p.relative_to(root()).as_posix(), p.stat().st_mtime_ns, p.stat().st_ctime_ns, p.stat().st_size) for p in paths if p.is_file()]}


def check_fingerprint(check):
    import os
    environment = dict(os.environ)
    if os.name == "nt":
        environment = {key.upper(): value for key, value in environment.items()}
    if "environment" in check:
        names = [name.upper() if os.name == "nt" else name for name in check["environment"]]
        environment = {name: environment.get(name) for name in names}
    return stable_hash({"source": digest(source_paths(check), root()), "check": check,
                        "configuration": config.lookup(config.load(), "verification", {}),
                        "environment": stable_hash(environment),
                        "revision": run(["git", "rev-parse", "HEAD"], root()).stdout.strip() if check.get("revision") else None})


def receipt_directory():
    directory = records.planning()/"verification-receipts"
    directory.mkdir(parents=True, exist_ok=True)
    # Local receipt/log output must never turn a previously clean source dirty.
    exclude = Path(run(["git", "rev-parse", "--git-path", "info/exclude"], root()).stdout.strip())
    if not exclude.is_absolute():
        exclude = root()/exclude
    with planning_lock():
        content = read(exclude)
        if "/.planning/verification-receipts/" not in content.splitlines():
            write(exclude, content.rstrip()+"\n/.planning/verification-receipts/\n")
    return directory


def read_receipt(path, fingerprint, revision):
    try:
        packet = load_json(path)
        receipt = packet["receipt"]
        if packet["checksum"] != stable_hash(receipt) or receipt["inputs"]["fingerprint"] != fingerprint:
            return None
        result = receipt["result"]
        if not result["passed"] or result["status"] != "passed":
            return None
        if run(["git", "merge-base", "--is-ancestor", result["tested_revision"], revision], root(), check=False).returncode:
            return None
        for stream in ("stdout", "stderr"):
            log = safe_path(result[stream+"_log"])
            if not log.is_file() or stable_hash(read(log)) != receipt["logs"][stream]:
                return None
        return result
    except (OSError, ValueError, TypeError, KeyError, RecursionError, Failure):
        return None


def run_checks(args):
    from concurrent.futures import ThreadPoolExecutor
    import uuid
    settings, configured = configured_checks()
    selected = args.all("checks")
    if set(selected)-{check["id"] for check in configured}:
        raise Failure("unknown-check", "Requested check is not configured")
    checks = [check for check in configured if not selected or check["id"] in selected]
    revision = run(["git", "rev-parse", "HEAD"], root()).stdout.strip()
    if not checks:
        return {"ok": True, "configured": False, "passed": True, "checks": [], "count": 0, "snapshot_valid": True, "revision": revision, "tested_revision": revision}
    directory = receipt_directory()
    before = [source_snapshot(), *[source_snapshot(check) for check in checks]]
    fingerprints = [check_fingerprint(check) for check in checks]
    results = [None]*len(checks)

    def execute(index):
        check, fingerprint_value = checks[index], fingerprints[index]
        path = directory/(fingerprint_value+".json")
        relative = path.relative_to(root()).as_posix()
        cached = read_receipt(path, fingerprint_value, revision)
        if cached and settings.get("reuse", True) and check.get("reuse", True) and not args.has("force"):
            return {**cached, "reused": True}, None
        started, token = now(), uuid.uuid4().hex
        error = None
        try:
            process = run(check["argv"], safe_path(check.get("cwd", ".")), check=False, timeout=check.get("timeout", 300))
            code, stdout, stderr = process.returncode, process.stdout, process.stderr
        except subprocess.TimeoutExpired as exc:
            code, error = None, "command timed out"
            stdout, stderr = exc.stdout or "", exc.stderr or ""
        except OSError as exc:
            code, stdout, stderr, error = None, "", str(exc), str(exc)
        stdout = stdout.decode("utf-8", "replace") if isinstance(stdout, bytes) else stdout
        stderr = stderr.decode("utf-8", "replace") if isinstance(stderr, bytes) else stderr
        logs = {}
        for stream, content in (("stdout", stdout), ("stderr", stderr)):
            log = directory/(token+"."+stream+".log")
            write(log, content)
            logs[stream+"_log"] = log.relative_to(root()).as_posix()
            logs[stream+"_tail"] = content[-2000:]
        result = {"name": check["id"], "command": check["argv"], "argv": check["argv"], "revision": revision,
                  "tested_revision": revision, "fingerprint": fingerprint_value, "started": started, "finished": now(),
                  "exit_code": code, "status": "passed" if code == 0 and not error else "failed",
                  "passed": code == 0 and not error, "reused": False, "receipt": relative, **logs}
        if error:
            result["error"] = error
        packet = {"inputs": {"fingerprint": fingerprint_value}, "result": result,
                  "logs": {"stdout": stable_hash(stdout), "stderr": stable_hash(stderr)}}
        return result, packet

    packets = {}
    # Independent checks share a bounded pool. Resource conflicts and ordinary
    # checks form barriers; all futures are joined before batch evidence exists.
    with ThreadPoolExecutor(max_workers=settings.get("max_parallel", 4)) as pool:
        pending, resources = [], set()
        def join():
            for index, future in pending:
                results[index], packet = future.result()
                if packet:
                    packets[index] = packet
            pending.clear()
            resources.clear()
        for index, check in enumerate(checks):
            owned = set(check.get("resources", []))
            if not check.get("independent") or owned & resources:
                join()
            pending.append((index, pool.submit(execute, index)))
            resources.update(owned)
            if not check.get("independent"):
                join()
        join()
    after = [source_snapshot(), *[source_snapshot(check) for check in checks]]
    valid = before == after and revision == run(["git", "rev-parse", "HEAD"], root()).stdout.strip() and fingerprints == [check_fingerprint(check) for check in checks]
    if not valid:
        for result in results:
            result.update({"passed": False, "status": "failed", "error": "frozen verification inputs changed"})
    # Serialize publication, use unique logs and atomic receipt replacement; never
    # publish successful evidence for a batch whose shared snapshot changed.
    with planning_lock():
        for index, packet in packets.items():
            packet["result"] = results[index]
            write_json(safe_path(results[index]["receipt"]), {"receipt": packet, "checksum": stable_hash(packet)})
    passed = valid and all(item["passed"] for item in results)
    return {"ok": True, "configured": True, "passed": passed, "status": "passed" if passed else "failed",
            "snapshot_valid": valid, "revision": revision, "tested_revision": revision, "checks": results, "count": len(results)}


def check_status(args):
    revision = run(["git", "rev-parse", "HEAD"], root()).stdout.strip()
    _, checks = configured_checks()
    receipts = []
    for check in checks:
        fingerprint_value = check_fingerprint(check)
        receipt = read_receipt(records.planning()/"verification-receipts"/(fingerprint_value+".json"), fingerprint_value, revision)
        if receipt:
            receipts.append(receipt)
    return {"revision": revision, "receipts": receipts, "passed": len(receipts) == len(checks)}
