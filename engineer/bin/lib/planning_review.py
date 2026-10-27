"""Preview-bound structural repair and exact retirement of planning records."""
from pathlib import Path
import hashlib
import json
import re
import shutil
from . import records
from .core import Failure, digest, load_json, now, planning_lock, read, root, safe_path, write, write_json
from .text import join_frontmatter, split_frontmatter


def inventory():
    base = records.planning()
    return sorted(path for path in base.rglob("*") if path.is_file() and "archive" not in path.relative_to(base).parts and path.suffix in (".md", ".yaml"))


def review(args):
    paths = inventory()
    snapshot = digest(paths)
    findings, repairs = [], []
    from .misc import integrity
    packet, _ = integrity(args, strict=False)
    findings.extend(packet["warnings"])
    path = records.planning()/"STATE.md"
    if path.exists():
        before = read(path)
        after = before
        headings = ("## Current Position", "## Performance Metrics", "## Accumulated Context", "## Session Continuity")
        for heading in headings:
            if not re.search(r"(?m)^"+re.escape(heading)+r"\s*$", after):
                after = after.rstrip()+"\n\n"+heading+"\n\n"
        for heading in ("### Decisions", "### Pending Todos", "### Blockers/Concerns", "### Roadmap Evolution"):
            if not re.search(r"(?m)^"+re.escape(heading)+r"\s*$", after):
                marker = re.search(r"(?m)^## Accumulated Context\s*$", after)
                after = after[:marker.end()]+"\n\n"+heading+"\n"+after[marker.end():]
        try:
            metadata, body = split_frontmatter(after)
            derived = records.derived_progress()
            if metadata.get("progress") != derived:
                metadata["progress"] = derived
                after = join_frontmatter(metadata, body)
        except Failure:
            pass  # Malformed author input requires an explicit human repair.
        if after != before:
            repairs.append({"path": str(path), "reason": "Add absent STATE sections and synchronize derived progress, preserving author narrative", "before": before, "after": after})
    return {"snapshotDigest": snapshot, "digest": snapshot, "repairs": repairs, "findings": findings,
            "checked": len(paths), "repairable": bool(repairs), "valid": not findings}


def repair(args):
    packet = review(args)
    if not args.has("apply"):
        return {**packet, "applied": False}
    expected = args.get("expect", args.get("expect-digest"))
    with planning_lock():
        packet = review(args)
        if not expected or expected != packet["snapshotDigest"]:
            raise Failure("planning-review-stale", "Review planning records again before applying repairs")
        for item in packet["repairs"]:
            path = safe_path(item["path"])
            if read(path) != item["before"]:
                raise Failure("planning-repair-drift", str(path))
            write(path, item["after"])
    return {**packet, "applied": True, "repaired": len(packet["repairs"])}


def _retired(path):
    relative = path.relative_to(records.planning())
    if relative.parts[:2] == ("todos", "completed"):
        return True
    if path.is_dir():
        reports = list(path.glob("*-VERIFICATION.md"))
        return bool(reports) and all(split_frontmatter(read(p))[0].get("status") == "passed" for p in reports)
    metadata, _ = split_frontmatter(read(path))
    return metadata.get("status") in ("retired", "superseded", "closed", "complete", "passed")


def selected(args):
    values = args.all("paths") or args.all("path")
    if not values:
        raise Failure("missing-archive-selection", "Select exact planning records with --paths", 2)
    paths = [safe_path(value) for value in values]
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
    paths = selected(args)
    snapshot = selection_digest(paths)
    entries = [{"path": str(path), "directory": path.is_dir()} for path in paths]
    if not args.has("confirm"):
        return {"snapshotDigest": snapshot, "digest": snapshot, "entries": entries, "archived": False}
    expected = args.get("expect", args.get("expect-digest"))
    if expected != snapshot:
        raise Failure("archive-preview-stale", "Exact archive selection requires its fresh digest")
    identifier = now().replace(":", "").replace("+", "-")+"-"+snapshot[:8]
    destination = records.planning()/"archive/records"/identifier
    with planning_lock():
        if selection_digest(selected(args)) != expected:
            raise Failure("archive-source-drift", "Selected records changed")
        destination.mkdir(parents=True, exist_ok=False)
        for entry, path in zip(entries, paths):
            target = destination/path.relative_to(records.planning())
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(target))
            entry["archived_path"] = str(target)
        manifest = {"id": identifier, "created": now(), "snapshotDigest": snapshot, "entries": entries}
        write_json(destination/"archive.json", manifest)
    return {**manifest, "archived": True, "path": str(destination)}


def archives(args):
    entries = [load_json(path) for path in (records.planning()/"archive/records").glob("*/archive.json")]
    return {"archives": entries, "count": len(entries)}


def recover(args):
    identifier = args.need()
    if Path(identifier).name != identifier:
        raise Failure("invalid-archive-id", identifier)
    manifest_path = records.planning()/"archive/records"/identifier/"archive.json"
    manifest = load_json(manifest_path)
    if not manifest or manifest.get("recovered"):
        raise Failure("archive-not-found", identifier)
    sources = [safe_path(item["archived_path"]) for item in manifest["entries"]]
    snapshot = selection_digest(sources)
    if not args.has("confirm"):
        return {**manifest, "recoveryDigest": snapshot, "recovered": False}
    with planning_lock():
        if args.get("expect") != selection_digest(sources):
            raise Failure("archive-recovery-stale", "Review the archived contents before recovery")
        targets = [safe_path(item["path"]) for item in manifest["entries"]]
        if any(path.exists() for path in targets):
            raise Failure("archive-recovery-conflict", "An original record path already exists")
        for source, target in zip(sources, targets):
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
        manifest.update({"recovered": True, "recovered_at": now()})
        write_json(manifest_path, manifest)
    return manifest
