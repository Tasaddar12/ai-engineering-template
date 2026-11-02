"""Reentrant kernel-backed locks, released by the OS after process failure."""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time

_local = threading.local()


def lock_path(base, name="planning"):
    base = Path(base).resolve()
    result = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=base,
                            capture_output=True, text=True, timeout=30, check=False)
    identity = hashlib.sha256(str(base).encode()).hexdigest()
    directory = Path(result.stdout.strip())/"engineer/locks" if result.returncode == 0 else Path(tempfile.gettempdir())/"engineer-locks"
    return directory/(identity+"-"+name+".lock")


@contextmanager
def acquire(path, timeout=10):
    path = Path(path)
    held = getattr(_local, "held", None)
    if held is None:
        held = _local.held = set()
    key = str(path.resolve())
    if key in held:
        yield
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise OSError("Refusing linked lock file: "+str(path))
    with path.open("a+b") as handle:
        if handle.seek(0, 2) == 0:
            handle.write(b"0")
            handle.flush()
        deadline = time.monotonic()+timeout
        while True:
            handle.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("Lock remains owned: "+str(path))
                time.sleep(0.05)
        held.add(key)
        try:
            yield
        finally:
            held.remove(key)
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)
