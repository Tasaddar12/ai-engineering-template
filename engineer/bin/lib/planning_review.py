"""Evidence-bound structural repair, preserving authored project intent."""
from pathlib import Path
import hashlib
import json
import re
import shutil
from . import records, models, frontmatter, plans
from .archive import guarded
from .core import Failure, digest, load_json, now, planning_lock, read, root, run, safe_path, write, write_json
from .text import join_frontmatter, split_frontmatter

TEMPLATE_NAMESPACE = Path(__file__).resolve().parents[2]
TEMPLATES = TEMPLATE_NAMESPACE/"templates"


def _guard_tree(base):
    """Complete metadata-only preflight before any content fingerprint or lock."""
    import stat
    pending, result = [Path(base)], []
    for parent in reversed(Path(base).parents):
        if parent.exists():
            info = parent.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise Failure("linked-path", str(parent))
    while pending:
        path = pending.pop()
        try:
            info = path.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise Failure("linked-path", str(path))
        if stat.S_ISDIR(info.st_mode):
            pending.extend(path.iterdir())
        else:
            result.append(path)
    return result


def inventory():
    paths = _guard_tree(records.planning())
    _guard_tree(TEMPLATE_NAMESPACE)
    return sorted(path for path in paths if "archive" not in path.relative_to(records.planning()).parts and path.suffix.lower() in (".md", ".yaml", ".yml"))


def _audit(args):
    paths = inventory()
    templates = [path for path in _guard_tree(TEMPLATES) if path.suffix.lower() == ".md"]
    snapshot = digest(paths+templates)
    findings, repairs = [], []
    def report(path, check, message):
        findings.append({"record": Path(path).relative_to(root()).as_posix(), "path": str(path), "check": check, "message": message, "error": message})
    packet = {"fingerprint": snapshot, "snapshotDigest": snapshot, "digest": snapshot,
              "inventory": [{"record": path.relative_to(root()).as_posix()} for path in paths]}
    if re.search(r"(?i)unfilled adoption skeleton.*CHANGEME", read(records.planning()/"PROJECT.md")):
        return {**packet, "status": "unfilled", "findings": [], "repairs": [], "valid": True}, []
    from .planning_consistency import findings as consistency
    for item in consistency():
        message = item["error"]
        check = ("phase-id" if "Duplicate roadmap" in message else "plan-id" if "Frontmatter phase" in message else
                 "plan-dependency" if "Plan dependency" in message else "phase-dependency" if "phase dependency" in message.lower() else
                 "requirement-phase" if "absent phase" in message else "requirement-id" if "requirement" in message.lower() else "record-consistency")
        report(item["path"], check, message)
    dependencies = {}
    completion_conflict = False
    for path in paths:
        content = read(path)
        try:
            metadata, body = split_frontmatter(content)
        except Failure as exc:
            report(path, "frontmatter", exc.message)
            completion_conflict |= path.name.endswith("-VERIFICATION.md")
            continue
        structural = records.roadmap_structure(body)
        for target in re.findall(r"\]\(([^\s)#]+)(?:#[^)]*)?\)", structural):
            if re.match(r"[a-zA-Z]+:|/", target):
                continue
            if not (path.parent/target).exists():
                report(path, "local-reference", "Missing local reference "+target)
        if path.name.endswith("-PLAN.md"):
            identifier = path.name[:-8]
            dependencies[identifier] = metadata.get("depends_on", []) if isinstance(metadata.get("depends_on", []), list) else []
            errors = frontmatter.errors(metadata, "plan")+frontmatter.path_errors(path, metadata, "plan")
            for task in plans.tasks(body):
                if not task["type"].startswith("checkpoint:"):
                    errors.extend("Task missing "+key for key in ("files", "action", "verify", "done") if not task[key])
            if errors:
                report(path, "plan-contract", "; ".join(errors))
        if path.name == "QUICK.md" and metadata.get("status") == "complete":
            if not metadata.get("completed") or not re.search(r"(?ms)^## Verification\s*\n\s*\S", body):
                report(path, "completion-evidence", "Completed quick task has no authored verification")
        if path.name.startswith("ADR-") and metadata.get("status") == "superseded" and not metadata.get("superseded_by"):
            report(path, "adr-replacement", "Superseded ADR has no replacement identity")
    active, visited = set(), set()
    def visit(identifier):
        if identifier in active:
            report(records.planning()/"ROADMAP.md", "plan-dependency", "Plan dependency cycle includes "+identifier)
            return
        if identifier in visited:
            return
        active.add(identifier)
        for dependency in dependencies.get(identifier, []):
            if dependency in dependencies:
                visit(dependency)
        active.remove(identifier)
        visited.add(identifier)
    for identifier in dependencies:
        visit(identifier)
    for phase in records.roadmap_phases():
        checked = re.findall(r"(?m)^- \[x\]\s*(\d+(?:\.\d+)?-[0-9]{2})\s*:", phase["body"])
        for identifier in checked:
            try:
                directory = records.phase_dir(phase["number"])
                metadata, body = split_frontmatter(read(directory/(identifier+"-SUMMARY.md")))
                commits = re.findall(r"`([0-9a-f]{7,40})`", body)
                valid = metadata.get("status") == "complete" and bool(commits) and all(run(["git", "cat-file", "-e", commit+"^{commit}"], root(), check=False).returncode == 0 for commit in commits)
            except Failure:
                valid = False
            if not valid:
                completion_conflict = True
                report(records.planning()/"ROADMAP.md", "completion-evidence", "Checked plan requires completed summary and resolvable task commits: "+identifier)
    path = records.planning()/"STATE.md"
    if path.is_file():
        before = read(path)
        metadata, body = split_frontmatter(before)
        after_body = body
        for heading, anchors in (("## Current Position", ("Phase:", "Plan:", "Status:")),
                                 ("## Accumulated Context", ("### Decisions", "### Pending Todos", "### Blockers/Concerns")),
                                 ("## Session Continuity", ("Last session:", "Stopped at:", "Resume file:"))):
            structure = records.roadmap_structure(after_body)
            if re.search(r"(?m)^"+re.escape(heading)+r"\s*$", structure):
                continue
            # A wrong-level heading or fenced anchor is authored ambiguity.
            if re.search(r"(?m)^#+\s+"+re.escape(heading.lstrip("# "))+r"\s*$", after_body):
                report(path, "template-section", "Wrong heading level for "+heading)
                continue
            matches = [list(re.finditer(r"(?m)^"+re.escape(anchor)+r"[^\n]*$", structure)) for anchor in anchors]
            if all(len(items) == 1 for items in matches) and [items[0].start() for items in matches] == sorted(items[0].start() for items in matches):
                insertion = matches[0][0].start()
                after_body = after_body[:insertion]+heading+"\n\n"+after_body[insertion:]
            else:
                report(path, "template-section", "Cannot restore unambiguous "+heading)
        reasons = []
        if after_body != body:
            reasons.append("restore-state-heading")
        derived = records.derived_progress()
        if metadata.get("progress") != derived and not completion_conflict:
            metadata["progress"] = derived
            reasons.append("derive-state-progress")
        if reasons and not any(item["check"] in ("phase-id", "plan-id", "plan-dependency") for item in findings):
            repairs.append({"id": "state-structure", "record": path.relative_to(root()).as_posix(), "path": str(path), "reason": ", ".join(reasons), "before": before, "after": join_frontmatter(metadata, after_body)})
    return {**packet, "status": "findings" if findings else "clean", "findings": findings, "repairs": repairs,
            "valid": not findings, "checked": len(paths), "repairable": bool(repairs)}, repairs


def review(args):
    return _audit(args)[0]


def _repair(args, apply=False, expected=None, only=()):
    if any(value != "state-structure" for value in only):
        raise Failure("unknown-repair", "Only explicitly supported structural repairs may be selected")
    packet, candidates = _audit(args)
    if not apply:
        return {**packet, "applied": False, "dry_run": True, "changed": []}
    if not expected or expected != packet["fingerprint"]:
        raise Failure("stale-review", "Review current evidence before applying structural repair")
    for item in candidates:
        path = guarded(item["record"])
        if path != records.planning()/"STATE.md":
            raise Failure("path-escape", "Only the reviewed STATE structure is repairable")
    with planning_lock():
        current, current_candidates = _audit(args)
        if current["fingerprint"] != expected:
            raise Failure("stale-review", "Planning evidence changed")
        for item in current_candidates:
            path = guarded(item["record"])
            if path != records.planning()/"STATE.md" or read(path) != item["before"]:
                raise Failure("path-escape", "Repair candidate no longer owns exact STATE content")
            write(path, item["after"])
    return {**packet, "applied": True, "dry_run": False, "changed": [item["record"] for item in current_candidates], "repaired": len(current_candidates)}


def repair(args, apply=False, expected=None, only=()):
    return _repair(args, apply or args.has("apply"), expected or args.get("expect", args.get("expect-digest")), only or args.all("only"))


def _retired(path):
    relative = path.relative_to(records.planning())
    if relative.parts[:2] == ("todos", "completed"):
        return True
    if path.is_dir():
        from .archive import historical_phase_evidence
        return historical_phase_evidence(path)
    metadata, _ = split_frontmatter(read(path))
    return metadata.get("status") in ("retired", "superseded", "closed", "complete", "passed")


def selected(args):
    values = args.all("paths") or args.all("path")
    if not values:
        raise Failure("missing-archive-selection", "Select exact planning records with --paths", 2)
    paths = [guarded(value) for value in values]
    base = records.planning()
    for path in paths:
        if not path.is_relative_to(base) or path == base or not path.exists() or path.name in ("STATE.md", "PROJECT.md", "ROADMAP.md", "REQUIREMENTS.md", "config.yaml") or "archive" in path.relative_to(base).parts:
            raise Failure("invalid-archive-selection", str(path))
        if not _retired(path):
            raise Failure("record-not-retired", str(path))
    for path in paths:
        if any(path != other and path.is_relative_to(other) for other in paths):
            raise Failure("overlapping-archive-selection", str(path))
    return paths


def selection_digest(paths):
    files = [child for path in paths for child in (path.rglob("*") if path.is_dir() else [path]) if child.is_file()]
    marker = "\n".join(sorted(str(path.relative_to(root())) for path in paths))
    return hashlib.sha256((marker+"\n"+digest(files)).encode()).hexdigest()


def archive(args):
    from .archive import archive as operation
    return operation(args)


def archives(args):
    from .archive import archives as operation
    return operation(args)


def recover(args):
    from .archive import recover as operation
    return operation(args)
