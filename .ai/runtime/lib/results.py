"""Pure-result contract shared by every runtime verb.

Handlers return data, never print and never raise for expected conditions.
`RuntimeError_` marks an expected failure; anything else is a defect and
surfaces with a traceback so it is not mistaken for a handled outcome.
"""
import json
import sys


class VerbError(Exception):
    """An expected failure. Carries a machine-readable code."""

    def __init__(self, message, code="error"):
        super().__init__(message)
        self.code = code


def require(condition, message, code="error"):
    if not condition:
        raise VerbError(message, code)


def use_utf8(stream):
    """Windows consoles default to cp1252; results carry box-drawing characters."""
    if hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass
    return stream


def emit(payload, raw=False, stream=None):
    """Write a verb result. `raw` prints a scalar for shell capture."""
    stream = use_utf8(stream or sys.stdout)
    if raw:
        if payload is None:
            text = ""
        elif isinstance(payload, bool):
            text = "true" if payload else "false"
        elif isinstance(payload, (dict, list)):
            text = json.dumps(payload, ensure_ascii=False)
        else:
            text = str(payload)
        stream.write(text + "\n")
        return
    stream.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def failure(message, code="error"):
    return {"ok": False, "error": message, "code": code}


def success(payload=None):
    result = {"ok": True}
    if payload:
        result.update(payload)
    return result
