"""Review missing required configuration without resetting adopting-project values."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import sys
import types

REQUIRED = {"workflow.isolation": "auto", "handoff.enabled": True,
            "handoff.context_percent": 60, "handoff.context_tokens": 250000,
            "verification.commands": []}
ENUMS = {"workflow.isolation": {"auto", "harness-worktree", "orchestrator-worktree"},
         "workflow.discuss_mode": {"discuss", "assumptions"},
         "workflow.code_review_depth": {"standard", "deep", "quick"},
         "workflow.human_verify_mode": {"end-of-phase", "mid-flight"},
         "delivery.merge_method": {"merge", "squash", "rebase"}}


def parser(source):
    """Use the copied runtime's standard-library YAML parser, never legacy .ai."""
    package = "engineer_review_yaml_" + str(abs(hash(str(Path(source).resolve()))))
    if package not in sys.modules:
        module = types.ModuleType(package)
        module.__path__ = [str(Path(source) / "engineer/bin/lib")]
        sys.modules[package] = module
    name = package + ".text"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, Path(source) / "engineer/bin/lib/text.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def flatten(value, prefix=""):
    result = {}
    for key, child in value.items():
        name = prefix + str(key)
        if isinstance(child, dict) and child:
            result.update(flatten(child, name + "."))
        else:
            result[name] = child
    return result


def insert_missing(text, dotted, value, yaml):
    """Insert one simple required key while retaining all existing text."""
    parts = dotted.split(".")
    lines = text.splitlines(keepends=True)
    newline = "\r\n" if "\r\n" in text else "\n"
    start, end = 0, len(lines)
    for depth, key in enumerate(parts):
        indent = depth * 2
        found = next((i for i in range(start, end) if re.match(r"^ {" + str(indent) + "}" + re.escape(key) + r":(?:\s|$)", lines[i])), None)
        if found is None:
            tail = []
            for level, remaining in enumerate(parts[depth:], depth):
                tail.append(" " * (level * 2) + remaining + ":" + (" " + json.dumps(value) if level == len(parts) - 1 else "") + newline)
            if end and not lines[end - 1].endswith(("\n", "\r")):
                lines[end - 1] += newline
            lines[end:end] = tail
            break
        if depth == len(parts) - 1:
            break
        # Extend a supported one-line flow parent in place. Preserve the rest of
        # the document and any trailing comment instead of appending a duplicate
        # key or classifying valid user formatting as invalid configuration.
        match = re.match(r"^(\s*" + re.escape(key) + r":\s*)(\{.*\})([^\r\n]*)(\r?\n)?$", lines[found])
        if match:
            mapping = yaml.yaml_load(key + ": " + match[2])[key]
            cursor = mapping
            for part in parts[depth + 1:-1]:
                cursor = cursor.setdefault(part, {})
            cursor[parts[-1]] = deepcopy(value)
            lines[found] = match[1] + json.dumps(mapping, ensure_ascii=False) + match[3] + (match[4] or "")
            return "".join(lines)
        # An empty inline map has no user fields to disturb.
        if re.match(r"^\s*" + re.escape(key) + r":\s*\{\}\s*(?:#.*)?(?:\r?\n)?$", lines[found]):
            lines[found] = re.sub(r"\{\}", "", lines[found], count=1)
        start = found + 1
        end = next((i for i in range(start, end) if lines[i].strip() and not lines[i].lstrip().startswith("#") and len(lines[i]) - len(lines[i].lstrip()) <= indent), end)
    return "".join(lines)


def review(source, before, defaults):
    yaml = parser(source)
    text = before.decode("utf-8-sig") if before is not None else ""
    try:
        current = yaml.yaml_load(text)
        template = yaml.yaml_load(defaults.decode("utf-8-sig"))
        if not isinstance(current, dict) or not isinstance(template, dict):
            raise ValueError("configuration must be a mapping")
        missing, optional, errors = {}, {}, []
        flat_defaults = flatten(template)
        flat_defaults["workflow.isolation"] = "auto"
        for name, default in {**flat_defaults, **REQUIRED}.items():
            cursor = current
            exists = True
            for part in name.split("."):
                if not isinstance(cursor, dict):
                    errors.append(name + " parent must be a mapping")
                    exists = False
                    break
                if part not in cursor:
                    exists = False
                    break
                cursor = cursor[part]
            if exists:
                valid_type = (cursor is None or isinstance(cursor, str)) if default is None else type(cursor) is type(default)
                if not valid_type:
                    errors.append(name + " has invalid type")
                if name in ENUMS and (not isinstance(cursor, str) or cursor not in ENUMS[name]):
                    errors.append(name + " has invalid value")
                if name.startswith("handoff.context_") and type(cursor) is int and cursor <= 0:
                    errors.append(name + " must be positive")
            elif name in REQUIRED:
                missing[name] = deepcopy(REQUIRED[name])
            else:
                optional[name] = deepcopy(default)
        # Validate established enum fields even if not present in the new template.
        for name, values in ENUMS.items():
            cursor = current
            for part in name.split("."):
                cursor = cursor.get(part) if isinstance(cursor, dict) else None
            if cursor is not None and (not isinstance(cursor, str) or cursor not in values):
                errors.append(name + " has invalid value")
        if errors:
            return before, missing, optional, "; ".join(sorted(set(errors)))
        if text.lstrip().startswith("{") and missing:
            merged = deepcopy(current)
            for name, value in missing.items():
                cursor = merged
                parts = name.split(".")
                for part in parts[:-1]:
                    cursor = cursor.setdefault(part, {})
                cursor[parts[-1]] = deepcopy(value)
            # JSON itself is valid YAML; retain all explicitly configured values.
            text = json.dumps(merged, indent=2, ensure_ascii=False) + "\n"
        else:
            for name, value in missing.items():
                text = insert_missing(text, name, value, yaml)
        result = (b"\xef\xbb\xbf" if before and before.startswith(b"\xef\xbb\xbf") else b"") + text.encode()
        parsed = yaml.yaml_load(text)
        # Confirm every required insertion survived parsing before proposing it.
        for name, value in missing.items():
            cursor = parsed
            for part in name.split("."):
                cursor = cursor.get(part) if isinstance(cursor, dict) else None
            if cursor != value:
                raise ValueError("required key cannot be inserted safely: " + name)
        return result, missing, optional, None
    except Exception as exc:
        return before, {}, {}, "invalid project configuration: " + str(exc)
