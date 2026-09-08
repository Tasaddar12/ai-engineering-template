"""Project configuration is local, editable YAML."""

from pathlib import Path
from typing import Any

from .errors import FrameworkError
from .io import read_yaml, safe_path


def load_config(root: Path, name: str) -> dict[str, Any]:
    if name not in {"framework", "constraints", "models", "project/commands"}:
        raise FrameworkError(f"Unknown configuration: {name}")
    return read_yaml(safe_path(root, f".ai/{name}.yaml"))
