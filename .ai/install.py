#!/usr/bin/env python3
"""Install the workflow into a new directory or an existing project (Python 3.11+)."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


SOURCE = "https://github.com/Tasaddar12/ai-engineering-template.git"
AGENT_MARKER = "<!-- ai-engineering-template -->"
IGNORE_BLOCK = "\n# AI engineering workflow (local only)\n.worktrees/\n.ai-venv/\n__pycache__/\n*.pyc\n"


def run(*args, cwd=None, capture=False):
    return subprocess.run(args, cwd=cwd, check=True, text=True,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None).stdout


def safe_path(path):
    """Refuse links/junctions rather than writing through them."""
    for part in (path, *path.parents):
        if part.is_symlink() or getattr(part, "is_junction", lambda: False)():
            raise ValueError(f"Refusing linked path: {part}")
    if path.resolve() != path:
        raise ValueError(f"Path resolves elsewhere: {path}")


def payload(source):
    selected = []
    entries = run("git", "ls-files", "--stage", "-z", cwd=source, capture=True)
    for entry in entries.split("\0"):
        if not entry:
            continue
        metadata, name = entry.split("\t", 1)
        if not (name.startswith((".ai/", ".agents/skills/", ".planning/", "docs/"))
                or name in ("AGENTS.md", "changes.log")):
            continue
        if name.startswith(".planning/maintenance/"):
            continue
        if metadata.split()[0] not in ("100644", "100755"):
            raise ValueError(f"Unsupported template entry: {name}")
        selected.append(Path(name))
    for required in ("AGENTS.md", ".ai/runtime/phase.py", ".planning/config.yaml"):
        if Path(required) not in selected:
            raise ValueError(f"Source is not a workflow template: missing {required}")
    return selected


def plan_install(source, target):
    changes = []
    conflicts = []
    for relative in payload(source):
        destination = target / relative
        safe_path(destination)
        for parent in destination.parents:
            if parent.exists() and not parent.is_dir():
                conflicts.append(str(parent))
                break
        if destination.exists() and not destination.is_file():
            conflicts.append(str(relative))
            continue
        incoming = (source / relative).read_bytes()
        if destination.exists():
            current = destination.read_bytes()
            if current == incoming:
                continue
            if relative == Path("AGENTS.md"):
                if AGENT_MARKER.encode() in current:
                    continue
                incoming = current + b"\n\n" + AGENT_MARKER.encode() + b"\n" + incoming
            else:
                conflicts.append(str(relative))
                continue
        changes.append((destination, incoming))
    ignore = target / ".gitignore"
    safe_path(ignore)
    if ignore.exists() and not ignore.is_file():
        conflicts.append(".gitignore")
    else:
        current = ignore.read_bytes() if ignore.exists() else b""
        if IGNORE_BLOCK.encode() not in current:
            changes.append((ignore, current + IGNORE_BLOCK.encode()))
    if conflicts:
        raise ValueError("Existing files conflict; nothing was installed. Reconcile these paths "
                         "in a worktree, then retry:\n  " + "\n  ".join(sorted(set(conflicts))))
    return changes


def install(args):
    target = Path(os.path.abspath(os.path.expanduser(args.target)))
    safe_path(target)
    if target.exists() and not target.is_dir():
        raise ValueError(f"Target is not a directory: {target}")
    # A project subdirectory is almost always an accidental installation location.
    ancestor = target
    while not ancestor.exists():
        ancestor = ancestor.parent
    probe = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=ancestor,
                           text=True, capture_output=True)
    in_git = probe.returncode == 0
    if in_git and Path(probe.stdout.strip()).resolve() != target:
        raise ValueError("Target is inside another repository. Choose its root or an assigned worktree.")
    if not args.skip_deps:
        environment = target / ".ai-venv"
        safe_path(environment)
        if environment.exists():
            raise ValueError(".ai-venv already exists; preserve it and rerun with --skip-deps. "
                             "See docs/INSTALL.md for dependency repair.")
    with tempfile.TemporaryDirectory(prefix="ai-template-") as temporary:
        source = Path(temporary)
        run("git", "init", "--quiet", str(source))
        run("git", "fetch", "--quiet", "--depth=1", "--", args.source, args.ref, cwd=source)
        run("git", "checkout", "--quiet", "--detach", "FETCH_HEAD", cwd=source)
        revision = run("git", "rev-parse", "HEAD", cwd=source, capture=True).strip()
        changes = plan_install(source, target)
        print(f"Template revision: {revision}\nTarget: {target}", flush=True)
        print(f"{'Would write' if args.dry_run else 'Writing'} {len(changes)} workflow files.", flush=True)
        if args.dry_run:
            for path, _ in changes:
                print(f"  {path.relative_to(target)}")
            print(f"Git: {'preserve repository' if in_git else 'initialize repository'}; "
                  f"dependencies: {'skip' if args.skip_deps else 'create .ai-venv and install PyYAML'}")
            return
        target.mkdir(parents=True, exist_ok=True)
        for destination, content in changes:
            destination.parent.mkdir(parents=True, exist_ok=True)
            existed = destination.exists()
            destination.write_bytes(content)
            original = source / destination.relative_to(target)
            if not existed and original.is_file():
                shutil.copymode(original, destination)
        if not in_git:
            run("git", "init", "--quiet", str(target))
        if not args.skip_deps:
            run(sys.executable, "-m", "venv", str(environment))
            interpreter = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            run(str(interpreter), "-m", "pip", "install", "-r",
                str(target / ".ai/runtime/requirements.txt"))
            run(str(interpreter), str(target / ".ai/runtime/phase.py"), "status", cwd=target)
        print("Installed. No project files were committed and no remote was changed.\n"
              "If installed into a primary checkout, a human must review and commit the "
              "bootstrap before an agent creates a worktree (see docs/INSTALL.md).\n"
              "Next: follow .ai/commands/onboard.md to fill project intent, configure actual "
              "checks and worker commands, and commit setup. See docs/INSTALL.md.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default=".", help="Project root or assigned worktree (default: current directory)")
    parser.add_argument("--source", default=SOURCE, help="Template Git URL or local repository")
    parser.add_argument("--ref", default="main", help="Template branch, tag or commit (default: main)")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and check without changing the target")
    parser.add_argument("--skip-deps", action="store_true", help="Skip virtual environment and dependency setup")
    args = parser.parse_args()
    try:
        if sys.version_info < (3, 11):
            raise ValueError("Python 3.11 or newer is required.")
        if not shutil.which("git"):
            raise ValueError("Git is required on PATH.")
        install(args)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Setup failed: {error}\nIf setup had already started, files are retained for "
              "inspection; fix the error and retry with --skip-deps when .ai-venv exists.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
