"""Shared command, repository, locking, and atomic I/O primitives."""
from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import sys


class Failure(Exception):
    def __init__(self, code, message, status=1, **details):
        super().__init__(message)
        self.code, self.message, self.status, self.details = code, message, status, details


class Args:
    """Parse long options without shell interpolation; multi-value options stay lists."""
    FLAGS = {"raw", "json", "force", "confirm", "fix", "mvp", "mutating", "stdin",
             "commits-only", "uat-only", "require-verification", "discuss", "research",
             "validate", "full", "no-archive-phases", "milestone-bound", "tdd", "dry-run",
             "publish", "execution-authorized", "authorize-execution", "track-issues", "list", "apply", "repair", "backfill",
             "all", "auto", "lines", "first", "require-nonempty", "preview", "no-write"}

    def __init__(self, values, flags=()):
        self.pos, self.opts = [], {}
        boolean_flags = self.FLAGS | set(flags)
        active = None
        for token in values:
            if token == "--":
                active = "_body"
                self.opts[active] = []
            elif active == "_body":
                self.opts[active].append(token)
            elif token.startswith("--"):
                key, sep, value = token[2:].partition("=")
                self.opts[key] = [value] if sep else []
                active = None if key in boolean_flags else key
            elif active:
                self.opts[active].append(token)
            else:
                self.pos.append(token)

    def get(self, key, default=None):
        values = self.opts.get(key)
        return default if values is None else (values[0] if values else True)

    def all(self, key):
        return self.opts.get(key, [])

    def has(self, key):
        return key in self.opts

    def arg(self, n=0, default=None):
        return self.pos[n] if len(self.pos) > n else default

    def need(self, n=0):
        value = self.arg(n)
        if value is None:
            raise Failure("missing-argument", f"Missing positional argument {n + 1}", 2)
        return value

    def json(self, key, default=None):
        value = self.get(key)
        if value is None:
            return default
        try:
            return json.loads(value)
        except (TypeError, ValueError) as exc:
            raise Failure("invalid-json", f"--{key}: {exc}", 2) from exc


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "untitled"


def run(argv, cwd=None, check=True, timeout=None, env=None, stdin=None):
    try:
        result = subprocess.run([str(x) for x in argv], cwd=cwd, text=True, env=env, stdin=stdin,
                                encoding="utf-8", errors="replace", capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise Failure("command-timeout", "Command exceeded its time budget", 124,
                      command=list(map(str, argv)), timeout=timeout) from exc
    if check and result.returncode:
        raise Failure("command-failed", result.stderr.strip() or result.stdout.strip(),
                      command=list(map(str, argv)), exit_code=result.returncode)
    return result


def root():
    override = os.environ.get("ENGINEER_ROOT")
    if override:
        return Path(override).resolve()
    result = run(["git", "rev-parse", "--show-toplevel"], check=False)
    return Path(result.stdout.strip()).resolve() if result.returncode == 0 else Path.cwd().resolve()


def safe_path(value, base=None):
    base = (base or root()).resolve()
    path = Path(value)
    path = (base / path).resolve() if not path.is_absolute() else path.resolve()
    if not path.is_relative_to(base):
        raise Failure("path-outside-repository", f"Refusing path outside {base}: {path}")
    return path


def read(path, default=""):
    path = Path(path)
    return path.read_text(encoding="utf-8-sig") if path.exists() else default


def write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def load_json(path, default=None):
    return json.loads(read(path)) if Path(path).exists() else default


def input_json(path=None, max_bytes=10*1024*1024):
    """Read an explicitly named regular JSON input, including workflow temp files."""
    try:
        if path is None:
            content = sys.stdin.read(max_bytes+1)
            if len(content.encode("utf-8")) > max_bytes:
                raise Failure("json-input-too-large", "JSON input exceeds the configured read bound", 2)
        else:
            selected = Path(str(path)).expanduser()
            if selected.is_symlink() or not selected.is_file():
                raise Failure("json-input-file", "Expected an explicitly named regular JSON file: "+str(selected), 2)
            with selected.open("rb") as stream:
                raw_content = stream.read(max_bytes+1)
            if len(raw_content) > max_bytes:
                raise Failure("json-input-too-large", str(selected), 2)
            content = raw_content.decode("utf-8-sig")
        return json.loads(content)
    except (OSError, UnicodeError, ValueError) as exc:
        raise Failure("invalid-json-input", str(exc), 2) from exc


def write_json(path, value):
    write(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


@contextlib.contextmanager
def planning_lock(base=None, timeout=10):
    from .locking import acquire, lock_path
    try:
        with acquire(lock_path(base or root()), timeout):
            yield
    except TimeoutError as exc:
        raise Failure("planning-locked", str(exc)) from exc


def digest(paths, base=None):
    base = base or root()
    result = hashlib.sha256()
    for path in sorted(set(Path(p).resolve() for p in paths), key=str):
        name = str(path.relative_to(base)) if path.is_relative_to(base) else str(path)
        result.update(name.replace("\\", "/").encode())
        result.update(b"\0")
        result.update(path.read_bytes() if path.is_file() else b"<missing>")
        result.update(b"\0")
    return result.hexdigest()


def pick(value, dotted):
    for key in dotted.split("."):
        try:
            value = value[int(key)] if isinstance(value, list) else value[key]
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            raise Failure("pick-missing", f"Missing result field: {dotted}") from exc
    return value


def raw(value):
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
