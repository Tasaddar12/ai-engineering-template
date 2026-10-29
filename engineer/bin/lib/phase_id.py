"""Canonical numeric, dotted and letter-suffix phase identifiers."""
import re
from .core import Failure

PATTERN = r"\d+[a-z]?(?:\.\d+[a-z]?)*"


def normalize(value):
    text = str(value).split("-", 1)[0]
    if not re.fullmatch(PATTERN, text) or major(text) < 1:
        raise Failure("invalid-phase-number", str(value), 2)
    parts = []
    for index, part in enumerate(text.split(".")):
        match = re.fullmatch(r"(\d+)([a-z]?)", part)
        numeric = str(int(match[1]))
        parts.append((numeric.zfill(2) if index == 0 else numeric) + match[2])
    return ".".join(parts)


def major(value):
    match = re.match(r"\d+", str(value))
    return int(match[0]) if match else 0


def sort_key(value):
    return tuple((int(match[1]), match[2]) for part in normalize(value).split(".")
                 for match in [re.fullmatch(r"(\d+)([a-z]?)", part)])


def next_child(base, identifiers):
    children = []
    for value in identifiers:
        match = re.fullmatch(re.escape(base) + r"\.(\d+)", value)
        if match:
            children.append(int(match[1]))
    return base + "." + str(max(children, default=0) + 1)
