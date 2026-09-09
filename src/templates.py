"""Resolve root-authored assets and render templates with strict substitution."""

from __future__ import annotations

import re
from importlib import resources
from pathlib import Path
from typing import Any, BinaryIO

import yaml

from .errors import FrameworkError
from .io import safe_path

VARIABLE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")
ASSET_DIRECTORIES = ("agents", "templates", "workflows", "constraints")
ASSET_FILES = ("framework.yaml",)


def asset_root() -> Any:
    """Return the source/editable root or the derived installed resource root."""
    source = Path(__file__).resolve().parent.parent
    if (source / "framework.yaml").is_file() and all(
        (source / name).is_dir() for name in ASSET_DIRECTORIES
    ):
        return source
    packaged = resources.files("ai_engineering").joinpath("_assets")
    if not packaged.joinpath("framework.yaml").is_file():
        raise FrameworkError("Installed framework assets are missing")
    return packaged


def _relative_asset(relative: str) -> tuple[str, ...]:
    raw = str(relative).replace("\\", "/")
    parts = tuple(raw.split("/"))
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise FrameworkError(f"Invalid asset path: {relative}")
    if parts[0] not in {*ASSET_DIRECTORIES, *ASSET_FILES}:
        raise FrameworkError(f"Unknown asset root: {parts[0]}")
    if parts[0] in ASSET_FILES and len(parts) != 1:
        raise FrameworkError(f"Asset file cannot contain a child path: {relative}")
    return parts


def asset_file(relative: str) -> Any:
    candidate = asset_root()
    for part in _relative_asset(relative):
        candidate = candidate.joinpath(part)
    if not candidate.is_file():
        raise FrameworkError(f"Missing framework asset: {relative}")
    return candidate


def asset_bytes(relative: str) -> bytes:
    resource = asset_file(relative)
    try:
        with resource.open("rb") as handle:
            stream: BinaryIO = handle
            return stream.read()
    except OSError as exc:
        raise FrameworkError(f"Cannot read framework asset: {relative}") from exc


def asset_text(relative: str) -> str:
    try:
        return asset_file(relative).read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise FrameworkError(f"Cannot read framework asset: {relative}") from exc


def iter_asset_files(directory: str) -> list[str]:
    if directory not in ASSET_DIRECTORIES:
        raise FrameworkError(f"Unknown asset directory: {directory}")
    base = asset_root().joinpath(directory)
    if not base.is_dir():
        raise FrameworkError(f"Missing framework asset directory: {directory}")
    result: list[str] = []

    def visit(node: Any, prefix: tuple[str, ...]) -> None:
        for child in sorted(node.iterdir(), key=lambda item: item.name):
            relative = (*prefix, child.name)
            if child.is_dir():
                visit(child, relative)
            elif child.is_file():
                result.append("/".join((directory, *relative)))

    visit(base, ())
    return result


def template_text(root: Path, relative_template: str) -> str:
    installed = safe_path(Path(root), f".ai/templates/{relative_template}")
    if installed.is_file():
        path: Any = installed
    else:
        _relative_asset(f"templates/{relative_template}")
        path = asset_file(f"templates/{relative_template}")
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
