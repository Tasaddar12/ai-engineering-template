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


def fingerprint(args):
    directory = records.phase_dir(args.arg(0, args.get("phase")))
    report = resolve_file(directory)
    paths = list(directory.glob("*-PLAN.md"))+list(directory.glob("*-SUMMARY.md"))
    covered = args.all("files") + args.all("covered-files")
    for path in list(paths):
        metadata, _ = split_frontmatter(read(path))
        covered.extend(metadata.get("files_modified", []))
        for artifact in metadata.get("must_haves", {}).get("artifacts", []):
            if isinstance(artifact, dict) and artifact.get("path"):
                covered.append(artifact["path"])
    paths.extend(safe_path(p) for p in covered)
    value = digest([p for p in paths if p != report], root())
    with planning_lock():
        metadata, body = split_frontmatter(read(report))
        metadata["fingerprint"] = value
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


def run_checks(args):
    configured = config.lookup(config.load(), "verification.commands", [])
    if not isinstance(configured, list):
        raise Failure("invalid-checks", "verification.commands must be a list", 2)
    selected = args.all("checks")
    revision = run(["git", "rev-parse", "HEAD"], root()).stdout.strip()
    dirty = run(["git", "status", "--porcelain", "--untracked-files=all"], root()).stdout
    content_files = [root()/line[3:] for line in dirty.splitlines() if len(line) > 3 and not line[3:].startswith(".planning/")]
    dirty_digest = digest(content_files)
    receipts = records.planning()/"verification/receipts"
    results = []
    for index, check in enumerate(configured):
        if not isinstance(check, dict) or not isinstance(check.get("argv"), list) or not check["argv"] or any(not isinstance(v, str) for v in check["argv"]):
            raise Failure("invalid-check", "Each check requires a nonempty argv string array", 2)
        name = check.get("id", check.get("name", str(index+1)))
        if selected and name not in selected:
            continue
        inputs = [safe_path(p) for p in check.get("inputs", [])]
        key = digest(inputs) + ":" + json.dumps(check, sort_keys=True) + ":" + revision + ":" + dirty_digest
        import hashlib
        fingerprint_value = hashlib.sha256(key.encode()).hexdigest()
        receipt_path = receipts/(fingerprint_value+".json")
        receipt = load_json(receipt_path)
        if receipt and receipt.get("status") == "passed" and not args.has("force"):
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
    for path in (records.planning()/"verification/receipts").glob("*.json"):
        item = load_json(path)
        if item.get("revision") == revision:
            receipts.append(item)
    return {"revision": revision, "receipts": receipts, "passed": bool(receipts) and all(r["status"] == "passed" for r in receipts)}
