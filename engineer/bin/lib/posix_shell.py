"""Locate a real POSIX `bash` or `sh` as an absolute path.

On Windows a bare `bash` handed to `CreateProcess` resolves to `System32\bash.exe`, the WSL
launcher, before any PATH entry. It prints "Windows Subsystem for Linux has no installed
distributions" and runs nothing. This module returns a Git for Windows shell instead, and never
a WSL launcher. On POSIX it is `shutil.which`.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

_WSL_PARTS = ("system32", "syswow64", "sysnative", "windowsapps")
_GIT_SUBDIRS = {
    "bash": ("bin/bash.exe", "usr/bin/bash.exe"),
    "sh": ("usr/bin/sh.exe", "bin/sh.exe"),
}


def is_wsl_launcher(path) -> bool:
    """True for a Windows system-directory or app-alias shell: the WSL launcher, not a POSIX shell."""
    parts = {part.lower() for part in Path(str(path).replace("\\", "/")).parts}
    return bool(parts.intersection(_WSL_PARTS))


def git_roots(environ=None, which=shutil.which) -> list[Path]:
    """Git for Windows installation roots, derived from `git` itself first, then `ProgramFiles`."""
    environ = os.environ if environ is None else environ
    roots: list[Path] = []
    git = which("git")
    if git:
        try:
            exec_path = subprocess.run([git, "--exec-path"], capture_output=True, text=True, timeout=30).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            exec_path = ""
        if exec_path:
            # <root>/mingw64/libexec/git-core
            roots.append(Path(exec_path).parents[2] if len(Path(exec_path).parents) > 2 else Path(exec_path))
        roots.append(Path(git).resolve().parent.parent)  # <root>/cmd/git.exe
    for variable in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)", "LocalAppData"):
        base = environ.get(variable)
        if base:
            roots.append(Path(base) / "Git")
            roots.append(Path(base) / "Programs" / "Git")
    return roots


def windows_candidates(name: str, roots, path_matches=()) -> list[Path]:
    """Ordered candidate files for `name`: Git for Windows first, then PATH matches."""
    found = [Path(root) / relative for root in roots for relative in _GIT_SUBDIRS.get(name, (f"usr/bin/{name}.exe",))]
    return found + [Path(match) for match in path_matches]


def find_posix_shell(name: str = "bash", candidates=None, windows: bool | None = None) -> str | None:
    """Absolute path of a real POSIX shell named `name`, or None.

    `candidates` (an ordered list of paths) and `windows` exist so the choice can be exercised
    without a particular host; by default they come from the machine.
    """
    windows = os.name == "nt" if windows is None else windows
    if not windows:
        if candidates is None:
            found = shutil.which(name)
            return str(Path(found).resolve()) if found else None
        return next((str(path) for path in candidates if Path(path).is_file()), None)
    if candidates is None:
        path_matches = []
        for directory in os.environ.get("PATH", "").split(os.pathsep):
            if directory and os.path.isabs(directory):
                match = shutil.which(name, path=directory)
                if match:
                    path_matches.append(match)
        candidates = windows_candidates(name, git_roots(), path_matches)
    for path in candidates:
        if Path(path).is_file() and not is_wsl_launcher(path):
            return str(path)
    return None
