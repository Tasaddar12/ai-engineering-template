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
            if isinstance(metadata.get("depends_on"), list):
                metadata["depends_on"] = [shift_identifier(value, removed) for value in metadata["depends_on"]]
            if metadata:
                write(artifact, join_frontmatter(metadata, body))
            new_name = shift_identifier(artifact.name, removed)
            if new_name != artifact.name:
                artifact.rename(artifact.with_name(new_name))
        renamed.append({"from": old, "to": new})
    return renamed


def references(content, removed):
    # Explicit phase labels and plan IDs are owned identifiers. Narrative numbers
    # without these markers are preserved.
    content = re.sub(r"(?i)\bPhase\s+(\d+(?:\.\d+)?)", lambda m: "Phase "+shift_identifier(m[1], removed), content)
    content = re.sub(r"(?m)^(\d+(?:\.\d+)?-\d+)", lambda m: shift_identifier(m[1], removed), content)
    content = re.sub(r"(?m)^(- \[[ x]\]\s*)(\d+(?:\.\d+)?-\d+)", lambda m: m[1]+shift_identifier(m[2], removed), content)
    content = re.sub(r"(?m)^(\|\s*)(\d+)([.\s])", lambda m: m[1]+shift_identifier(m[2], removed)+m[3], content)
    return content
