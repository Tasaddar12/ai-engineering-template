"""Revision-bound verification reports and argv-only command receipts."""
from pathlib import Path
import json
import re
import subprocess
from . import config, records
from .core import Failure, digest, load_json, now, planning_lock, read, root, run, safe_path, write, write_json
from .text import join_frontmatter, split_frontmatter


def resolve_file(value):
    directory = records.phase_dir(value)
    matches = sorted(directory.glob("*-VERIFICATION.md"))
    return matches[0] if matches else directory/(directory.name.split("-")[0]+"-VERIFICATION.md")


def status(args):
    value = args.arg(0, args.get("phase"))
    path = resolve_file(value)
    metadata, body = split_frontmatter(read(path))
    state = metadata.get("status", "not_started")
    phase = path.parent.name.split("-")[0]
    routes = {"passed": ("ship", "Publish verified work", f"/ship {phase}"),
              "gaps_found": ("fix", "Close verification gaps", f"/plan-phase {phase} --gaps"),
              "human_needed": ("human", "Complete human verification", f"/verify-work {phase}")}
    route, action, command = routes.get(state, ("verify", "Verify phase goal", f"/verify-work {phase}"))
    return {**metadata, "status": state, "path": str(path), "exists": path.exists(), "route": route,
            "next_action": action, "next_command": command}


def phase_fingerprint(directory, extra=()):
    report = resolve_file(directory)
    paths = list(directory.glob("*-PLAN.md"))+list(directory.glob("*-SUMMARY.md"))
    covered = list(extra)
    for path in list(paths):
        metadata, _ = split_frontmatter(read(path))
        covered.extend(metadata.get("files_modified", []))
        for artifact in metadata.get("must_haves", {}).get("artifacts", []):
            if isinstance(artifact, dict) and artifact.get("path"):
                covered.append(artifact["path"])
    paths.extend(safe_path(p) for p in covered)
    return digest([p for p in paths if p != report], root())


def current_evidence(value):
    directory = records.phase_dir(value)
    report = resolve_file(directory)
    metadata, body = split_frontmatter(read(report))
    head = run(["git", "rev-parse", "HEAD"], root()).stdout.strip()
    recorded = metadata.get("fingerprint")
    covered = metadata.get("covered_files", [])
    expected = phase_fingerprint(directory, covered)
    reasons = []
    if metadata.get("status") != "passed":
        reasons.append("verification has not passed")
    if not recorded or recorded != expected:
        reasons.append("verification fingerprint is absent or stale")
    revision = metadata.get("revision", metadata.get("verified_revision"))
    if not revision or run(["git", "merge-base", "--is-ancestor", str(revision), head], root(), check=False).returncode:
        reasons.append("verified revision is absent or outside current history")
    if revision and revision != head:
        changed = run(["git", "diff", "--name-only", str(revision), head], root(), check=False)
        allowed = {str(report.relative_to(root())).replace("\\", "/"), ".planning/STATE.md", ".planning/ROADMAP.md", ".planning/REQUIREMENTS.md"}
        if changed.returncode or any(path not in allowed for path in changed.stdout.splitlines()):
            reasons.append("source changed since the frozen verification revision")
    if run(["git", "status", "--porcelain"], root()).stdout:
        reasons.append("working tree is dirty")
    settings = config.lookup(config.load(), "verification.commands", [])
    if settings:
        receipt_status = check_status(None)
        names = {check.get("id", check.get("name", str(i+1))) for i, check in enumerate(settings)}
        passed = {r["name"] for r in receipt_status["receipts"] if r["status"] == "passed"}
        if not names.issubset(passed):
            reasons.append("configured checks lack passing receipts at current HEAD")
    return {"current": not reasons, "reasons": reasons, "revision": head, "verified_revision": revision, "fingerprint": expected}


def fingerprint(args):
    directory = records.phase_dir(args.arg(0, args.get("phase")))
    report = resolve_file(directory)
    covered = args.all("files") + args.all("covered-files")
    value = phase_fingerprint(directory, covered)
    with planning_lock():
        metadata, body = split_frontmatter(read(report))
        metadata["fingerprint"] = value
        metadata.setdefault("status", "not_started")
        metadata["covered_files"] = covered
        metadata["revision"] = run(["git", "rev-parse", "HEAD"], root()).stdout.strip()
        metadata.setdefault("phase", directory.name.split("-")[0])
        write(report, join_frontmatter(metadata, body))
    return {"fingerprint": value, "path": str(report)}


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


def check_fingerprint(check):
    import hashlib
    if check.get("inputs"):
        inputs = [safe_path(path) for path in check["inputs"]]
    else:
        tracked = run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], root()).stdout.splitlines()
        inputs = [safe_path(path) for path in tracked if not path.startswith(".planning/")]
    key = digest(inputs)+":"+json.dumps(check, sort_keys=True)
    return hashlib.sha256(key.encode()).hexdigest()


def run_checks(args):
    configured = config.lookup(config.load(), "verification.commands", [])
    if not isinstance(configured, list):
        raise Failure("invalid-checks", "verification.commands must be a list", 2)
    selected = args.all("checks")
    revision = run(["git", "rev-parse", "HEAD"], root()).stdout.strip()
    receipts = records.planning()/"verification/receipts"
    results = []
    for index, check in enumerate(configured):
        if not isinstance(check, dict) or not isinstance(check.get("argv"), list) or not check["argv"] or any(not isinstance(v, str) for v in check["argv"]):
            raise Failure("invalid-check", "Each check requires a nonempty argv string array", 2)
        name = check.get("id", check.get("name", str(index+1)))
        if selected and name not in selected:
            continue
        fingerprint_value = check_fingerprint(check)
        receipt_path = receipts/(fingerprint_value+".json")
        receipt = load_json(receipt_path)
        receipt_ancestor = receipt and run(["git", "merge-base", "--is-ancestor", receipt["revision"], revision], root(), check=False).returncode == 0
        if receipt and receipt_ancestor and receipt.get("status") == "passed" and not args.has("force"):
            results.append({**receipt, "reused": True})
            continue
        started = now()
        try:
            result = run(check["argv"], safe_path(check.get("cwd", ".")), check=False, timeout=float(check.get("timeout", 300)))
            code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired as exc:
            code, stdout, stderr = 124, str(exc.stdout or ""), str(exc.stderr or "")
        after = run(["git", "rev-parse", "HEAD"], root()).stdout.strip()
        if revision != after:
            raise Failure("revision-drift", "HEAD changed while running verification checks")
        if check_fingerprint(check) != fingerprint_value:
            raise Failure("verification-input-drift", "Check inputs changed during the frozen verification run", check=name)
        receipt = {"name": name, "argv": check["argv"], "revision": revision, "fingerprint": fingerprint_value,
                   "started": started, "finished": now(), "exit_code": code, "stdout": stdout,
                   "stderr": stderr, "status": "passed" if code == 0 else "failed", "reused": False}
        write_json(receipt_path, receipt)
        results.append(receipt)
    passed = all(item["status"] == "passed" for item in results)
    return {"passed": passed, "status": "passed" if passed else "failed", "revision": revision,
            "checks": results, "count": len(results)}, int(not passed)


def check_status(args):
    revision = run(["git", "rev-parse", "HEAD"], root()).stdout.strip()
    receipts = []
    configured = config.lookup(config.load(), "verification.commands", [])
    expected = {check_fingerprint(check) for check in configured}
    for path in (records.planning()/"verification/receipts").glob("*.json"):
        item = load_json(path)
        ancestor = run(["git", "merge-base", "--is-ancestor", item["revision"], revision], root(), check=False).returncode == 0
        if ancestor and item.get("fingerprint") in expected:
            receipts.append(item)
    passing = {r["fingerprint"] for r in receipts if r["status"] == "passed"}
    return {"revision": revision, "receipts": receipts, "passed": expected.issubset(passing)}
