"""Path-scoped code-review depth resolution.

Ported from gsd-core ``src/code-review-depth.cts`` at pinned commit
d37ff11b47258b560f0cf8f1132b42ecd90e0c79 (MIT, Copyright (c) 2026 Open GSD).

Zero I/O, zero clock. Resolves the effective review depth (``quick`` |
``standard`` | ``deep``) from, in priority order: the ``--depth=`` flag, the
strongest matching path-scoped rule in ``workflow.code_review_depth_overrides``,
the global ``workflow.code_review_depth`` config value, and the ``standard``
default, then applies the large-scope ``deep`` -> ``standard`` downgrade.

Inputs and results are plain dicts that keep the upstream camelCase field names
(``flagDepth``, ``configDepth``, ``overrides``, ``files``, ``repoRoot``,
``resolvedDepth``, ``matchedRule``, ``fileCount``, ``ruleIndex``...).

Deviations:
- Upstream exposes no CLI, so none is provided.
- Upstream distinguishes an absent ``overrides`` property (treated as ``[]``)
  from an explicit ``null``; here an absent dict key is treated as ``[]`` and an
  explicit ``None`` is rejected as ``not_an_array``.
- The upstream ``REASON`` object is a read-only ``MappingProxyType``.
- ``engineer/bin/lib/workflow_ops.py`` ``review_depth`` is a separate
  implementation bound to this repo's config and is not wired to this module.
"""
from __future__ import annotations

from types import MappingProxyType
import re

REASON = MappingProxyType({
    "NOT_AN_ARRAY": "not_an_array",
    "RULE_NOT_OBJECT": "rule_not_object",
    "PATHS_MALFORMED": "paths_malformed",
    "INVALID_DEPTH": "invalid_depth",
    "GLOB_UNSUPPORTED": "glob_unsupported",
    "PATH_CONTROL_CHAR": "path_control_char",
    "PATH_TRAVERSAL": "path_traversal",
    "PATH_ABSOLUTE": "path_absolute",
    "PATH_EMPTY": "path_empty",
})

DEPTH_TIERS = ("quick", "standard", "deep")
LARGE_SCOPE_THRESHOLD = 50

# ECMAScript String.prototype.trim whitespace (Python's str.strip differs).
_JS_WHITESPACE = (
    "\t\n\v\f\r           "
    "       　﻿"
)
_DRIVE_SLASH = re.compile(r"^[A-Za-z]:/")
_DRIVE = re.compile(r"^[A-Za-z]:")
_GLOB = re.compile(r"[*?]")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_SLASHES = re.compile(r"/+")


def _trim(value):
    return value.strip(_JS_WHITESPACE)


def normalize_rel_path(p, repo_root=None):
    """Normalize a repo-relative-ish path for matching. Idempotent.

    Non-strings become an empty string. Whitespace is trimmed, backslashes become
    ``/``, repeated ``/`` collapse, a leading ``repo_root/`` prefix and leading
    ``./`` segments are stripped, and a trailing ``/`` is removed. A leading ``/``
    is stripped only when the path was relativized against ``repo_root`` or was
    never absolute, so an absolute path outside the repo stays absolute.
    """
    value = p if isinstance(p, str) else ""
    value = _trim(value)
    value = value.replace("\\", "/")
    value = _SLASHES.sub("/", value)

    is_absolute = value.startswith("/") or bool(_DRIVE_SLASH.match(value))
    relativized = False

    if isinstance(repo_root, str) and repo_root != "":
        root_normalized = re.sub(r"/+$", "", _trim(repo_root).replace("\\", "/"))
        if root_normalized != "" and value.startswith(root_normalized + "/"):
            value = value[len(root_normalized) + 1:]
            relativized = True

    previous = None
    while value != previous:
        previous = value
        if value.startswith("./"):
            value = value[2:]

    if (relativized or not is_absolute) and value.startswith("/"):
        value = value[1:]
    if value.endswith("/") and value != "/":
        value = value[:-1]
    return value


def rule_matches_file(rule_path, file_path):
    """True iff ``file_path == rule_path`` or it starts with ``rule_path + "/"``.

    Both arguments must already be normalized. Case-sensitive.
    """
    return file_path == rule_path or file_path.startswith(rule_path + "/")


def _validate_rule_path(raw_path):
    """Return ``(error_key, normalized)``; ``error_key`` is ``None`` when valid."""
    slashified = _trim(raw_path).replace("\\", "/")

    if _GLOB.search(slashified):
        return "GLOB_UNSUPPORTED", None
    if _CONTROL.search(slashified):
        return "PATH_CONTROL_CHAR", None

    collapsed = _SLASHES.sub("/", slashified)
    if ".." in collapsed.split("/"):
        return "PATH_TRAVERSAL", None

    looks_absolute = slashified.startswith("/") or bool(_DRIVE.match(slashified))

    normalized = collapsed
    previous = None
    while normalized != previous:
        previous = normalized
        if normalized.startswith("./"):
            normalized = normalized[2:]
    if normalized.startswith("/"):
        normalized = normalized[1:]
    if normalized.endswith("/"):
        normalized = normalized[:-1]

    if looks_absolute and normalized not in ("", "."):
        return "PATH_ABSOLUTE", None
    if normalized in ("", "."):
        return "PATH_EMPTY", None
    return None, normalized


def _validate_overrides(overrides_input):
    """Return ``(rules, errors)``; ``rules`` is ``None`` when any error occurred."""
    if not isinstance(overrides_input, list):
        return None, [{"reason": REASON["NOT_AN_ARRAY"]}]

    errors, rules = [], []
    for index, rule in enumerate(overrides_input):
        if not isinstance(rule, dict):
            errors.append({"reason": REASON["RULE_NOT_OBJECT"], "ruleIndex": index})
            continue

        raw_paths = rule.get("paths")
        if (not isinstance(raw_paths, list) or len(raw_paths) == 0
                or any(not isinstance(entry, str) for entry in raw_paths)):
            errors.append({"reason": REASON["PATHS_MALFORMED"], "ruleIndex": index})
            continue

        path_error, normalized_paths = None, []
        for raw_path in raw_paths:
            key, normalized = _validate_rule_path(raw_path)
            if key:
                path_error = {"reason": REASON[key], "ruleIndex": index, "path": raw_path}
                break
            normalized_paths.append(normalized)
        if path_error:
            errors.append(path_error)
            continue

        depth_value = rule.get("depth")
        if not isinstance(depth_value, str) or depth_value not in DEPTH_TIERS:
            error = {"reason": REASON["INVALID_DEPTH"], "ruleIndex": index}
            if "depth" in rule:
                error["value"] = depth_value
            errors.append(error)
            continue

        rules.append({"index": index, "paths": normalized_paths, "depth": depth_value})

    if errors:
        return None, errors
    return rules, []


def _finalize(resolved_depth, source, matched_rule, file_count, invalid_flag_depth=False, invalid_config_depth=False):
    downgraded = resolved_depth == "deep" and file_count > LARGE_SCOPE_THRESHOLD
    result = {
        "ok": True,
        "depth": "standard" if downgraded else resolved_depth,
        "resolvedDepth": resolved_depth,
        "source": source,
        "matchedRule": matched_rule,
        "downgraded": downgraded,
        "fileCount": file_count,
    }
    if invalid_flag_depth:
        result["invalidFlagDepth"] = True
    if invalid_config_depth:
        result["invalidConfigDepth"] = True
    return result


def resolve_code_review_depth(input):
    """Resolve the effective code-review depth.

    ``input`` keys: ``flagDepth``, ``configDepth``, ``overrides`` (any value,
    validated here), ``files`` (list of strings), ``repoRoot``. Overrides are
    always validated first, even when the flag would win. Returns either
    ``{"ok": False, "errors": [...]}`` or the ok result with ``depth``,
    ``resolvedDepth``, ``source``, ``matchedRule``, ``downgraded`` and ``fileCount``
    (plus ``invalidFlagDepth`` / ``invalidConfigDepth`` when set).
    """
    flag_depth = input.get("flagDepth")
    config_depth = input.get("configDepth")
    overrides = input["overrides"] if "overrides" in input else []
    files = input["files"]
    repo_root = input.get("repoRoot")

    rules, errors = _validate_overrides(overrides)
    if rules is None:
        return {"ok": False, "errors": errors}

    if isinstance(flag_depth, str) and flag_depth != "":
        if flag_depth in DEPTH_TIERS:
            return _finalize(flag_depth, "flag", None, len(files))
        return _finalize("standard", "flag", None, len(files), invalid_flag_depth=True)

    normalized_files = [normalize_rel_path(f, repo_root) for f in files]
    best, best_tier_index = None, -1
    for rule in rules:
        tier_index = DEPTH_TIERS.index(rule["depth"])
        matched_path = None
        for rule_path in rule["paths"]:
            if any(rule_matches_file(rule_path, file) for file in normalized_files):
                matched_path = rule_path
                break
        if matched_path is None:
            continue
        if best is None or tier_index > best_tier_index:
            best = {"index": rule["index"], "path": matched_path, "depth": rule["depth"]}
            best_tier_index = tier_index
    if best is not None:
        return _finalize(best["depth"], "rule", best, len(files))

    if isinstance(config_depth, str) and config_depth != "":
        if config_depth in DEPTH_TIERS:
            return _finalize(config_depth, "config", None, len(files))
        return _finalize("standard", "config", None, len(files), invalid_config_depth=True)

    return _finalize("standard", "default", None, len(files))
