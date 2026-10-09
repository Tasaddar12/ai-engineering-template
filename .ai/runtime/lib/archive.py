"""Explicit, recoverable archival of planning records.

The catalog is a discovery index; source records remain the historical evidence.
Every apply saves exact before/after bytes before moving anything. Recovery is a
hash-guarded rollback, never an overwrite of subsequent user edits.
"""
import base64
import hashlib
import json
import os
import re
import stat
from pathlib import Path
from urllib.parse import unquote

from . import phases
from .paths import read_text
from .results import VerbError, require
from .roadmap import Roadmap, as_number, display_number
from .state import POSITION, State, planning_lock, progress_bar
from .text import join_frontmatter, section_body, split_frontmatter

KINDS = {"phase": "phases", "adr": "decisions", "quick": "quick"}
SCHEMA = 1
LINK = re.compile(r"(?P<prefix>!?\[[^\]\n]*\]\()(?P<target><[^>\n]+>|[^\s)]+)(?P<tail>(?:\s+[^)\n]*)?\))")
REFERENCE = re.compile(r"(?P<prefix>^\s*\[[^\]\n]+\]:\s*)(?P<target><[^>\n]+>|[^\s]+)", re.MULTILINE)
PLANNING_REF = re.compile(r"(?<![\w./-])\.planning/[\w./%+-]+")
PLACEHOLDER = re.compile(r"\b(?:TBD|TODO|CHANGEME|placeholder)\b|filled on completion", re.I)


def guarded(workspace, path):
    """Reject traversal and every symlink/junction, including intermediate ones."""
    path = Path(path)
    require(".." not in path.parts, "traversal is not an archive selector", "path-escape")
    root = workspace.root.resolve()
    require(not workspace.planning.is_symlink(), "planning directory is a symlink", "path-escape")
    try:
        relative = path.absolute().relative_to(root)
    except ValueError:
        raise VerbError("archive path escapes repository", "path-escape")
    require(relative.parts and relative.parts[0] == ".planning",
            "archive paths must stay in .planning", "path-escape")
    current = root
    for part in relative.parts:
        current = current / part
        try:
            attributes = getattr(current.lstat(), "st_file_attributes", 0)
        except FileNotFoundError:
            attributes = 0
        # Python 3.11 has no Path.is_junction; lstat still exposes Windows
        # reparse attributes without resolving their target.
        reparse = attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        require(not current.is_symlink() and not reparse,
                "archive path contains a symlink or junction: " + str(current), "path-escape")
    try:
        path.resolve().relative_to(workspace.planning.resolve())
    except ValueError:
        raise VerbError("archive path escapes .planning", "path-escape")
    return path


def selector_path(workspace, value):
    text = str(value).replace("\\", "/")
    require(".." not in text.split("/"), "traversal is not permitted", "path-escape")
    target = Path(text)
    if not target.is_absolute():
        target = workspace.root / target if text.startswith(".planning/") else workspace.planning / target
    return guarded(workspace, target)


def tree_files(workspace, path):
    guarded(workspace, path)
    if path.is_file():
        return [path]
    found = []
    for directory, dirs, files in os.walk(path, followlinks=False):
        for name in sorted(dirs + files):
            guarded(workspace, Path(directory) / name)
        found.extend(Path(directory) / name for name in sorted(files))
    return sorted(found)


def catalog_path(workspace):
    return guarded(workspace, workspace.archive_dir / "catalog.json")


def catalog(workspace):
    path = catalog_path(workspace)
    require(not path.exists() or path.is_file(), "archive catalog path is not a file", "archive-collision")
    if not path.exists():
        return {"schema": SCHEMA, "entries": []}
    try:
        data = json.loads(read_text(path))
    except (ValueError, UnicodeError):
        raise VerbError("invalid archive catalog", "bad-archive-catalog")
    require(isinstance(data, dict) and data.get("schema") == SCHEMA
            and isinstance(data.get("entries"), list), "unsupported archive catalog", "bad-archive-catalog")
    return data


def render_json(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def substantive(value):
    text = str(value or "").strip()
    return bool(text and not PLACEHOLDER.search(text) and not re.fullmatch(r"\[[^\]]+\]", text) and text.lower() not in {"none", "none.", "n/a"})


def legacy_evidence(workspace, evidence, kind, identifier, statuses):
    if not evidence:
        return None
    path = selector_path(workspace, evidence)
    require(path.is_file() and path.suffix.lower() == ".md", "evidence must be a planning Markdown file", "bad-archive-evidence")
    front, _ = split_frontmatter(read_text(path))
    require(front.get("archive_kind") == kind and str(front.get("archive_id")) == identifier
            and front.get("archive_status") in statuses and substantive(front.get("archive_reason")),
            "legacy evidence must name archive_kind, archive_id, archive_status and authored archive_reason",
            "bad-archive-evidence")
    return workspace.relative(path)


def matches_selector(kind, selector, name):
    """Use the same identifier aliases for live records and catalog history."""
    if name == selector or (kind == "adr" and Path(name).stem == selector):
        return True
    if kind == "phase" and re.fullmatch(r"\d+(?:\.\d+)?", selector):
        match = phases.DIRECTORY.match(name)
        return bool(match and as_number(match.group(1)) == as_number(selector))
    if kind == "adr" and re.fullmatch(r"(?:ADR-)?\d+", selector, re.I):
        match = re.match(r"ADR-(\d+)(?:-|\.)", name, re.I)
        return bool(match and int(match.group(1)) == int(selector.upper().removeprefix("ADR-")))
    return False


def selected(workspace, kind, selector):
    require(kind in KINDS, "archive kind must be phase, adr or quick", "bad-archive-kind")
    base = guarded(workspace, workspace.planning / KINDS[kind])
    text = str(selector).strip()
    require(text, "archive selector required", "missing-selector")
    require(".." not in text.replace("\\", "/").split("/"), "traversal is not permitted", "path-escape")
    if "/" in text or "\\" in text or Path(text).is_absolute():
        candidate = selector_path(workspace, text)
        require(candidate.parent == base, "selector must name one direct record in " + KINDS[kind], "bad-archive-selector")
        return candidate
    candidates = []
    for item in sorted(base.iterdir()) if base.is_dir() else []:
        guarded(workspace, item)
        if matches_selector(kind, text, item.name):
            candidates.append(item)
    require(len(candidates) <= 1, "ambiguous archive selector", "archive-ambiguous")
    return candidates[0] if candidates else base / text


def eligibility(workspace, kind, source, evidence=None, replacement=None):
    """Use authored outcome evidence; age is deliberately never consulted."""
    identifier = source.stem if kind == "adr" else source.name
    if kind == "phase":
        match = phases.DIRECTORY.fullmatch(source.name)
        require(source.is_dir() and match is not None, "invalid phase directory", "bad-archive-selector")
        number = match.group(1)
        phase = Roadmap(workspace).find(number)
        require(phase is None or phase.status == "Complete",
                "active or incomplete phase cannot be archived", "archive-active")
        files = phases.artifacts(source, number)
        statuses = []
        outcomes = []
        plan_paths = [path for path in tree_files(workspace, source) if path.name.endswith("-PLAN.md")]
        require(all(phases.PLAN_FILE.fullmatch(path.name) and path.parent == source for path in plan_paths),
                "phase contains unregistered or noncanonical plan files", "archive-evidence-required")
        disk_plans = {path.name[:-8] for path in plan_paths}
        registered = {plan["id"] for plan in phase.plans} if phase else disk_plans
        require(disk_plans == registered,
                "phase plan files must match the registered roadmap plans", "archive-evidence-required")
        summaries = {name[:-11] for name in files["summaries"]}
        require(disk_plans <= summaries, "every plan file needs its completed summary", "archive-evidence-required")
        for path in plan_paths:
            front, _ = split_frontmatter(read_text(path))
            require(not front.get("status") or str(front["status"]).lower() == "complete",
                    "phase contains affirmatively incomplete plan work", "archive-active")
        for name in files["summaries"]:
            front, body = split_frontmatter(read_text(source / name))
            statuses.append(front.get("status"))
            outcomes.append(substantive(section_body(body, "Accomplishments")))
        verification, _ = split_frontmatter(read_text(source / files["verification"])) if files["verification"] else ({}, "")
        active = any(
            status is not None and str(status).lower() != "complete" for status in statuses)
        require(not active, "active or incomplete phase cannot be archived", "archive-active")
        state = State(workspace)
        require(not (state.phase_number and as_number(state.phase_number) == as_number(number)
                     and str(state.field(POSITION, "Status")).lower()
                     in {"in progress", "executing", "planning", "ready to execute", "ready to plan"}),
                "current active phase cannot be archived", "archive-active")
        legacy = legacy_evidence(workspace, evidence, kind, identifier, {"complete"})
        expected = registered
        proven = bool(expected) and expected <= summaries and all(status == "complete" for status in statuses) and all(outcomes)
        proven = proven and verification.get("status") == "passed"
        require(proven or legacy, "phase needs complete plan summaries and passed verification, or explicit legacy evidence", "archive-evidence-required")
        return identifier, {"phase": display_number(number), "status": "complete", "evidence": legacy or workspace.relative(source / files["verification"])}
    if kind == "quick":
        require(source.is_dir() and (source / "QUICK.md").is_file(), "invalid quick directory", "bad-archive-selector")
        front, body = split_frontmatter(read_text(source / "QUICK.md"))
        status = str(front.get("status") or "open")
        require(status not in {"open", "active", "in_progress", "in progress"}, "active quick task cannot be archived", "archive-active")
        require(status in {"complete", "abandoned", "obsolete"}, "quick task must be complete, abandoned or obsolete", "archive-evidence-required")
        legacy = legacy_evidence(workspace, evidence, kind, identifier, {status})
        proven = (bool(front.get("completed")) and substantive(section_body(body, "Verification"))) if status == "complete" else (
            substantive(front.get("archive_reason")) or substantive(section_body(body, "Retirement")))
        require(proven or legacy, "quick task needs authored verification or retirement evidence", "archive-evidence-required")
        return identifier, {"status": status, "evidence": legacy or workspace.relative(source / "QUICK.md")}
    require(source.is_file() and re.fullmatch(r"ADR-\d+(?:-[\w-]+)?\.md", source.name, re.I),
            "invalid ADR file", "bad-archive-selector")
    front, _ = split_frontmatter(read_text(source))
    status = str(front.get("status") or "proposed")
    legacy = legacy_evidence(workspace, evidence, kind, identifier, {"superseded"})
    require(status == "superseded" or legacy, "ADR needs superseded evidence", "archive-evidence-required")
    replacements = front.get("superseded_by") or []
    if isinstance(replacements, str):
        replacements = [replacements]
    if replacement:
        replacements = [replacement]
    require(len(replacements) == 1, "ADR needs one explicit replacement", "archive-replacement-required")
    value = str(replacements[0])
    target = selector_path(workspace, value) if "/" in value or "\\" in value else workspace.planning / "decisions" / (value if value.endswith(".md") else value + ".md")
    guarded(workspace, target)
    require(target.is_file() and target != source and target.parent == workspace.planning / "decisions",
            "replacement must be an existing active ADR", "bad-archive-replacement")
    new_front, _ = split_frontmatter(read_text(target))
    require(new_front.get("status") == "accepted", "replacement ADR must be accepted", "bad-archive-replacement")
    return identifier, {"status": "superseded", "evidence": legacy or workspace.relative(source), "replacement": workspace.relative(target)}


def mapped(path, source, target):
    if path == source or source in path.parents:
        return target / path.relative_to(source) if path != source else target
    return path


def rewrite_links(workspace, content, old_file, new_file, source, target):
    """Rebase local Markdown destinations and repo-relative planning references."""
    def destination(value):
        angle = value.startswith("<") and value.endswith(">")
        token = value[1:-1] if angle else value
        if re.match(r"^[A-Za-z][\w+.-]*:", token) or token.startswith(("#", "//", "/")):
            return value
        raw, marker, fragment = token.partition("#")
        raw, query_marker, query = raw.partition("?")
        if not raw:
            return value
        decoded = unquote(raw)
        old_target = (workspace.root / decoded) if decoded.startswith(".planning/") else old_file.parent / decoded
        old_target = old_target.resolve()
        new_target = mapped(old_target, source, target)
        if old_file == new_file and old_target == new_target:
            return value
        try:
            old_target.relative_to(workspace.planning.resolve())
        except ValueError:
            # Moved files may link to repo source outside planning: rebase those too.
            if old_file == new_file:
                return value
        rendered = workspace.relative(new_target) if decoded.startswith(".planning/") else Path(os.path.relpath(new_target, new_file.parent)).as_posix()
        rendered = rendered.replace(" ", "%20") if not angle else rendered
        rendered += (query_marker + query if query_marker else "") + (marker + fragment if marker else "")
        return "<" + rendered + ">" if angle else rendered
    content = LINK.sub(lambda match: match["prefix"] + destination(match["target"]) + match["tail"], content)
    content = REFERENCE.sub(lambda match: match["prefix"] + destination(match["target"]), content)
    # Bare canonical_refs and code-spelled repo paths are also durable references.
    old_prefix, new_prefix = workspace.relative(source), workspace.relative(target)
    content = PLANNING_REF.sub(lambda match: new_prefix + match[0][len(old_prefix):]
                              if match[0] == old_prefix or match[0].startswith(old_prefix + "/") else match[0], content)
    return content


def archive_index(entries):
    lines = ["# Planning archives", "", "Historical records retain their identifiers and outcome evidence.", "",
             "| Kind | ID | Record | Evidence | Replacement |", "|---|---|---|---|---|"]
    for entry in sorted(entries, key=lambda item: (item["kind"], item["id"])):
        link = lambda value: "[" + value + "](" + Path(os.path.relpath(value, ".planning/archive")).as_posix() + ")" if value else "-"
        lines.append("| " + " | ".join([entry["kind"], entry["id"], link(entry["destination"]), link(entry["evidence"]), link(entry.get("replacement"))]) + " |")
    return ("\n".join(lines) + "\n").encode("utf-8")


def encode(data):
    return base64.b64encode(data).decode("ascii") if data is not None else None


def decode(data):
    return base64.b64decode(data, validate=True) if data is not None else None


def archive(workspace, kind, selector, apply=False, evidence=None, replacement=None):
    workspace.require_planning()
    # Preview is genuinely read-only: no lock file or archive directory is created.
    if apply:
        guarded(workspace, workspace.planning / ".lock")
        with planning_lock(workspace):
            return _archive(workspace, kind, selector, True, evidence, replacement)
    return _archive(workspace, kind, selector, False, evidence, replacement)


def _archive(workspace, kind, selector, apply, evidence, replacement):
    source = selected(workspace, kind, selector)
    data = catalog(workspace)
    recovery_dir = guarded(workspace, workspace.archive_dir / "recovery")
    if recovery_dir.is_dir():
        for path in sorted(recovery_dir.glob("archive-*.json")):
            guarded(workspace, path)
            try:
                previous = json.loads(read_text(path))
            except ValueError:
                raise VerbError("invalid recovery journal", "bad-recovery-journal")
            require(isinstance(previous, dict), "invalid recovery journal", "bad-recovery-journal")
            require(previous.get("state") != "pending",
                    "recover interrupted operation first: " + path.stem, "archive-pending")
    text = str(selector).strip()
    path_selector = "/" in text or "\\" in text or Path(text).is_absolute()
    matches = [entry for entry in data["entries"] if entry["kind"] == kind and (
        entry["source"] == workspace.relative(source) if path_selector else
        matches_selector(kind, text, Path(entry["source"]).name))]
    require(len(matches) <= 1, "ambiguous archive selector", "archive-ambiguous")
    existing = matches[0] if matches else None
    if existing:
        require(not source.exists(), "active record collides with an archived identity", "archive-collision")
        destination = guarded(workspace, workspace.root / existing["destination"])
        require(destination.exists(), "archive catalog destination missing", "archive-missing")
        return {"dry_run": not apply, "state": "already_archived", "entry": existing, "moves": [], "rewritten_files": [], "recovery_id": existing["recovery_id"]}
    require(source.exists(), "archive record not found: " + str(selector), "archive-not-found")
    target = guarded(workspace, workspace.archive_dir / KINDS[kind] / source.name)
    require(not target.exists(), "archive destination already exists: " + workspace.relative(target), "archive-collision")
    identifier, facts = eligibility(workspace, kind, source, evidence, replacement)
    moved_files = tree_files(workspace, source)
    before, after, intermediate = {}, {}, {}
    for path in moved_files:
        old, new = workspace.relative(path), workspace.relative(mapped(path, source, target))
        before[old], before[new] = path.read_bytes(), None
        after[old], after[new] = None, path.read_bytes()
        intermediate[new] = path.read_bytes()
    # Rebase every moved Markdown file, and every planning document referencing it.
    planning_files = tree_files(workspace, workspace.planning)
    for path in planning_files:
        if path.suffix.lower() != ".md":
            continue
        original = path.read_bytes()
        try:
            content = original.decode("utf-8")
        except UnicodeDecodeError:
            raise VerbError("planning Markdown must be UTF-8: " + workspace.relative(path), "bad-archive-encoding")
        new_path = mapped(path, source, target)
        updated = rewrite_links(workspace, content, path, new_path, source, target)
        if updated != content:
            rel = workspace.relative(new_path)
            before.setdefault(rel, original if path == new_path else None)
            after[rel] = updated.encode("utf-8")
    if kind == "phase":
        roadmap = Roadmap(workspace)
        phase = roadmap.find(facts["phase"])
        if phase:
            rel = workspace.relative(workspace.roadmap)
            content = after.get(rel, workspace.roadmap.read_bytes()).decode("utf-8")
            roadmap.content = content
            phase = roadmap.find(facts["phase"])
            body_start = phase.end - len(phase.body)
            marker = "\n**Archived**: [" + identifier + "](archive/phases/" + source.name + ")\n"
            roadmap.content = content[:body_start] + marker + content[body_start:]
            roadmap.content = roadmap.drop_checklist(phase.number)
            roadmap.content = roadmap.update_progress_table()
            before.setdefault(rel, workspace.roadmap.read_bytes())
            after[rel] = roadmap.content.encode("utf-8")
            if workspace.state.is_file():
                state = State(workspace)
                state.derive_frontmatter(roadmap)
                state_rel = workspace.relative(workspace.state)
                # Preserve any path rebase already computed for state prose.
                _, state.body = split_frontmatter(after.get(state_rel, workspace.state.read_bytes()).decode("utf-8"))
                before.setdefault(state_rel, workspace.state.read_bytes())
                percent = state.frontmatter["progress"]["percent"]
                state.body = re.sub(r"^Progress:\s*\[.*?\]\s*\d+%[ \t]*$",
                                    "Progress: " + progress_bar(percent) + " " + str(percent) + "%",
                                    state.body, flags=re.MULTILINE)
                after[state_rel] = join_frontmatter(state.frontmatter, state.body).encode("utf-8")
    if kind == "adr":
        new_rel = workspace.relative(target)
        front, body = split_frontmatter(after[new_rel].decode("utf-8"))
        front["superseded_by"] = [facts["replacement"]]
        after[new_rel] = join_frontmatter(front, body).encode("utf-8")
        replacement_path = workspace.root / facts["replacement"]
        rel = facts["replacement"]
        original = replacement_path.read_bytes()
        front, body = split_frontmatter(after.get(rel, original).decode("utf-8"))
        supersedes = front.get("supersedes") or []
        if isinstance(supersedes, str):
            supersedes = [supersedes]
        front["supersedes"] = sorted(set(supersedes + [new_rel]))
        before.setdefault(rel, original)
        after[rel] = join_frontmatter(front, body).encode("utf-8")
    facts["evidence"] = workspace.relative(mapped(workspace.root / facts["evidence"], source, target))
    entry = dict(facts, kind=kind, id=identifier, source=workspace.relative(source), destination=workspace.relative(target))
    # Identity includes the complete proposed bytes so stale previews cannot alias a new operation.
    identity = render_json({"entry": entry, "before": {key: encode(value) for key, value in sorted(before.items())},
                            "after": {key: encode(value) for key, value in sorted(after.items())}})
    recovery_id = "archive-" + hashlib.sha256(identity).hexdigest()[:24]
    entry["recovery_id"] = recovery_id
    for previous in data["entries"]:
        for field in ("evidence", "replacement"):
            if previous.get(field):
                previous[field] = workspace.relative(mapped(workspace.root / previous[field], source, target))
    data["entries"].append(entry)
    data["entries"].sort(key=lambda item: (item["kind"], item["id"]))
    for path, content in ((catalog_path(workspace), render_json(data)), (guarded(workspace, workspace.archive_dir / "INDEX.md"), archive_index(data["entries"]))):
        rel = workspace.relative(path)
        require(not path.exists() or path.is_file(), "archive index path is not a file", "archive-collision")
        before[rel] = path.read_bytes() if path.exists() else None
        after[rel] = content
    changes = [{"path": key, "before": encode(before.get(key)), "after": encode(after.get(key)), "intermediate": encode(intermediate.get(key))} for key in sorted(set(before) | set(after)) if before.get(key) != after.get(key)]
    # Include unchanged moved bytes in the journal: recovery also guards new nested files.
    journal = {"schema": SCHEMA, "recovery_id": recovery_id, "state": "pending", "entry": entry, "changes": changes,
               "source_dirs": [workspace.relative(path) for path in [source] + sorted(p for p in source.rglob("*") if p.is_dir())] if source.is_dir() else []}
    journal["checksum"] = journal_checksum(journal)
    payload = {"dry_run": not apply, "state": "preview", "entry": entry, "moves": [{"from": entry["source"], "to": entry["destination"]}],
               "rewritten_files": [item["path"] for item in changes if item["after"] is not None], "recovery_id": recovery_id}
    if not apply:
        return payload
    journal_path = guarded(workspace, workspace.archive_dir / "recovery" / (recovery_id + ".json"))
    if journal_path.exists():
        previous = json.loads(read_text(journal_path))
        require(isinstance(previous, dict), "invalid recovery journal", "bad-recovery-journal")
        require(previous.get("state") == "recovered" and previous.get("checksum") == journal["checksum"],
                "recovery journal already exists; inspect/recover it first", "archive-pending")
        journal["history"] = previous.get("history", []) + ["recovered"]
    # Recheck every byte before the first write. No collision is discovered after the move.
    for change in changes:
        path = guarded(workspace, workspace.root / change["path"])
        require(not path.exists() or path.is_file(), "archive metadata path is not a file", "archive-collision")
        if change["after"] is not None:
            temporary = guarded(workspace, path.with_name(path.name + ".archive-tmp"))
            require(not temporary.exists(), "archive temporary file collision", "archive-collision")
        require((path.read_bytes() if path.is_file() else None) == decode(change["before"]), "record changed during archive preflight", "archive-stale")
    atomic_write(workspace, journal_path, render_json(journal))
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        source.rename(target)
        for change in changes:
            if change["after"] is not None:
                atomic_write(workspace, workspace.root / change["path"], decode(change["after"]))
        journal["state"] = "applied"
        atomic_write(workspace, journal_path, render_json(journal))
    except (OSError, VerbError) as exc:
        raise VerbError("archive interrupted; recover " + recovery_id + ": " + str(exc), "archive-interrupted")
    return dict(payload, dry_run=False, state="archived")


def journal_checksum(journal):
    return hashlib.sha256(render_json({key: value for key, value in journal.items()
                                     if key not in {"state", "checksum", "history"}})).hexdigest()


def atomic_write(workspace, path, content):
    path = guarded(workspace, path)
    temporary = guarded(workspace, path.with_name(path.name + ".archive-tmp"))
    require(not temporary.exists(), "archive temporary file collision", "archive-collision")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with temporary.open("xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def listing(workspace, kind=None):
    require(kind is None or kind in KINDS, "archive kind must be phase, adr or quick", "bad-archive-kind")
    entries = [entry for entry in catalog(workspace)["entries"] if kind is None or entry["kind"] == kind]
    journals = []
    directory = guarded(workspace, workspace.archive_dir / "recovery")
    if directory.is_dir():
        for path in sorted(directory.glob("archive-*.json")):
            guarded(workspace, path)
            try:
                data = json.loads(read_text(path))
                require(isinstance(data, dict) and data.get("schema") == SCHEMA
                        and data.get("checksum") == journal_checksum(data),
                        "invalid recovery journal: " + path.stem, "bad-recovery-journal")
            except ValueError:
                raise VerbError("invalid recovery journal: " + path.stem, "bad-recovery-journal")
            journals.append({"recovery_id": data["recovery_id"], "state": data["state"], "record": workspace.relative(path)})
    return {"entries": entries, "count": len(entries), "recoveries": journals, "directory": workspace.relative(workspace.archive_dir)}


def recover(workspace, recovery_id, apply=False):
    require(re.fullmatch(r"archive-[0-9a-f]{24}", str(recovery_id)) is not None, "invalid recovery id", "bad-recovery-id")
    guarded(workspace, workspace.planning / ".lock")
    if apply:
        with planning_lock(workspace):
            return _recover(workspace, recovery_id, True)
    return _recover(workspace, recovery_id, False)


def _recover(workspace, recovery_id, apply):
    journal_path = guarded(workspace, workspace.archive_dir / "recovery" / (recovery_id + ".json"))
    require(journal_path.is_file(), "recovery journal not found", "archive-recovery-not-found")
    try:
        journal = json.loads(read_text(journal_path))
        require(isinstance(journal, dict), "invalid recovery journal", "bad-recovery-journal")
        require(journal.get("schema") == SCHEMA and journal.get("recovery_id") == recovery_id
                and journal.get("state") in {"pending", "applied", "recovered"}, "invalid recovery journal", "bad-recovery-journal")
        require(journal.get("checksum") == journal_checksum(journal),
                "recovery journal checksum mismatch", "bad-recovery-journal")
        changes = journal["changes"]
        require(isinstance(changes, list) and changes, "empty recovery journal", "bad-recovery-journal")
        for item in changes:
            require(set(item) == {"path", "before", "after", "intermediate"}, "invalid recovery change", "bad-recovery-journal")
            guarded(workspace, workspace.root / item["path"])
            decode(item["before"])
            decode(item["after"])
            decode(item["intermediate"])
    except (KeyError, ValueError, TypeError):
        raise VerbError("invalid recovery journal", "bad-recovery-journal")
    expected_paths = {item["path"] for item in changes}
    source = guarded(workspace, workspace.root / journal["entry"]["source"])
    target = guarded(workspace, workspace.root / journal["entry"]["destination"])
    source_dirs = {str(value) for value in journal.get("source_dirs", [])}
    target_dirs = {workspace.relative(mapped(workspace.root / value, source, target)) for value in source_dirs}
    for root, directories in ((source, source_dirs), (target, target_dirs)):
        if root.exists():
            if root.is_dir():
                for path in [root] + sorted(item for item in root.rglob("*") if item.is_dir()):
                    guarded(workspace, path)
                    require(workspace.relative(path) in directories,
                            "recovery would remove an added directory: " + workspace.relative(path), "archive-recovery-conflict")
            for path in tree_files(workspace, root):
                require(workspace.relative(path) in expected_paths, "recovery would overwrite an added record: " + workspace.relative(path), "archive-recovery-conflict")
    for item in changes:
        path = guarded(workspace, workspace.root / item["path"])
        require(not path.exists() or path.is_file(), "recovery path changed type", "archive-recovery-conflict")
        current = path.read_bytes() if path.is_file() else None
        require(current in ([decode(item["before"]), decode(item["after"])]
                            + ([decode(item["intermediate"])] if item["intermediate"] is not None else [])),
                "record edited since archival: " + item["path"], "archive-recovery-conflict")
    payload = {"dry_run": not apply, "recovery_id": recovery_id, "state": "already_recovered" if journal["state"] == "recovered" else "recovery_preview",
               "restored_files": [item["path"] for item in changes if item["before"] is not None]}
    if not apply or journal["state"] == "recovered":
        return payload
    # Restore original bytes first; the journal retains them even during interruption.
    for item in changes:
        if item["before"] is not None:
            atomic_write(workspace, workspace.root / item["path"], decode(item["before"]))
    for item in changes:
        path = guarded(workspace, workspace.root / item["path"])
        if item["before"] is None and path.is_file():
            path.unlink()
    if target.is_dir():
        for path in sorted([p for p in target.rglob("*") if p.is_dir()], key=lambda p: len(p.parts), reverse=True):
            path.rmdir()
        target.rmdir()
    for directory in journal.get("source_dirs", []):
        guarded(workspace, workspace.root / directory).mkdir(parents=True, exist_ok=True)
    journal["state"] = "recovered"
    atomic_write(workspace, journal_path, render_json(journal))
    return dict(payload, dry_run=False, state="recovered")
