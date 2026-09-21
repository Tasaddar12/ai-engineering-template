"""Project configuration: .planning/config.yaml with dotted access."""
import copy

import yaml

from .paths import read_text, write_text
from .results import VerbError

DEFAULTS = {
    "commit_docs": True,
    "response_language": None,
    "context_window": 200000,
    "workflow": {
        "text_mode": False,
        "auto_advance": False,
        "discuss_mode": "discuss",
        # Which isolation model to use, never whether to isolate. Worktree
        # isolation is a requirement of this project: there is no value here
        # that means "run unisolated", and no key that turns it off.
        "isolation": "auto",
    },
    "worktree": {
        "root": ".worktrees",
        "base_ref": "fork-point",
    },
    "agents": {},
    "verification": {"commands": []},
}

TRUE = {"true", "yes", "on", "1"}
FALSE = {"false", "no", "off", "0"}


def load(workspace):
    """Configured values merged over defaults."""
    if not workspace.config.is_file():
        return copy.deepcopy(DEFAULTS)
    try:
        data = yaml.safe_load(read_text(workspace.config, "")) or {}
    except yaml.YAMLError as exc:
        raise VerbError(f"invalid config.yaml: {exc}", "bad-config")
    if not isinstance(data, dict):
        raise VerbError("config.yaml must be a mapping", "bad-config")
    return merge(copy.deepcopy(DEFAULTS), data)


def merge(base, overlay):
    for key, value in (overlay or {}).items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge(base[key], value)
        else:
            base[key] = value
    return base


def get(workspace, dotted, default=None):
    node = load(workspace)
    for part in str(dotted).split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def set_value(workspace, dotted, value):
    """Write one dotted key, preserving everything else in the file."""
    raw = {}
    if workspace.config.is_file():
        raw = yaml.safe_load(read_text(workspace.config, "")) or {}
    parts = str(dotted).split(".")
    node = raw
    for part in parts[:-1]:
        if not isinstance(node.get(part), dict):
            node[part] = {}
        node = node[part]
    node[parts[-1]] = coerce(value)
    write_text(workspace.config, yaml.safe_dump(raw, sort_keys=False, allow_unicode=True,
                                                default_flow_style=False))
    return node[parts[-1]]


def coerce(value):
    """Interpret a shell-supplied string as bool, int or string."""
    if not isinstance(value, str):
        return value
    lowered = value.strip().lower()
    if lowered in TRUE:
        return True
    if lowered in FALSE:
        return False
    if lowered in {"null", "none", ""}:
        return None
    try:
        return int(value)
    except ValueError:
        return value
