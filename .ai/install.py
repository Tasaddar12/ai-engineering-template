#!/usr/bin/env python3
"""Install the workflow into a new directory or an existing project (Python 3.11+)."""

import argparse
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tarfile
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
LEGACY_REVISION = "f4855eb66023495c75a9c9d5c9190565d3af2315"
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


def payload(source, host="codex", hooks=True):
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
                or name in PLANNING_RESOURCES):
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
    selected.update(host_payload(source, selected, host, hooks))
    return selected


def host_payload(source, shared, host, hooks):
    """Project-local host entry points; never copy personal host state."""
    if host not in ("codex", "claude", "both"):
        raise ValueError(f"Unknown host: {host}")
    selected = {}
    if host in ("claude", "both"):
        selected["CLAUDE.md"] = (AGENT_MARKER + "\n# Shared engineering workflow\n\n"
                                "@AGENTS.md\n\n" + AGENT_END + "\n").encode()
        for name, content in shared.items():
            if not (name.startswith(".agents/skills/") and name.endswith("/SKILL.md")):
                continue
            text = content.decode("utf-8-sig").replace("\r\n", "\n")
            if not text.startswith("---\n") or "\n---\n" not in text[4:]:
                raise ValueError(f"Missing skill metadata: {name}")
            header = text.split("\n---\n", 1)[0] + "\n---\n"
            destination = name.replace(".agents/skills/", ".claude/skills/", 1)
            # Both native discovery trees are three levels below the repository.
            selected[destination] = (header + "\nRead and follow the complete canonical skill at "
                                      f"[SKILL.md](../../../{name}) before doing this work. "
                                      "Resolve that skill's references relative to its canonical "
                                      "location. Apply repository instructions and your assigned "
                                      "role and ownership.\n").encode()
        if host == "claude":
            selected[".planning/config.yaml"] = (source / ASSETS / "claude-config.txt").read_bytes()
    if hooks:
        for selected_host in (("codex", "claude") if host == "both" else (host,)):
            name = ".codex/hooks.json" if selected_host == "codex" else ".claude/settings.json"
            selected[name] = json_bytes(hook_settings(selected_host))
    return selected


def hook_settings(host):
    # The command locates the active Git checkout, including launches in subfolders.
    # Payload cwd is separately used by the adapter to assess the tool's target.
    launcher = ("import runpy,subprocess; "
                "root=subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).rstrip(chr(10)+chr(13)); "
                "runpy.run_path(root+'/.ai/hooks/host-adapter.py',run_name='__main__')")
    unix = f'python3 -c "{launcher}"'
    windows = f'python -c "{launcher}"'
    if host == "claude":
        # Claude's default command shell is Bash, including Git Bash on Windows.
        # Actually probe Python: a Windows Store alias can exist but be unusable.
        command = ('if python3 -c "import sys; sys.exit(sys.version_info < (3, 11))" '
                   f'>/dev/null 2>&1; then {unix}; else {windows}; fi')
    else:
        command = unix
    handler = {"type": "command", "command": command, "timeout": 10}
    if host == "codex":
        handler["commandWindows"] = windows
    return {"hooks": {event: [{"matcher": "^(Bash|Write|Edit|NotebookEdit|apply_patch)$",
                                "hooks": [dict(handler)]}]
                      for event in ("PreToolUse", "PostToolUse")}}


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def invalid_json_constant(value):
    raise ValueError(f"Non-JSON numeric constant: {value}")


def merge_hooks(current, incoming, path):
    """Append managed groups, retaining user settings and refusing ambiguous edits."""
    try:
        settings = json.loads(current.decode("utf-8-sig"), object_pairs_hook=unique_json_object,
                              parse_constant=invalid_json_constant)
        if not isinstance(settings, dict):
            raise ValueError("settings must be a JSON object")
        events = settings.setdefault("hooks", {})
        if not isinstance(events, dict):
            raise ValueError("hooks must be an object")
        for event, groups in events.items():
            if not isinstance(groups, list):
                raise ValueError(f"hooks.{event} must be an array")
            for group in groups:
                if (not isinstance(group, dict) or not isinstance(group.get("hooks"), list)
                        or ("matcher" in group and not isinstance(group["matcher"], str))
                        or any(not isinstance(item, dict) or not isinstance(item.get("type"), str)
                               or (item["type"] == "command" and
                                   (not isinstance(item.get("command"), str) or not item["command"].strip()))
                               for item in group["hooks"])):
                    raise ValueError(f"invalid matcher/handler group for {event}")
        additions = json.loads(incoming)["hooks"]
        changed = False
        for event, groups in additions.items():
            existing = events.setdefault(event, [])
            for group in groups:
                if group in existing:
                    continue
                if any(".ai/hooks/host-adapter.py" in json.dumps(item) for item in existing):
                    raise ValueError(f"managed {event} registration differs; reconcile it manually")
                existing.append(group)
                changed = True
        return json_bytes(settings) if changed else current
    except (ValueError, UnicodeError) as error:
        raise ValueError(f"Invalid or conflicting host settings {path}: {error}; nothing was installed.") from error


def require_utf8(content, path):
    try:
        content.decode("utf-8-sig")
        if b"\0" in content:
            raise ValueError("NUL bytes in text")
    except ValueError as error:
        raise ValueError(f"{path} must be UTF-8 text before appending; nothing was installed.") from error


def load_legacy(source, remote):
    """Read the original release from Git; keep no duplicate manifest or history file."""
    run("git", "fetch", "--quiet", "--depth=1", "--", remote, LEGACY_REVISION, cwd=source)
    archive = subprocess.run(["git", "archive", LEGACY_REVISION], cwd=source,
                             check=True, capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as snapshot:
        return {member.name: snapshot.extractfile(member).read().replace(b"\r\n", b"\n")
                for member in snapshot.getmembers() if member.isfile()}


def legacy_matches(legacy, name, content):
    return legacy is not None and legacy.get(name) == content.replace(b"\r\n", b"\n")


def merge_agent(current, incoming, legacy, name="AGENTS.md"):
    if any(variant in current for variant in (incoming, incoming.replace(b"\n", b"\r\n"))):
        return current
    if AGENT_MARKER.encode() in current:
        if legacy:
            old = (AGENT_MARKER + "\n").encode() + legacy["AGENTS.md"]
            for variant in (old, old.replace(b"\n", b"\r\n")):
                if current.count(variant) == 1:
                    return current.replace(variant, incoming, 1)
        raise ValueError(f"Existing {name} workflow block differs. For an unmodified prior "
                         "install use --repair-template-context; otherwise reconcile it manually.")
    if legacy:
        old = legacy["AGENTS.md"]
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


def plan_install(source, target, legacy=None, host="codex", hooks=True):
    changes = []
    conflicts = []
    for name, incoming in payload(source, host, hooks).items():
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
            elif name in ("AGENTS.md", "CLAUDE.md"):
                require_utf8(current, destination)
                incoming = merge_agent(current, incoming, legacy if name == "AGENTS.md" else None, name)
                if current == incoming:
                    continue
            elif name in (".codex/hooks.json", ".claude/settings.json"):
                incoming = merge_hooks(current, incoming, destination)
                if current == incoming:
                    continue
            else:
                conflicts.append(str(relative))
                continue
        changes.append((destination, incoming))
    if legacy:
        for name in legacy:
            if not (name.startswith("docs/") or ("/" not in name and name.endswith(".log"))):
                continue
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
        if IGNORE_BLOCK.encode() not in current.replace(b"\r\n", b"\n"):
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
                             "See .ai/commands/install.md for dependency repair.")
    with tempfile.TemporaryDirectory(prefix="ai-template-") as temporary:
        source = Path(temporary)
        run("git", "init", "--quiet", str(source))
        run("git", "fetch", "--quiet", "--depth=1", "--", args.source, args.ref, cwd=source)
        run("git", "checkout", "--quiet", "--detach", "FETCH_HEAD", cwd=source)
        revision = run("git", "rev-parse", "HEAD", cwd=source, capture=True).strip()
        legacy = load_legacy(source, args.source) if args.repair_template_context else None
        changes = plan_install(source, target, legacy, args.host, not args.no_hooks)
        print(f"Template revision: {revision}\nTarget: {target}\nHost: {args.host}; "
              f"hook registration: {'skip' if args.no_hooks else 'advisory'}", flush=True)
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
              "bootstrap before an agent creates a worktree (see .ai/commands/install.md).\n"
              "Next: follow .ai/commands/onboard.md to fill project intent, configure actual "
              "checks and worker commands, and commit setup. See .ai/commands/onboard.md.")
        if not args.no_hooks:
            print("Review project hook registrations in /hooks in each selected host. "
                  "Codex requires project and hook trust before running them; existing "
                  "host policies remain in effect. No personal configuration was changed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default=".", help="Project root or assigned worktree (default: current directory)")
    parser.add_argument("--source", default=SOURCE, help="Template Git URL or local repository")
    parser.add_argument("--ref", default="main", help="Template branch, tag or commit (default: main)")
    parser.add_argument("--host", choices=("codex", "claude", "both"), default="codex",
                        help="Project host integration (default: codex); both uses Codex for new worker routes")
    parser.add_argument("--no-hooks", action="store_true",
                        help="Skip adding hook registrations; preserve existing hooks")
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
