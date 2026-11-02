"""Fallow binary resolution and report normalisation.

Ported from gsd-core ``src/fallow-runner.cts`` at pinned commit
d37ff11b47258b560f0cf8f1132b42ecd90e0c79 (MIT, Copyright (c) 2026 Open GSD),
together with the pieces of ``src/shell-command-projection.cts`` it depends on
(``resolveExecutableBinary``, ``envGet``, ``_isFile``, ``DEFAULT_PATHEXT``),
inlined here as private ``_`` helpers.

Parses the real ``fallow audit --format json`` schema (schema_version 3
envelope, nested ``dead_code`` / ``duplication`` sections) into the compact
``{summary, findings[]}`` contract the code reviewer consumes.

Deviations:
- Upstream functions take an options object ``{cwd, envPath}``; the Python
  functions take ``cwd`` and ``env_path`` as arguments. ``env_path=None`` means
  "use the ambient PATH" (upstream: ``envPath`` omitted).
- ``fs.accessSync(path, X_OK)`` becomes ``os.access(path, os.X_OK)``; like
  upstream it is consulted only on non-win32 platforms and only when the caller
  requires an executable.
- Only ``resolveExecutableBinary`` (and its helpers) is taken from the platform
  seam; ``projectSpawnInvocation``, ``execTool``, ``execNpm`` and the cmd.exe
  quoting helpers are not ported because ``fallow-runner`` does not use them.
- Upstream exposes no CLI for this module, so none is provided.
- This repo's ``review.normalize-structural`` verb
  (``engineer/bin/lib/runtime_tools.py``) validates an already-normalized report
  and does not convert the raw fallow schema; it is not wired to this module.
"""
from __future__ import annotations

import json
import os
import sys

DEFAULT_PATHEXT = ".EXE;.CMD;.BAT;.COM"

_NO_BINARY_MESSAGE = (
    "Fallow is enabled but no binary was found. "
    "Please install fallow via `npm install -D fallow` or `cargo install fallow`."
)


# --- platform seam (inlined from shell-command-projection.cts) ---------------

def _is_file(candidate, require_executable=False, platform=None):
    platform = sys.platform if platform is None else platform
    try:
        if not os.path.isfile(candidate):
            return False
        if require_executable and platform != "win32" and not os.access(candidate, os.X_OK):
            return False
        return True
    except Exception:
        return False


def _env_get(env, name):
    """Read an environment variable by name, case-insensitively (exact match wins)."""
    if name in env:
        return env[name]
    lower = name.lower()
    for key in env:
        if key.lower() == lower:
            return env[key]
    return None


def _join(*parts):
    return os.path.normpath(os.path.join(*parts))


def _resolve_executable_binary(name, platform=None, env=None, prepend_paths=(), require_executable=False,
                               path_override=None):
    """Resolve a declared command name to the file a spawn can start, or ``None``.

    win32 tries PATHEXT entries only (never the bare name) unless the name already
    carries a PATHEXT-listed extension; other platforms scan for the bare name.
    ``path_override`` replaces ``env["PATH"]`` as the search path while PATHEXT is
    still read from ``env`` (default: the ambient environment).
    """
    if not name:
        return None
    platform = sys.platform if platform is None else platform
    if "/" in name or "\\" in name:
        return name if _is_file(name, require_executable, platform) else None
    env = os.environ if env is None else env
    raw_path = path_override if path_override is not None else (_env_get(env, "PATH") or "")
    segments = [*prepend_paths, *[part for part in str(raw_path).split(os.pathsep) if part]]

    if platform != "win32":
        for directory in segments:
            candidate = _join(directory, name)
            if _is_file(candidate, require_executable, platform):
                return candidate
        return None

    extensions = [ext for ext in str(_env_get(env, "PATHEXT") or DEFAULT_PATHEXT).split(";") if ext]
    lower = name.lower()
    carries_known_ext = any(lower.endswith(ext.lower()) for ext in extensions)
    for directory in segments:
        if carries_known_ext:
            as_is = _join(directory, name)
            if _is_file(as_is, require_executable, platform):
                return as_is
        for ext in extensions:
            candidate = _join(directory, name + ext)
            if _is_file(candidate, require_executable, platform):
                return candidate
    return None


# --- binary resolution -------------------------------------------------------

def resolve_fallow_binary(cwd, env_path=None):
    """Resolve the ``fallow`` binary: ``<cwd>/node_modules/.bin`` first, then ``env_path``.

    ``env_path`` defaults to the ambient ``PATH``. Returns ``None`` when absent.
    """
    if env_path is None:
        env_path = os.environ.get("PATH", "")
    return _resolve_executable_binary(
        "fallow",
        prepend_paths=[_join(cwd, "node_modules", ".bin")],
        path_override=env_path,
        require_executable=True,
    )


def require_fallow_binary(cwd, env_path=None):
    """Like ``resolve_fallow_binary`` but raise ``RuntimeError`` with install guidance when absent."""
    binary = resolve_fallow_binary(cwd, env_path)
    if binary:
        return binary
    raise RuntimeError(_NO_BINARY_MESSAGE)


# --- report normalisation ----------------------------------------------------

def _get(value, key):
    """Property read that yields ``None`` for anything that is not a mapping (JS ``undefined``)."""
    return value.get(key) if isinstance(value, dict) else None


def _object_items(value):
    """Upstream filter: a list's entries that are non-null objects (mappings or arrays)."""
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, (dict, list))]


def _js_str(value):
    """Template-literal / ``Array.prototype.join`` string conversion for JSON values."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value != value:
            return "NaN"
        if value in (float("inf"), float("-inf")):
            return "Infinity" if value > 0 else "-Infinity"
        return str(int(value)) if value == int(value) else repr(value)
    if isinstance(value, list):
        return ",".join(_js_str(item) for item in value)
    return "[object Object]"


def _coalesce(value, default):
    return default if value is None else value


def normalize_fallow_report(report):
    """Normalise a raw fallow audit report into ``{"summary": {...}, "findings": [...]}``.

    ``report`` may be ``None`` or any JSON value; malformed sections count as empty.
    """
    dead_code = _get(report, "dead_code")
    duplication = _get(report, "duplication")
    unused_exports = _object_items(_get(dead_code, "unused_exports"))
    unused_files = _object_items(_get(dead_code, "unused_files"))
    circular_deps = _object_items(_get(dead_code, "circular_dependencies"))
    clone_groups = _object_items(_get(duplication, "clone_groups"))

    findings = []

    for item in unused_exports:
        findings.append({
            "type": "unused_export",
            "message": "Unused export " + _js_str(_coalesce(_get(item, "export_name"), "<unknown>")),
            "file": _coalesce(_get(item, "path"), ""),
            "line": _coalesce(_get(item, "line"), None),
        })

    for item in unused_files:
        findings.append({
            "type": "unused_file",
            "message": "Unused file " + _js_str(_coalesce(_get(item, "path"), "<unknown>")),
            "file": _coalesce(_get(item, "path"), ""),
            "line": None,
        })

    for item in circular_deps:
        files = _get(item, "files")
        files = files if isinstance(files, list) else []
        findings.append({
            "type": "circular_dependency",
            "message": "Circular dependency: " + " -> ".join(_js_str(entry) for entry in files),
            "file": files[0] if files else "",
            "line": _coalesce(_get(item, "line"), None),
        })

    for group in clone_groups:
        instances = _get(group, "instances")
        instances = instances if isinstance(instances, list) else []
        first = instances[0] if len(instances) > 0 else None
        second = instances[1] if len(instances) > 1 else None
        findings.append({
            "type": "duplicate_block",
            "message": f"Duplicate block ({len(instances)} instances)",
            "file": _coalesce(_get(first, "file"), ""),
            "line": _coalesce(_get(first, "start_line"), None),
            "related_file": _coalesce(_get(second, "file"), ""),
        })

    return {
        "summary": {
            "unused_exports": len(unused_exports),
            "unused_files": len(unused_files),
            "duplicates": len(clone_groups),
            "circular_dependencies": len(circular_deps),
            "total": len(findings),
        },
        "findings": findings,
    }


def normalize_fallow_report_file(file_path):
    """Read and normalise a fallow JSON report file; unreadable or invalid files yield an empty report."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
            return normalize_fallow_report(json.loads(handle.read()))
    except Exception:
        return normalize_fallow_report(None)
