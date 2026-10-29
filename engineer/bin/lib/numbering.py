"""Preflighted phase renumbering with durable before-images and rollback evidence."""
from pathlib import Path
import base64
import hashlib
import re
import uuid
from .core import Failure, now, read, write, write_json
from .planning import safe
from .text import join_frontmatter, split_frontmatter
from . import phase_id


def shift_identifier(value, removed):
    text = str(value)
    match = re.match(r"^(\d+)(.*)$", text)
    if not match or int(match[1]) <= removed:
        return value
    current = str(int(match[1])-1)
    if match[1].startswith("0"):
        current = current.zfill(len(match[1]))
    return current+match[2]


def references(content, removed):
    content = re.sub(r"(?i)\bPhase\s+(" + phase_id.PATTERN + r")", lambda match: "Phase "+str(shift_identifier(match[1], removed)), content)
    content = re.sub(r"(?m)^(" + phase_id.PATTERN + r"-\d+)", lambda match: str(shift_identifier(match[1], removed)), content)
    content = re.sub(r"(?m)^(- \[[ x]\]\s*)(" + phase_id.PATTERN + r"-\d+)", lambda match: match[1]+str(shift_identifier(match[2], removed)), content)
    content = re.sub(r"(?m)^(\|\s*)(\d+)([.\s])", lambda match: match[1]+str(shift_identifier(match[2], removed))+match[3], content)
    return content


def records(root, removed):
    if isinstance(removed, bool) or not isinstance(removed, int) or removed < 1:
        raise Failure("invalid-removed-phase", str(removed), 2)
    directory = safe(root/".planning/phases")
    entries = sorted([safe(path) for path in directory.iterdir() if path.is_dir() and re.fullmatch(phase_id.PATTERN + r"-.+", path.name)],
                     key=lambda path: phase_id.sort_key(path.name)) if directory.exists() else []
    moves, files = [], []
    active = {str(path) for path in entries if phase_id.major(path.name) > removed}
    for path in entries:
        old = path.name.split("-")[0]
        new = shift_identifier(old, removed)
        if new == old:
            continue
        destination = safe(path.with_name(str(new)+path.name[len(old):]))
        if destination.exists() and str(destination) not in active:
            raise Failure("phase-renumber-conflict", str(destination))
        moves.append({"from": str(path), "to": str(destination), "old": old, "new": new})
        for artifact in path.rglob("*"):
            safe(artifact)
            if not artifact.is_file() or artifact.suffix != ".md":
                continue
            before = artifact.read_bytes()
            content = before.decode("utf-8-sig")
            metadata, body = split_frontmatter(content)
            if "phase" in metadata:
                metadata["phase"] = shift_identifier(metadata["phase"], removed)
            if isinstance(metadata.get("depends_on"), list):
                metadata["depends_on"] = [shift_identifier(value, removed) for value in metadata["depends_on"]]
            after = join_frontmatter(metadata, references(body, removed)) if metadata else references(body, removed)
            relative = artifact.relative_to(path)
            new_name = shift_identifier(relative.name, removed)
            output = safe(destination/relative.parent/str(new_name))
            files.append({"source": str(artifact), "destination": str(output), "intermediate": str(destination/relative),
                          "before_sha256": hashlib.sha256(before).hexdigest(), "before_base64": base64.b64encode(before).decode(), "after": after})
    destinations = [item["destination"] for item in files]
    if len(destinations) != len(set(destinations)):
        raise Failure("phase-renumber-conflict", "Two artifacts map to one destination")
    for item in files:
        if Path(item["source"]).read_bytes() != base64.b64decode(item["before_base64"]):
            raise Failure("phase-renumber-drift", item["source"])
    if not moves:
        return []
    journal_path = safe(root/".planning/archive/numbering"/(uuid.uuid4().hex+".json"))
    journal = {"created": now(), "state": "prepared", "removed": removed, "moves": moves, "files": files}
    write_json(journal_path, journal)
    completed_moves, completed_files = [], []
    try:
        for item in moves:
            source, target = safe(Path(item["from"])), safe(Path(item["to"]))
            if target.exists():
                raise Failure("phase-renumber-conflict", str(target))
            source.rename(target)
            completed_moves.append(item)
        for item in files:
            intermediate, target = safe(Path(item["intermediate"])), safe(Path(item["destination"]))
            if hashlib.sha256(intermediate.read_bytes()).hexdigest() != item["before_sha256"]:
                raise Failure("phase-renumber-drift", str(intermediate))
            if target != intermediate and target.exists():
                raise Failure("phase-renumber-conflict", str(target))
            if target != intermediate:
                intermediate.rename(target)
            completed_files.append(item)
            write(target, item["after"])
        journal["state"], journal["completed"] = "complete", now()
        write_json(journal_path, journal)
    except Exception as exc:
        rollback_errors = []
        for item in reversed(completed_files):
            try:
                target, intermediate = Path(item["destination"]), Path(item["intermediate"])
                if target != intermediate:
                    target.rename(intermediate)
                safe(intermediate).write_bytes(base64.b64decode(item["before_base64"]))
            except Exception as error:
                rollback_errors.append(str(error))
        for item in reversed(completed_moves):
            try:
                Path(item["to"]).rename(Path(item["from"]))
            except Exception as error:
                rollback_errors.append(str(error))
        journal.update({"state": "recovery-required" if rollback_errors else "rolled-back", "error": str(exc), "rollback_errors": rollback_errors})
        write_json(journal_path, journal)
        raise Failure("phase-renumber-failed", str(exc), journal=str(journal_path), rollback_errors=rollback_errors) from exc
    return [{"from": item["old"], "to": item["new"], "journal": str(journal_path)} for item in moves]
