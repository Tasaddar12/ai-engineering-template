#!/usr/bin/env python3
"""Install the workflow into a new directory or an existing project (Python 3.11+)."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile


SOURCE = "https://github.com/Tasaddar12/ai-engineering-template.git"
AGENT_MARKER = "<!-- ai-engineering-template -->"
AGENT_END = "<!-- /ai-engineering-template -->"
ASSETS = ".ai/install-assets/"
PROJECT_RECORDS = {f".planning/{name}" for name in
                   ("PROJECT.md", "REQUIREMENTS.md", "ROADMAP.md", "STATE.md", "config.yaml")}
PLANNING_RESOURCES = {f".planning/{name}" for name in
                      ("README.md", "config.yaml", "phases/README.md", "codebase/README.md",
                       "specs/.gitkeep", "decisions/.gitkeep")}
GUIDES = {f"docs/{name}.md" for name in
          ("INSTALL", "AGENT-SKILLS", "ONBOARDING-PROMPTS", "PHASE-WORKFLOW",
           "TEMPLATE-GUIDE", "WORKFLOW-FEATURES")}
IGNORE_BLOCK = "\n# AI engineering workflow (local only)\n.worktrees/\n.ai-venv/\n__pycache__/\n*.pyc\n"


def run(*args, cwd=None, capture=False):
    return subprocess.run(args, cwd=cwd, check=True, text=True,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None).stdout


def safe_path(path):
    """Refuse links/junctions rather than writing through them."""
    for part in (path, *path.parents):
        try:
            metadata = part.lstat()
        except FileNotFoundError:
            continue
        reparse = (os.name == "nt"
                   and metadata.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
        if stat.S_ISLNK(metadata.st_mode) or reparse:
            raise ValueError(f"Refusing linked path: {part}")


def payload(source):
    selected = {}
    modes = {}
    entries = run("git", "ls-files", "--stage", "-z", cwd=source, capture=True)
    for entry in entries.split("\0"):
        if not entry:
            continue
        metadata, name = entry.split("\t", 1)
        modes[name] = metadata.split()[0]
        if name.startswith(ASSETS):
            continue
        if not (name.startswith((".ai/", ".agents/skills/"))
                or name in PLANNING_RESOURCES or name in GUIDES):
            continue
        if modes[name] not in ("100644", "100755"):
            raise ValueError(f"Unsupported template entry: {name}")
        selected[name] = (source / name).read_bytes()
    for destination, asset in [("AGENTS.md", "agent-entry.txt"), *[
            (f".planning/{name}.md", f"{name}.txt")
            for name in ("PROJECT", "REQUIREMENTS", "ROADMAP", "STATE")]]:
        origin = ASSETS + asset
        if modes.get(origin) not in ("100644", "100755"):
            raise ValueError(f"Missing or unsupported project install asset: {origin}")
        selected[destination] = (source / origin).read_bytes()
    selected["AGENTS.md"] = (AGENT_MARKER.encode() + b"\n" + selected["AGENTS.md"]
                             + b"\n" + AGENT_END.encode() + b"\n")
    for required in ("AGENTS.md", ".ai/runtime/phase.py", ".planning/config.yaml"):
        if required not in selected:
            raise ValueError(f"Source is not a workflow template: missing {required}")
    return selected


def require_utf8(content, path):
    try:
        content.decode("utf-8-sig")
        if b"\0" in content:
            raise ValueError("NUL bytes in text")
    except ValueError as error:
        raise ValueError(f"{path} must be UTF-8 text before appending; nothing was installed.") from error


def legacy_matches(legacy, name, content):
    digest = hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest()
    return legacy is not None and legacy["sha256"].get(name) == digest


def merge_agent(current, incoming, legacy):
    if any(variant in current for variant in (incoming, incoming.replace(b"\n", b"\r\n"))):
        return current
    if AGENT_MARKER.encode() in current:
        if legacy:
            old = (AGENT_MARKER + "\n" + legacy["agent_entry"]).encode()
            for variant in (old, old.replace(b"\n", b"\r\n")):
                if current.count(variant) == 1:
                    return current.replace(variant, incoming, 1)
        raise ValueError("Existing AGENTS.md workflow block differs. For an unmodified prior "
                         "install use --repair-template-context; otherwise reconcile it manually.")
    if legacy:
        old = legacy["agent_entry"].encode()
        for variant in (old, old.replace(b"\n", b"\r\n")):
            if current.count(variant) == 1:
                return current.replace(variant, incoming, 1)
    if any(signal in current for signal in (
            b"reusable engineering workflow template",
            b"for template maintenance only when the user requests them.")):
        raise ValueError("AGENTS.md still contains template-maintenance instructions. "
                         "Use --repair-template-context for an unchanged original entry; "
                         "reconcile edited instructions manually.")
    return current + b"\n\n" + incoming


def plan_install(source, target, repair=False):
    changes = []
    conflicts = []
    baseline = json.loads((source / ASSETS / "legacy-context.json").read_text(encoding="utf-8"))
    legacy = baseline if repair else None
    for name, incoming in payload(source).items():
        relative = Path(name)
        destination = target / relative
        safe_path(destination)
        for parent in destination.parents:
            if parent.exists() and not parent.is_dir():
                conflicts.append(str(parent))
                break
        if destination.exists() and not destination.is_file():
            conflicts.append(str(relative))
            continue
        if destination.exists():
            current = destination.read_bytes()
            if current.replace(b"\r\n", b"\n") == incoming.replace(b"\r\n", b"\n"):
                continue
            if legacy_matches(legacy, name, current):
                pass  # Explicit repair replaces only recognized prior installer bytes.
            elif name in PROJECT_RECORDS:
                continue  # Existing intent, execution history and config remain authoritative.
            elif relative == Path("AGENTS.md"):
                require_utf8(current, destination)
                if legacy_matches(baseline, name, current):
                    raise ValueError("AGENTS.md came from the original template installer. "
                                     "Use --repair-template-context to replace its template context.")
                incoming = merge_agent(current, incoming, legacy)
                if current == incoming:
                    continue
            else:
                conflicts.append(str(relative))
                continue
        changes.append((destination, incoming))
    if repair:
        for name in ("changes.log", "docs/WORKFLOW-DIRECTION.md"):
            destination = target / name
            safe_path(destination)
            if destination.is_file() and legacy_matches(legacy, name, destination.read_bytes()):
                changes.append((destination, None))
    ignore = target / ".gitignore"
    safe_path(ignore)
    if ignore.exists() and not ignore.is_file():
        conflicts.append(".gitignore")
    else:
        current = ignore.read_bytes() if ignore.exists() else b""
        require_utf8(current, ignore)
        if IGNORE_BLOCK.encode() not in current:
            changes.append((ignore, current + IGNORE_BLOCK.encode()))
    if conflicts:
        raise ValueError("Existing files conflict; nothing was installed. Reconcile these paths "
                         "in a worktree, then retry:\n  " + "\n  ".join(sorted(set(conflicts))))
    return changes


def install(args):
    target = Path(os.path.abspath(os.path.expanduser(args.target)))
    safe_path(target)
    # Canonicalize legitimate Windows 8.3 aliases only after checking for links.
    target = target.resolve()
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
        changes = plan_install(source, target, args.repair_template_context)
        print(f"Template revision: {revision}\nTarget: {target}", flush=True)
        print(f"{'Would change' if args.dry_run else 'Changing'} {len(changes)} workflow files.", flush=True)
        if args.dry_run:
            for path, content in changes:
                print(f"  {'remove' if content is None else 'write'} {path.relative_to(target)}")
            print(f"Git: {'preserve repository' if in_git else 'initialize repository'}; "
                  f"dependencies: {'skip' if args.skip_deps else 'create .ai-venv and install PyYAML'}")
            return
        target.mkdir(parents=True, exist_ok=True)
        for destination, content in changes:
            if content is None:
                destination.unlink()
                continue
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
    parser.add_argument("--repair-template-context", action="store_true",
                        help="Repair recognized files from the original installer; preserve customized project records")
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
