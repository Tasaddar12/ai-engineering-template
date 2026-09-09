"""Reusable prompt and artifact assets with strict variable substitution."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .errors import FrameworkError
from .io import safe_path

VARIABLE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def asset_root() -> Path:
    return Path(__file__).parent / "templates"


def template_text(root: Path, relative_template: str) -> str:
    installed = safe_path(Path(root), f".ai/templates/{relative_template}")
    path = installed if installed.is_file() else safe_path(asset_root(), relative_template)
    try:
        return path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise FrameworkError(f"Missing template: {relative_template}") from exc


def render(root: Path, relative_template: str, values: dict[str, Any]) -> str:
    source = template_text(root, relative_template)
    missing = set(VARIABLE.findall(source)) - values.keys()
    if missing:
        raise FrameworkError(f"Missing template values: {', '.join(sorted(missing))}")

    def substitute(match: re.Match[str]) -> str:
        value = values[match.group(1)]
        if isinstance(value, (dict, list, tuple)):
            return yaml.safe_dump(value, sort_keys=False, allow_unicode=True).rstrip()
        return "None" if value is None else str(value)

    return VARIABLE.sub(substitute, source)
