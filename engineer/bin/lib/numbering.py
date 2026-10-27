"""Renumber runtime-owned phase paths and identifiers after integer removal."""
from pathlib import Path
import re
from .core import Failure, read, write
from .text import join_frontmatter, split_frontmatter


def shift_identifier(value, removed):
    text = str(value)
    match = re.match(r"^(\d+)(.*)$", text)
    if not match or int(match[1]) <= removed:
        return value
    current = str(int(match[1])-1)
    if match[1].startswith("0"):
        current = current.zfill(len(match[1]))
    return current+match[2]


def remove_dependency(content, removed):
    def replace(match):
        value = re.sub(r"(?i)(?<![\w.])(?:Phase\s+)?0*"+re.escape(str(removed))+r"(?![\d.])", "", match[2])
        value = re.sub(r"^[\s,;]+|[\s,;]+$", "", value)
        value = re.sub(r"\s*[,;]\s*[,;]\s*", ", ", value)
        return match[1]+(value or "Nothing")
    return re.sub(r"(?mi)^(\*\*Depends on(?::\*\*|\*\*:)\s*)([^\n]*)$", replace, content)


def records(root, removed):
    directory = root/".planning/phases"
    renamed = []
    entries = sorted([p for p in directory.iterdir() if p.is_dir() and re.match(r"^\d", p.name)], key=lambda p: tuple(map(int, p.name.split("-")[0].split("."))))
    for path in entries:
        old = path.name.split("-")[0]
        new = shift_identifier(old, removed)
        if new == old:
            continue
        destination = path.with_name(new+path.name[len(old):])
        if destination.exists():
            raise Failure("phase-renumber-conflict", str(destination))
        path.rename(destination)
        for artifact in list(destination.iterdir()):
            if not artifact.is_file() or artifact.suffix != ".md":
                continue
            content = read(artifact)
            metadata, body = split_frontmatter(content)
            if "phase" in metadata:
                metadata["phase"] = shift_identifier(metadata["phase"], removed)
            write(artifact, references(remove_dependency(join_frontmatter(metadata, body) if metadata else body, removed), removed))
            new_name = shift_identifier(artifact.name, removed)
            if new_name != artifact.name:
                artifact.rename(artifact.with_name(new_name))
        renamed.append({"from": old, "to": new})
    # References can occur in an earlier phase, PROJECT narrative or a todo.
    # Archives remain historical evidence and must retain their original names.
    for artifact in (root/".planning").rglob("*.md"):
        parts = artifact.relative_to(root/".planning").parts
        if any(part in ("archive", "milestones") for part in parts) or (parts and parts[0] == "phases" and len(parts) > 1 and any(parts[1].startswith(item["to"]+"-") for item in renamed)):
            continue
        content = read(artifact)
        updated = references(remove_dependency(content, removed), removed)
        if updated != content:
            write(artifact, updated)
    return renamed


def references(content, removed):
    # Explicit phase labels and plan IDs are owned identifiers. Narrative numbers
    # without these markers are preserved.
    content = re.sub(r"(?i)\bPhase\s+(\d+(?:\.\d+)?)", lambda m: "Phase "+shift_identifier(m[1], removed), content)
    content = re.sub(r"(?mi)^((?:\*\*)?Phase(?::\*\*|\*\*:|:)\s*)(\d+(?:\.\d+)?)", lambda m: m[1]+shift_identifier(m[2], removed), content)
    content = re.sub(r"(?m)^(\|\s*)(\d+)([.\s])", lambda m: m[1]+shift_identifier(m[2], removed)+m[3], content)
    content = re.sub(r"(?<![\w.-])(\d+(?:\.\d+)?-\d+)(?=-[A-Z][A-Z-]*\.md|\b)", lambda m: shift_identifier(m[1], removed), content)
    content = re.sub(r"(?<![\w.-])(\d+(?:\.\d+)?)(?=-(?:CONTEXT|RESEARCH|VERIFICATION|VALIDATION|UI-SPEC|SECURITY|REVIEW|UAT)\.md)", lambda m: shift_identifier(m[1], removed), content)
    content = re.sub(r"(?<=phases/)(\d+(?:\.\d+)?)(?=-)", lambda m: shift_identifier(m[1], removed), content)
    content = re.sub(r"(?m)^(\*\*Depends on(?::\*\*|\*\*:)\s*)(\d+(?:\.\d+)?)(?=\s|,|$)", lambda m: m[1]+shift_identifier(m[2], removed), content)
    return content
