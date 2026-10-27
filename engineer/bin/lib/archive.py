"""Exact archive transactions with durable, conflict-checked byte recovery."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
from . import records
from .core import Failure, now, planning_lock, read, root, write_json
from .text import split_frontmatter


def guarded(value):
    """Reject lexical traversal and every link/reparse component before reading."""
    path = Path(value)
    if ".." in path.parts:
        raise Failure("path-escape", str(value))
    path = path if path.is_absolute() else root()/path
    if not path.is_relative_to(root()):
        raise Failure("path-escape", str(value))
    for component in (root(), *[root().joinpath(*path.relative_to(root()).parts[:i])
                                for i in range(1, len(path.relative_to(root()).parts)+1)]):
        try:
            info = component.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise Failure("path-escape", str(component))
    return path


def _tree(path):
    """A byte snapshot also represents empty directories, without following links."""
    path = guarded(path)
    if not path.exists():
        return {}
    result = {}
    pending = [path]
    while pending:
        current = guarded(pending.pop())
        relative = current.relative_to(root()).as_posix()
        if current.is_dir():
            result[relative] = None
            pending.extend(sorted(current.iterdir(), reverse=True))
        else:
            result[relative] = base64.b64encode(current.read_bytes()).decode("ascii")
    return result


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _snapshot():
    result = {name: content for name, content in _tree(records.planning()).items()
              if not name.startswith(".planning/archive/recovery") and name != ".planning/.engineer.lock"}
    # The recovery journal is deliberately retained after rollback. Its parent
    # is infrastructure, not additional user data in the restored inventory.
    if not any(name.startswith(".planning/archive/") for name in result):
        result.pop(".planning/archive", None)
    return result


def atomic_write(path, content):
    path = guarded(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".archive-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _journal_paths():
    directory = guarded(records.planning()/"archive/recovery")
    return sorted(directory.glob("*.json")) if directory.exists() else []


def _load(path):
    try:
        value = json.loads(read(guarded(path)))
        sealed = {key: item for key, item in value.items() if key != "seal"}
        if value.get("seal") != _hash(sealed) or value.get("version") != 1:
            raise ValueError("journal checksum or version differs")
        for item in value["changes"]:
            path = guarded(item["path"])
            if not path.is_relative_to(records.planning()) or "recovery" in path.relative_to(records.planning()).parts:
                raise ValueError("journal path is outside its record scope")
            for key in ("before", "after"):
                if item[key] is not None:
                    base64.b64decode(item[key], validate=True)
        for key in ("before_tree", "after_tree"):
            if _hash(value[key]) != value[key+"_hash"]:
                raise ValueError("tree digest differs")
        return value
    except (ValueError, KeyError, TypeError) as exc:
        raise Failure("bad-recovery-journal", str(exc)) from exc


def _save(path, value):
    value = {key: item for key, item in value.items() if key != "seal"}
    write_json(guarded(path), {**value, "seal": _hash(value)})


def _authored(content, heading):
    match = re.search(r"(?ms)^## "+heading+r"\s*\n(.*?)(?=^## |\Z)", content)
    if not match:
        return False
    prose = match[1].strip()
    return len(prose) >= 12 and not re.search(r"(?im)filled on completion|how the change|^\s*\[[^]]+\]\s*$", prose)


def historical_phase_evidence(directory):
    """Validate a committed past result without treating it as current readiness.

    Source files may have evolved since verification. The phase records must
    still describe that exact result, and the digest must match Git's bytes at
    the recorded revision, rather than today's source or an unbound status.
    """
    from . import frontmatter
    directory = guarded(directory)
    reports = list(directory.glob("*-VERIFICATION.md"))
    if len(reports) != 1:
        return False
    report = guarded(reports[0])
    metadata, body = split_frontmatter(read(report))
    if (frontmatter.errors(metadata, "verification") or
            frontmatter.path_errors(report, metadata, "verification") or
            metadata.get("status") != "passed" or len(body.strip()) < 12):
        return False
    revision = metadata.get("revision", metadata.get("verified_revision", ""))
    if not isinstance(revision, str) or not re.fullmatch(r"[a-f0-9]{40,64}", revision):
        return False
    def git(*argv):
        return subprocess.run(["git", *argv], cwd=root(), capture_output=True, check=False)
    if git("merge-base", "--is-ancestor", revision, "HEAD").returncode:
        return False
    name = report.relative_to(root()).as_posix()
    committed = git("show", "HEAD:"+name)
    if committed.returncode or committed.stdout != report.read_bytes():
        return False
    # Establish when these exact report bytes entered history. A new report
    # cannot borrow an old digest after development has already moved on; an
    # actual historical report remains valid when source evolves afterwards.
    history = git("log", "--full-history", "--format=%H", "--", name)
    if history.returncode:
        return False
    witness = None
    for commit in reversed(history.stdout.decode("ascii").splitlines()):
        candidate = git("show", commit+":"+name)
        if candidate.returncode == 0 and candidate.stdout == committed.stdout:
            witness = commit
            break
    if not witness or git("merge-base", "--is-ancestor", revision, witness).returncode:
        return False
    allowed = {name, ".planning/STATE.md", ".planning/ROADMAP.md", ".planning/REQUIREMENTS.md"}
    commits = git("rev-list", revision+".."+witness)
    if commits.returncode:
        return False
    for commit in commits.stdout.decode("ascii").splitlines():
        # Inspect each parent of merges too. Net equality after a revert does
        # not prove that the frozen source survived until the first verdict.
        changed = git("diff-tree", "--no-renames", "--no-commit-id", "--name-only", "-r", "-m", "-z", commit)
        if changed.returncode or any(item.decode("utf-8") not in allowed for item in changed.stdout.split(b"\0") if item):
            return False
    relative = directory.relative_to(root()).as_posix()
    inventory = git("ls-tree", "-r", "--name-only", "-z", revision, "--", relative)
    if inventory.returncode:
        return False
    names = [item.decode("utf-8") for item in inventory.stdout.split(b"\0") if item]
    historical = {name for name in names if Path(name).parent == Path(relative)
                  and name.endswith(("-PLAN.md", "-SUMMARY.md"))}
    current = {p.relative_to(root()).as_posix() for p in directory.iterdir()
               if p.name.endswith(("-PLAN.md", "-SUMMARY.md"))}
    if not historical or current != historical:
        return False
    if any(not isinstance(item, str) for item in metadata["covered_files"]):
        return False
    covered = set(metadata["covered_files"])
    contents = {}
    for name in sorted(historical):
        path = guarded(name)
        blob = git("show", revision+":"+name)
        if blob.returncode or blob.stdout != path.read_bytes():
            return False
        contents[path] = blob.stdout
        details, _ = split_frontmatter(blob.stdout.decode("utf-8-sig"))
        kind = "plan" if name.endswith("-PLAN.md") else "summary"
        if frontmatter.errors(details, kind) or frontmatter.path_errors(path, details, kind):
            return False
        if any(not isinstance(item, str) for item in details.get("files_modified", [])):
            return False
        covered.update(details.get("files_modified", []))
        for item in details.get("must_haves", {}).get("artifacts", []):
            if isinstance(item, dict) and item.get("path"):
                if not isinstance(item["path"], str):
                    return False
                covered.add(item["path"])
    for item in covered:
        if not isinstance(item, str):
            return False
        path = guarded(item)
        if path == report:
            continue
        name = path.relative_to(root()).as_posix()
        mode = git("ls-tree", revision, "--", name)
        if mode.stdout and not mode.stdout.startswith((b"100644 ", b"100755 ")):
            return False
        blob = git("show", revision+":"+name)
        contents[path] = blob.stdout if blob.returncode == 0 else b"<missing>"
    fingerprint = hashlib.sha256()
    for path in sorted(contents, key=str):
        fingerprint.update(path.relative_to(root()).as_posix().encode()+b"\0")
        fingerprint.update(contents[path]+b"\0")
    expected = fingerprint.hexdigest()
    return metadata.get("fingerprint") == expected and metadata.get("covered_digest") == "v4:sha256:"+expected


def _evidence(path, kind, args):
    if kind == "phase":
        try:
            phase = records.roadmap_phase(path.name)
        except Failure:
            phase = None
        plans = [child for child in path.rglob("*") if child.is_file() and child.name.lower().endswith("-plan.md")]
        ids = re.findall(r"(?m)^- \[([ x])\]\s*(\d+(?:\.\d+)?-[0-9]{2})\s*:", phase["body"]) if phase else []
        if phase and (not ids or any(check != "x" for check, _ in ids)):
            raise Failure("archive-active", "Registered phase work remains incomplete")
        if {identifier for _, identifier in ids} != {child.name[:-8] for child in plans}:
            raise Failure("archive-active", "Reconcile the exact registered plan inventory before retirement")
        for plan in plans:
            if plan.parent != path or not plan.name.endswith("-PLAN.md"):
                raise Failure("archive-active", "Nested or noncanonical plan records remain")
            metadata, _ = split_frontmatter(read(plan))
            summary = plan.with_name(plan.name.replace("-PLAN.md", "-SUMMARY.md"))
            details, prose = split_frontmatter(read(summary))
            if metadata.get("status") in ("in_progress", "blocked", "halted", "open") or details.get("status") != "complete":
                raise Failure("archive-active", "Every plan requires completed source evidence")
            if not _authored(prose, "Accomplishments"):
                raise Failure("archive-evidence-required", "Completed summaries require authored accomplishments")
        if historical_phase_evidence(path):
            return
        if args.has("evidence"):
            metadata, _ = split_frontmatter(read(guarded(args.get("evidence"))))
            if metadata.get("archive_kind") == kind and metadata.get("archive_id") == path.name and metadata.get("archive_status") == "complete" and len(str(metadata.get("archive_reason", ""))) >= 12:
                return
    elif kind == "quick":
        metadata, body = split_frontmatter(read(path/"QUICK.md"))
        status = metadata.get("status")
        if status not in ("complete", "abandoned", "obsolete"):
            raise Failure("archive-active", "Quick task remains active")
        if metadata.get("completed") and _authored(body, "Verification" if status == "complete" else "Retirement"):
            return
    elif kind == "adr":
        metadata, _ = split_frontmatter(read(path))
        replacements = metadata.get("superseded_by", [])
        if metadata.get("status") in ("superseded", "retired") and replacements:
            for identifier in replacements:
                _replacement(identifier)
            return
    else:
        from .planning_review import _retired
        if _retired(path):
            return
    raise Failure("archive-evidence-required", "Explicit retirement outcome evidence is required")


def _replacement(identifier):
    identifier = str(identifier).removesuffix(".md")
    if not re.fullmatch(r"ADR-\d+(?:-[\w-]+)?", identifier):
        raise Failure("archive-evidence-required", "Replacement requires an exact ADR identity")
    base = guarded(records.planning()/"decisions")
    numeric = re.fullmatch(r"ADR-\d+", identifier)
    candidates = [path for path in base.iterdir() if path.suffix == ".md" and
                  (path.stem.startswith(identifier+"-") if numeric else path.stem == identifier)] if base.exists() else []
    if len(candidates) != 1:
        raise Failure("archive-evidence-required", "Replacement ADR is absent or ambiguous")
    return guarded(candidates[0])


def _selection(args):
    values = args.all("paths") or args.all("path")
    kind = args.arg(0, "record")
    if not values:
        selector = args.need(1)
        directory = {"phase": "phases", "quick": "quick", "adr": "decisions"}.get(kind)
        if not directory:
            raise Failure("missing-archive-selection", "Select phase, quick, adr, or exact --paths")
        base = guarded(records.planning()/directory)
        if "/" in selector or "\\" in selector:
            values = [selector]
        else:
            stem = selector.removesuffix(".md")
            if kind == "phase" and re.fullmatch(r"\d+(?:\.\d+)?", stem):
                stem = records.number(stem)
            if kind == "adr" and re.fullmatch(r"(?i)(?:adr-)?\d+", stem):
                stem = "ADR-"+str(int(re.sub(r"(?i)^adr-", "", stem))).zfill(3)
            if any(character in selector for character in "*?[]") or selector in (".", ".."):
                raise Failure("invalid-archive-selection", selector)
            numeric = (kind == "phase" and re.fullmatch(r"\d+(?:\.\d+)?", stem)) or (kind == "adr" and re.fullmatch(r"ADR-\d+", stem))
            values = sorted(path for path in base.iterdir() if path.is_dir() == (kind != "adr")
                            and (kind != "adr" or path.suffix == ".md")
                            and (path.stem == stem if kind == "adr" and not numeric else
                                 records.number(path.name) == stem if numeric and kind == "phase" and re.match(r"^\d+(?:\.\d+)?-", path.name) else
                                 path.name.startswith(stem+"-") if numeric and kind == "adr" else path.name == selector)) if base.exists() else []
            if len(values) != 1:
                raise Failure("archive-ambiguous" if values else "archive-not-found", selector)
    paths = [guarded(value) for value in values]
    if kind == "record":
        inferred = {("phase" if relative.parts[0] == "phases" else "quick" if relative.parts[0] == "quick" else "adr" if relative.parts[0] == "decisions" else "record")
                    for path in paths if path.is_relative_to(records.planning())
                    and (relative := path.relative_to(records.planning())).parts}
        if len(inferred) > 1:
            raise Failure("mixed-archive-selection", "Review each retirement kind separately")
        kind = next(iter(inferred), kind)
    for path in paths:
        relative = path.relative_to(records.planning()) if path.is_relative_to(records.planning()) else Path()
        if len(relative.parts) < 2 or relative.parts[0] in ("archive",) or not path.exists():
            raise Failure("invalid-archive-selection", str(path))
        if kind in ("phase", "quick", "adr") and len(relative.parts) != 2:
            raise Failure("invalid-archive-selection", str(path))
        if kind in ("phase", "quick", "adr") and relative.parts[0] != {"phase": "phases", "quick": "quick", "adr": "decisions"}[kind]:
            raise Failure("invalid-archive-selection", str(path))
        if kind in ("phase", "quick") and not path.is_dir():
            raise Failure("invalid-archive-selection", str(path))
        _tree(path)
        _evidence(path, kind, args)
    if len(set(paths)) != len(paths) or any(a != b and a.is_relative_to(b) for a in paths for b in paths):
        raise Failure("overlapping-archive-selection", "Select non-overlapping exact paths")
    return kind, paths


def catalog():
    path = guarded(records.planning()/"archive/catalog.json")
    return json.loads(read(path)) if path.is_file() else []


def _matches(entry, kind, selector):
    if entry["kind"] != kind:
        return False
    if selector in (entry["id"], entry["id"]+".md", entry["path"], entry["archived_path"]):
        return True
    if kind == "phase":
        try:
            return records.number(selector) == records.number(entry["id"])
        except ValueError:
            return selector == entry["id"].split("-", 1)[-1]
    if kind == "adr" and re.fullmatch(r"(?i)(?:adr-)?\d+", selector):
        return int(re.sub(r"(?i)^adr-", "", selector)) == int(re.match(r"(?i)ADR-(\d+)", entry["id"])[1])
    return False


def _rebase(content, source, destination, moves):
    def mapped(path):
        for before, after in moves:
            if path.is_relative_to(before):
                return after/path.relative_to(before)
        return path
    def link(match):
        target = match[2]
        if re.match(r"[a-zA-Z]+:|#|/", target):
            return match[0]
        base, separator, fragment = target.partition("#")
        resolved = (source.parent/base).resolve()
        target = os.path.relpath(mapped(resolved), destination.parent).replace("\\", "/")
        return match[1]+target+(separator+fragment if separator else "")+match[3]
    content = re.sub(r"(\]\()([^\s)]+)(\))", link, content)
    content = re.sub(r"(?m)(^\[[^\]]+\]:\s*)(\S+)()", link, content)
    for before, after in moves:
        content = content.replace(before.relative_to(root()).as_posix(), after.relative_to(root()).as_posix())
    return content


def archive(args):
    if any(_load(path)["state"] == "pending" for path in _journal_paths()):
        raise Failure("archive-pending", "Recover the interrupted archive before starting another")
    previous = [entry for entry in catalog() if _matches(entry, args.arg(0), args.arg(1, ""))]
    if previous:
        if len(previous) != 1:
            raise Failure("archive-ambiguous", "Select the exact archived identity")
        entry = previous[0]
        source = guarded(entry["path"])
        if source.exists():
            raise Failure("archive-collision", "An active record reuses the archived identity")
        if entry["kind"] == "phase" and any(records.number(path.name) == records.number(entry["id"]) for path in records.phases()):
            raise Failure("archive-collision", "An active phase reuses the archived number")
        if args.arg(0) == "adr" and re.fullmatch(r"(?i)(?:adr-)?\d+", args.arg(1, "")):
            identity = re.match(r"(?i)ADR-(\d+)", entry["id"])[1]
            if list(guarded(records.planning()/"decisions").glob("ADR-"+identity+"*.md")):
                raise Failure("archive-collision", "An active ADR reuses the archived number")
        return {"state": "already_archived", "recovery_id": entry["recovery_id"], "archived": True}
    kind, paths = _selection(args)
    moves = [(path, guarded(records.planning()/"archive"/path.relative_to(records.planning()))) for path in paths]
    if any(target.exists() for _, target in moves):
        raise Failure("archive-collision", "An archive destination already exists")
    before = _snapshot()
    after = dict(before)
    for source, target in moves:
        for name, value in list(after.items()):
            original = root()/name
            if original.is_relative_to(source):
                after.pop(name)
                after[(target/original.relative_to(source)).relative_to(root()).as_posix()] = value
    for name, value in list(after.items()):
        if value is None or not name.lower().endswith(".md"):
            continue
        destination = root()/name
        source = destination
        for old, new in moves:
            if destination.is_relative_to(new):
                source = old/destination.relative_to(new)
        content = base64.b64decode(value).decode("utf-8")
        after[name] = base64.b64encode(_rebase(content, source, destination, moves).encode()).decode()
    # Parent directories are explicit so recovery can guard and remove only its own.
    for name in list(after):
        parent = Path(name).parent
        while parent != Path("."):
            after.setdefault(parent.as_posix(), None)
            parent = parent.parent
    changes = [{"path": name, "before_exists": name in before, "after_exists": name in after,
                "before": before.get(name), "after": after.get(name)}
               for name in sorted(set(before)|set(after)) if (name in before, before.get(name)) != (name in after, after.get(name))]
    snapshot = _hash({"paths": [str(path.relative_to(root())) for path in paths], "before": before})
    identifier = snapshot[:24]
    journal_path = records.planning()/"archive/recovery"/(identifier+".json")
    packet = {"recovery_id": identifier, "snapshotDigest": snapshot, "digest": snapshot,
              "entries": [{"id": source.name if source.is_dir() else source.stem, "kind": kind, "path": source.relative_to(root()).as_posix(), "archived_path": target.relative_to(root()).as_posix()} for source, target in moves]}
    entries = catalog()
    for entry in entries:
        for old, new in moves:
            entry["replacement"] = str(entry.get("replacement", "")).replace(old.relative_to(root()).as_posix(), new.relative_to(root()).as_posix())
    phase_spans = []
    phase_labels = []
    for entry, (source, target) in zip(packet["entries"], moves):
        entry["recovery_id"] = identifier
        if kind == "phase":
            try:
                phase = records.roadmap_phase(source.name)
                entry.update({key: phase.get(key) for key in ("number", "name", "milestone", "goal", "requirements")})
                entry["roadmap_member"] = True
                entry["plan_count"] = len(re.findall(r"(?m)^- \[[ x]\]\s*\d", phase["body"]))
                phase_spans.append((phase["start"], phase["end"]))
                phase_labels.append(r"0*"+str(int(phase["number"].split(".")[0]))+(r"\."+phase["number"].split(".")[1] if "." in phase["number"] else ""))
            except Failure:
                entry.update({"number": records.number(source.name), "name": source.name.split("-", 1)[-1], "plan_count": 0})
        if kind == "adr":
            metadata, _ = split_frontmatter(read(source))
            replacement = _replacement(metadata["superseded_by"][0])
            entry["replacement"] = replacement.relative_to(root()).as_posix()
            from .text import join_frontmatter
            archived_name = target.relative_to(root()).as_posix()
            moved_metadata, moved_body = split_frontmatter(base64.b64decode(after[archived_name]).decode())
            moved_metadata["superseded_by"] = [entry["replacement"]]
            after[archived_name] = base64.b64encode(join_frontmatter(moved_metadata, moved_body).encode()).decode()
            replacement_name = replacement.relative_to(root()).as_posix()
            new_metadata, new_body = split_frontmatter(base64.b64decode(after[replacement_name]).decode())
            supersedes = new_metadata.get("supersedes", [])
            if archived_name not in supersedes:
                new_metadata["supersedes"] = [*supersedes, archived_name]
            after[replacement_name] = base64.b64encode(join_frontmatter(new_metadata, new_body).encode()).decode()
        entries.append(entry)
    if phase_spans:
        roadmap_name = ".planning/ROADMAP.md"
        roadmap = base64.b64decode(before[roadmap_name]).decode()
        for start, end in sorted(phase_spans, reverse=True):
            roadmap = roadmap[:start]+roadmap[end:]
        for label in phase_labels:
            roadmap = re.sub(r"(?m)^- \[[ x]\]\s*\*\*Phase\s+"+label+r":.*\n?", "", roadmap)
            roadmap = re.sub(r"(?m)^\|\s*"+label+r"\.\s*[^\n]+\n?", "", roadmap)
        after[roadmap_name] = base64.b64encode(_rebase(roadmap, root()/roadmap_name, root()/roadmap_name, moves).encode()).decode()
    if kind == "phase" and ".planning/STATE.md" in after:
        from .text import join_frontmatter
        metadata, body = split_frontmatter(base64.b64decode(after[".planning/STATE.md"]).decode())
        progress = records.derived_progress()
        for entry in packet["entries"]:
            progress["total_phases"] -= int(entry.get("roadmap_member", False))
            progress["completed_phases"] -= int(entry.get("roadmap_member", False))
            progress["total_plans"] -= entry["plan_count"]
            progress["completed_plans"] -= entry["plan_count"]
        progress["completed_phases"] = max(0, progress["completed_phases"])
        progress["percent"] = round(100*progress["completed_plans"]/progress["total_plans"]) if progress["total_plans"] else 0
        metadata["progress"] = progress
        after[".planning/STATE.md"] = base64.b64encode(join_frontmatter(metadata, body).encode()).decode()
    after[".planning/archive/catalog.json"] = base64.b64encode((json.dumps(entries, indent=2)+"\n").encode()).decode()
    index = "# Archived planning records\n\n"+"\n".join("- ["+entry["id"]+"]("+os.path.relpath(root()/entry["archived_path"], records.planning()/"archive").replace("\\", "/")+")" for entry in entries)+"\n"
    after[".planning/archive/INDEX.md"] = base64.b64encode(index.encode()).decode()
    changes = [{"path": name, "before_exists": name in before, "after_exists": name in after,
                "before": before.get(name), "after": after.get(name)}
               for name in sorted(set(before)|set(after)) if (name in before, before.get(name)) != (name in after, after.get(name))]
    if not args.has("apply") and not args.has("confirm"):
        return {**packet, "dry_run": True, "state": "preview", "archived": False}
    if args.get("expect", args.get("expect-digest")) != snapshot:
        raise Failure("archive-preview-stale", "Exact archive apply requires its reviewed preview digest")
    with planning_lock():
        current = _snapshot()
        if current != before:
            raise Failure("archive-source-drift", "Planning records changed since preview")
        history = [_load(journal_path)["state"]] if journal_path.exists() else []
        journal = {**packet, "version": 1, "state": "pending", "history": history, "changes": changes,
                   "before_tree": before, "after_tree": after, "before_tree_hash": _hash(before), "after_tree_hash": _hash(after)}
        _save(journal_path, journal)
        try:
            _apply(changes, "after")
        except OSError as exc:
            raise Failure("archive-interrupted", "Archive interrupted; recover the pending journal", recovery_id=identifier) from exc
        journal["state"] = "archived"
        _save(journal_path, journal)
    return {**packet, "archived": True, "state": "archived", "dry_run": False}


def _apply(changes, side):
    for item in sorted(changes, key=lambda row: len(Path(row["path"]).parts), reverse=True):
        path = guarded(item["path"])
        if not item[side+"_exists"] and path.exists():
            if path == records.planning()/"archive" and (path/"recovery").is_dir():
                continue
            path.rmdir() if path.is_dir() else path.unlink()
    for item in sorted(changes, key=lambda row: len(Path(row["path"]).parts)):
        if item[side+"_exists"]:
            path = guarded(item["path"])
            if item[side] is None:
                path.mkdir(parents=True, exist_ok=True)
            else:
                atomic_write(path, base64.b64decode(item[side]))


def recover(args):
    identifier = args.need()
    if not re.fullmatch(r"[0-9a-f]{24}", identifier):
        raise Failure("invalid-archive-id", identifier)
    journal_path = guarded(records.planning()/"archive/recovery"/(identifier+".json"))
    if not journal_path.is_file():
        raise Failure("archive-not-found", identifier)
    journal = _load(journal_path)
    if journal["state"] == "recovered":
        return {"state": "already_recovered", "recovery_id": identifier}
    with planning_lock():
        current = _snapshot()
        # Pending writes may be any prefix of the transaction, but never new user data.
        if journal["state"] == "archived":
            valid = current == journal["after_tree"]
        else:
            valid = all((name in current, current.get(name)) in ((name in journal[side+"_tree"], journal[side+"_tree"].get(name)) for side in ("before", "after"))
                        for name in set(current)|set(journal["before_tree"])|set(journal["after_tree"]))
        if not valid:
            raise Failure("archive-recovery-conflict", "Later file or directory changes require reconciliation")
        packet = {"recovery_id": identifier, "recoveryDigest": _hash(current), "dry_run": not (args.has("apply") or args.has("confirm"))}
        if packet["dry_run"]:
            return {**packet, "state": "preview"}
        if args.get("expect", args.get("expect-digest")) != packet["recoveryDigest"]:
            raise Failure("archive-recovery-stale", "Recovery apply requires its fresh reviewed digest")
        _apply(journal["changes"], "before")
        journal["state"] = "recovered"
        _save(journal_path, journal)
    return {**packet, "state": "recovered", "recovered": True}


def archives(args):
    journals = [_load(path) for path in _journal_paths()]
    entries = [entry for entry in catalog() if not args.has("kind") or entry["kind"] == args.get("kind")]
    return {"entries": entries, "archives": entries, "count": len(entries),
            "recoveries": [{"recovery_id": journal["recovery_id"], "state": journal["state"]} for journal in journals]}
