"""Strict readable records, atomic replacement, and contained paths."""

from __future__ import annotations

import os
import stat
import tempfile
from datetime import UTC, datetime
from pathlib import Path, PureWindowsPath
from typing import Any

import yaml

from .errors import FrameworkError

MAX_RECORD_BYTES = 2_000_000
RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


class StrictLoader(yaml.SafeLoader):
    """Reject duplicate keys and aliases instead of silently changing meaning."""


def _mapping(loader: StrictLoader, node: yaml.MappingNode) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if not isinstance(key, str) or key in result:
            raise FrameworkError(f"YAML keys must be unique strings: {key!r}")
        result[key] = loader.construct_object(value_node, deep=True)
    return result


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def parse_yaml(text: str) -> dict[str, Any]:
    if len(text.encode("utf-8")) > MAX_RECORD_BYTES:
        raise FrameworkError("YAML record exceeds size limit")
    try:
        if any(isinstance(token, yaml.tokens.AliasToken) for token in yaml.scan(text)):
            raise FrameworkError("YAML aliases are not supported")
        value = yaml.load(text, Loader=StrictLoader)
    except yaml.YAMLError as exc:
        raise FrameworkError(f"Invalid YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise FrameworkError("Expected a YAML mapping")
    return value


def is_link(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def reject_links(path: Path) -> None:
    for part in (path, *path.parents):
        if is_link(part):
            raise FrameworkError(f"Linked or junction path is not allowed: {part}")


def safe_path(root: Path, relative: str | Path) -> Path:
    root = Path(root).absolute()
    reject_links(root)
    raw = str(relative).replace("\\", "/")
    windows = PureWindowsPath(raw)
    parts = raw.split("/")
    if (
        not raw
        or raw.startswith("/")
        or windows.drive
        or any(part in ("", ".", "..") for part in parts)
        or any(
            part.endswith((".", " "))
            or part.split(".")[0].upper() in RESERVED_NAMES
            or any(ord(char) < 32 or char in '<>:"|?*' for char in part)
            for part in parts
        )
    ):
        raise FrameworkError(f"Expected a contained relative path: {relative}")
    target = root.joinpath(*parts)
    reject_links(target)
    if not target.resolve().is_relative_to(root.resolve()):
        raise FrameworkError(f"Path escapes root: {relative}")
    return target


def read_yaml(path: Path) -> dict[str, Any]:
    reject_links(Path(path).absolute())
    try:
        return parse_yaml(Path(path).read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise FrameworkError(f"Cannot read {path}: {exc}") from exc


def atomic_write(path: Path, text: str) -> None:
    path = Path(path).absolute()
    reject_links(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    reject_links(path)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
        ) as handle:
            temporary = handle.name
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    except OSError as exc:
        raise FrameworkError(f"Cannot write {path}: {exc}") from exc
    finally:
        if temporary:
            Path(temporary).unlink(missing_ok=True)


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    atomic_write(path, yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


def utc_now() -> str:
    return datetime.now(UTC).isoformat()
