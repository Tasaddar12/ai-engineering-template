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


class Failure(Exception):
    def __init__(self, code, message, status=1, **details):
        super().__init__(message)
        self.code, self.message, self.status, self.details = code, message, status, details


class Args:
    """Parse long options without shell interpolation; multi-value options stay lists."""
    FLAGS = {"raw", "json", "force", "confirm", "fix", "mvp", "mutating", "stdin",
             "commits-only", "uat-only", "require-verification", "discuss", "research",
             "validate", "full", "no-archive-phases", "milestone-bound", "tdd", "dry-run"}

    def __init__(self, values):
        self.pos, self.opts = [], {}
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
                active = None if key in self.FLAGS else key
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


def run(argv, cwd=None, check=True, timeout=None):
    result = subprocess.run([str(x) for x in argv], cwd=cwd, text=True,
                            encoding="utf-8", errors="replace", capture_output=True, timeout=timeout)
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


def write_json(path, value):
    write(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


@contextlib.contextmanager
def planning_lock(base=None, timeout=10):
    directory = (base or root()) / ".planning"
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / ".engineer.lock"
    end = time.monotonic() + timeout
    while True:
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.write(descriptor, json.dumps({"pid": os.getpid(), "created": now()}).encode())
            os.close(descriptor)
            break
        except FileExistsError:
            if time.monotonic() >= end:
                raise Failure("planning-locked", f"Planning records locked: {lock}")
            time.sleep(0.05)
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


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
