#!/usr/bin/env python3
"""Install the workflow into a new directory or an existing project (Python 3.11+)."""

import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
import os
import posixpath
import re
import runpy
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
from types import SimpleNamespace
import uuid


SOURCE = "https://github.com/Tasaddar12/ai-engineering-template.git"
AGENT_MARKER = "<!-- ai-engineering-template -->"
AGENT_END = "<!-- /ai-engineering-template -->"
ASSETS = ".ai/install-assets/"
PROJECT_RECORDS = {f".planning/{name}" for name in
                   ("PROJECT.md", "REQUIREMENTS.md", "ROADMAP.md", "STATE.md", "config.yaml")}
PLANNING_RESOURCES = {f".planning/{name}" for name in
                      ("README.md", "config.yaml", "phases/README.md", "codebase/README.md",
                       "specs/.gitkeep", "decisions/.gitkeep", "todos/README.md",
                       "todos/pending/.gitkeep", "todos/completed/.gitkeep",
                       "milestones/.gitkeep")}
IGNORE_HEADER = "# AI engineering workflow (local only)"
#: `.planning/handoffs/` holds handoff records: local to one checkout, deleted
#: once consumed, and never evidence, so they must never reach a commit.
IGNORE_ENTRIES = (".ai-venv/", ".workflow-backups/", ".planning/handoffs/", "__pycache__/",
                  "*.pyc")
IGNORE_BLOCK = "\n" + IGNORE_HEADER + "\n" + "".join(entry + "\n" for entry in IGNORE_ENTRIES)


def ignore_addition(current, namespace):
    """The ignore rules `current` still lacks, as bytes to append -- empty when none.

    Compared rule by rule, not as one block. A project installed before a rule
    was added carries the older block, and a whole-block test would append a
    second copy of every rule it already has just to add the new one.
    """
    entries = [entry.replace(".ai-venv", namespace + "-venv") for entry in IGNORE_ENTRIES]
    present = {line.strip() for line in
               current.replace(b"\r\n", b"\n").decode("utf-8").split("\n")}
    missing = [entry for entry in entries if entry not in present]
    if not missing:
        return b""
    header = [] if IGNORE_HEADER in present else [IGNORE_HEADER]
    return ("\n" + "\n".join(header + missing) + "\n").encode()


def run(*args, cwd=None, capture=False):
    return subprocess.run(args, cwd=cwd, check=True, text=True, encoding="utf-8",
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None).stdout


def safe_path(path):
    """Refuse links/junctions rather than writing through them."""
    for part in (path, *path.parents):
        try:
            metadata = part.lstat()
        except (FileNotFoundError, NotADirectoryError):
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
    if host not in ("codex", "claude"):
        raise ValueError(f"Unknown host: {host}")
    if host == "codex":
        # Native Codex definitions point to the full role, beside the installed TOML.
        # Packaging inputs stay out of Claude installs and are required per role.
        for name, content in list(selected.items()):
            if not (name.startswith(".ai/agents/") and name.endswith(".md")
                    and content.startswith(b"---")):
                continue
            origin = ASSETS + "codex-agents/" + Path(name).stem + ".toml"
            if modes.get(origin) not in ("100644", "100755"):
                raise ValueError(f"Missing or unsupported Codex agent install asset: {origin}")
            selected[name[:-3] + ".toml"] = (source / origin).read_bytes()
    rendered = {destination_path(name, host): render_asset(name, content, host)
                for name, content in selected.items()}
    rendered.update(host_payload(rendered, host, hooks))
    return rendered


def destination_path(name, host):
    namespace = "." + host
    if name == "AGENTS.md" and host == "claude":
        return "CLAUDE.md"
    for prefix, destination in ((".agents/skills", skill_root(host)),
                                (".ai", namespace)):
        if name == prefix or name.startswith(prefix + "/"):
            return destination + name[len(prefix):]
    return name


def render_asset(name, content, host):
    """Relocate authored paths without rewriting Python logic or upstream URLs."""
    if name.endswith((".py", ".json")) or not content:
        return content  # Executable code and structured data are copied unchanged.
    text = content.decode("utf-8-sig").replace("\r\n", "\n")
    destination = destination_path(name, host)
    if name.endswith((".md", ".txt")) or name == "AGENTS.md":
        def link(match):
            pieces = re.fullmatch(r'''(<[^>]+>|[^\s]+)(\s+["'].*["'])?''', match[2])
            if pieces is None:
                return match[0]
            target = pieces[1]
            angled = target.startswith("<") and target.endswith(">")
            if angled:
                target = target[1:-1]
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                return match[0]
            bare, anchor, fragment = target.partition("#")
            source_target = posixpath.normpath(posixpath.join(posixpath.dirname(name), bare))
            mapped = destination_path(source_target, host)
            relative = posixpath.relpath(mapped, posixpath.dirname(destination) or ".")
            resolved = relative + (anchor + fragment if anchor else "")
            if angled:
                resolved = "<" + resolved + ">"
            return match[1] + resolved + (pieces[2] or "") + match[3]
        text = re.sub(r"(\[[^\]\n]*\]\()([^\)\n]+)(\))", link, text)
    namespace = "." + host
    def local_paths(part):
        if part.startswith(("https://", "http://")):
            return part
        if host == "claude":
            # Branch examples are host-specific; .codex/ filesystem paths and
            # provenance URLs must retain their separate meaning.
            part = re.sub(r"(?<![\w./-])codex/", "claude/", part)
        if name == ".ai/commands/install.md":
            return part
        part = part.replace(".ai-venv", namespace + "-venv")
        part = part.replace(".agents/skills/", skill_root(host) + "/")
        part = re.sub(r"\.ai(?![\w-])", lambda _: namespace, part)
        if host == "claude" and name not in (".ai/commands/install.md", ".ai/runtime/README.md"):
            part = part.replace("AGENTS.md", "CLAUDE.md")
        return part
    # Source download and attribution URLs must keep the authoring paths.
    text = "".join(local_paths(part) for part in re.split(r"(https?://[^\s<>\"')\]]+)", text))
    return text.encode("utf-8")


def skill_root(host):
    return ".agents/skills" if host == "codex" else ".claude/skills"


def host_payload(rendered, host, hooks):
    """Register hooks; skills are installed in full at their discovery location."""
    if not hooks:
        return {}
    if host == "codex":
        return {".codex/config.toml": hooks_toml(hook_settings(host)["hooks"])}
    return {".claude/settings.json": json_bytes(hook_settings(host))}


def hooks_toml(events):
    """Serialize only generated hook groups, using TOML array-of-table syntax."""
    lines = []
    for event, groups in events.items():
        for group in groups:
            lines.append(f"[[hooks.{event}]]")
            if "matcher" in group:
                lines.append("matcher = " + json.dumps(group["matcher"], ensure_ascii=False))
            for handler in group["hooks"]:
                lines.append(f"[[hooks.{event}.hooks]]")
                for key, value in handler.items():
                    lines.append(f"{key} = " + json.dumps(value, ensure_ascii=False))
            lines.append("")
    return ("\n".join(lines) + "\n").encode("utf-8")


TOML_HEADER = re.compile(r"\s*\[\[?\s*([^\]]+?)\s*\]\]?\s*(#.*)?$")


def remove_toml_groups(text, removed):
    """Drop the `[[hooks.EVENT]]` blocks whose parsed group is in `removed`.

    Every other line -- comments, user tables, formatting -- is kept verbatim.
    A comment or blank run that ends a dropped block is kept too, because it
    usually introduces the table after it.
    """
    lines = text.splitlines(keepends=True)
    blocks, start = [], 0
    for index, line in enumerate(lines):
        header = TOML_HEADER.match(line)
        if not header or index == start:
            continue
        name, owner = header.group(1), TOML_HEADER.match(lines[start])
        if owner and name.startswith(owner.group(1) + "."):
            continue  # A sub-table such as [[hooks.EVENT.hooks]] stays in its group.
        blocks.append(lines[start:index])
        start = index
    blocks.append(lines[start:])
    pending = {event: list(groups) for event, groups in removed.items()}
    kept = []
    for block in blocks:
        header = TOML_HEADER.match(block[0]) if block else None
        event = header.group(1)[len("hooks."):] if header and \
            header.group(1).startswith("hooks.") else None
        if event and block[0].lstrip().startswith("[[") and pending.get(event):
            parsed = tomllib.loads("".join(block)).get("hooks", {}).get(event, [])
            if len(parsed) == 1 and parsed[0] in pending[event]:
                pending[event].remove(parsed[0])
                tail = len(block)
                while tail > 1 and (not block[tail - 1].strip()
                                    or block[tail - 1].lstrip().startswith("#")):
                    tail -= 1
                kept.extend(block[tail:])
                continue
        kept.extend(block)
    if any(pending.values()):
        raise ValueError("could not locate a stale hook table to replace")
    return "".join(kept)


def merge_codex_config(current, incoming, path, replace=False):
    """Append missing hooks while preserving existing TOML text and settings."""
    try:
        settings = tomllib.loads(current.decode("utf-8-sig"))
        additions = tomllib.loads(incoming.decode("utf-8"))
        merged = json.loads(merge_hooks(json_bytes(settings), json_bytes(additions), path,
                                        replace))
        missing = {event: [group for group in groups
                           if group not in settings.get("hooks", {}).get(event, [])]
                   for event, groups in merged["hooks"].items()}
        if not any(missing.values()):
            return current
        removed = {event: [group for group in groups
                           if group not in merged["hooks"].get(event, [])]
                   for event, groups in settings.get("hooks", {}).items()}
        if any(removed.values()):
            bom = b"\xef\xbb\xbf" if current.startswith(b"\xef\xbb\xbf") else b""
            current = bom + remove_toml_groups(current.decode("utf-8-sig"),
                                               removed).encode("utf-8")
        result = current + b"\n" + hooks_toml(missing)
        # Inline arrays/tables cannot always be extended with array-of-tables.
        # Refuse incompatible existing syntax rather than rewrite user settings.
        parsed = tomllib.loads(result.decode("utf-8-sig"))
        if parsed != merged:
            raise ValueError("appended hooks changed existing settings")
        return result
    except (ValueError, UnicodeError) as error:
        raise ValueError(f"Invalid or conflicting host settings {path}: {error}; "
                         "reconcile the TOML hook tables before installation.") from error


#: Managed hook registrations: (event, script, matcher). The worktree guard is
#: registered twice because its two jobs watch different tools -- refusing an
#: unisolated subagent dispatch, and warning about a write outside a worktree.
MANAGED_HOOKS = (
    ("PostToolUse", "ai-tier-notice.sh",
     "^(Bash|Write|Edit|MultiEdit|NotebookEdit|apply_patch)$"),
    ("PreToolUse", "worktree-guard.sh", "^(Agent|Task)$"),
    ("PreToolUse", "worktree-guard.sh",
     "^(Write|Edit|MultiEdit|NotebookEdit|apply_patch)$"),
    # The handoff hook measures on PostToolUse, catches an executor that
    # stopped early on SubagentStop, and clears its own session state on Stop.
    # SubagentStop and Stop carry no tool, so neither carries a tool matcher.
    # Codex does accept an `agent_type` matcher on SubagentStop, but the hook
    # filters on the role itself and Claude has no equivalent, so one
    # unmatched registration keeps the two hosts on the same shape.
    ("PostToolUse", "context-handoff.sh",
     "^(Bash|Write|Edit|MultiEdit|NotebookEdit|apply_patch|Agent|Task)$"),
    ("SubagentStop", "context-handoff.sh", None),
    ("Stop", "context-handoff.sh", None),
)

#: Registrations one host alone has an event for: (event, script, timeout).
#: Claude Code creates a subagent's isolated checkout itself, under
#: .claude/worktrees/ and branched from the default branch; WorktreeCreate
#: replaces that so every worktree lands under the project's worktree root and
#: starts from the phase being built. Creating a checkout of a large repository
#: can outlast the 10-second default, hence the longer timeout.
#:
#: Codex gives a tool-use hook no agent identity, so the handoff hook tells its
#: orchestrator apart by the transcript SessionStart records. Claude needs no
#: such record: every hook fired inside a Claude subagent carries agent_id.
HOST_HOOKS = {
    "claude": (
        ("WorktreeCreate", "worktree-location.sh", 180),
        ("WorktreeRemove", "worktree-location.sh", 60),
    ),
    "codex": (
        ("SessionStart", "context-handoff.sh", 10),
    ),
}


def managed_scripts():
    """Every script a managed registration can name, on any host."""
    names = {script for _, script, _ in MANAGED_HOOKS}
    names.update(script for hooks in HOST_HOOKS.values() for _, script, _ in hooks)
    return names


def hook_settings(host):
    events = {}
    registrations = [(event, script, matcher, 10) for event, script, matcher in MANAGED_HOOKS]
    registrations += [(event, script, None, timeout)
                      for event, script, timeout in HOST_HOOKS.get(host, ())]
    for event, script, matcher, timeout in registrations:
        command = f'bash "$(git rev-parse --show-toplevel)/.{host}/hooks/{script}"'
        handler = {"type": "command", "command": command, "timeout": timeout}
        if host == "codex":
            # Git for Windows does not put git.exe in one fixed place. An
            # installer-managed install has it at <root>\cmd\git.exe, so
            # ../bin/bash.exe resolves; a portable, scoop or winget layout has
            # it at <root>\mingw64\bin\git.exe, where the same relative path
            # points at mingw64\bin\bash.exe, which does not exist. Assuming
            # the first layout meant every Codex hook failed to launch on the
            # second -- including the dispatch guard, so an unisolated executor
            # went through while PowerShell printed CommandNotFoundException.
            #
            # Probe the known layouts and take the first bash that is really
            # there. PATH is deliberately not a fallback: on Windows it
            # commonly resolves to WSL's bash, which cannot see the Windows
            # checkout the hook is about to inspect. Finding none is a
            # misconfiguration worth surfacing, so it exits 1 (an error) rather
            # than 0 (silently no hook) or 2 (a denial the hook never made).
            #
            # `; exit $LASTEXITCODE` is load-bearing. PowerShell -Command does not
            # propagate a native command's exit status, so a hook that exits 2 to
            # deny a tool call arrived at the host as 1 -- the decision was made
            # and then thrown away. It went unnoticed while every managed hook
            # exited 0; worktree-guard.sh is the first that denies.
            handler["commandWindows"] = (
                "$d=Split-Path (Get-Command git).Source; "
                "$b=@('..\\bin\\bash.exe','..\\..\\bin\\bash.exe',"
                "'..\\usr\\bin\\bash.exe','..\\..\\usr\\bin\\bash.exe') "
                "| ForEach-Object { Join-Path $d $_ } "
                "| Where-Object { Test-Path $_ } | Select-Object -First 1; "
                "if (-not $b) { Write-Error 'Git Bash not found near git.exe'; exit 1 }; "
                # The repository path never crosses the PowerShell/bash
                # boundary. Capturing `git rev-parse` in PowerShell and passing
                # the result as a native argument mangles every non-ASCII path
                # component -- a checkout under "projet cafe 日本語" reached bash
                # as box-drawing characters and the hook died with "No such
                # file or directory", which reads like a missing hook rather
                # than an encoding fault. Handing bash an ASCII-only -c string
                # and letting it resolve the root itself removes the boundary,
                # and matches what the POSIX `command` above already does.
                # The inner quotes are written \" rather than ": PowerShell
                # re-parses a native command's arguments, and a bare double
                # quote inside them is consumed rather than passed, which
                # re-split this script at its spaces and left bash reading
                # "rev-parse" as its own name.
                "& $b -c 'exec bash \\\"$(git rev-parse --show-toplevel)"
                f"/.{host}/hooks/{script}\\\"'; "
                "exit $LASTEXITCODE")
        group = {"hooks": [handler]} if matcher is None else {"matcher": matcher,
                                                               "hooks": [handler]}
        events.setdefault(event, []).append(group)
    return {"hooks": events}


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


def merge_hooks(current, incoming, path, replace=False):
    """Append managed groups, retaining user settings and refusing ambiguous edits.

    With `replace`, a managed group an older revision wrote is swapped for the
    current one instead of refused.
    """
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
        scripts = managed_scripts()
        for event, groups in additions.items():
            existing = events.setdefault(event, [])
            for group in groups:
                if group in existing:
                    continue
                script = next((name for name in scripts
                               if f"/hooks/{name}" in json.dumps(group)), None)
                # A group already registering THIS script under THIS matcher,
                # but not byte-identical, is a customized or older managed
                # registration. A user hook on the same event that names a
                # different script is theirs, and is left alone.
                stale = [other for other in existing
                         if script and f"/hooks/{script}" in json.dumps(other)
                         and other.get("matcher") == group.get("matcher")]
                # An update replaces a stale registration, as it replaces any
                # other shipped file, once the caller has backed the settings
                # up. A group that also carries a user handler is not wholly
                # ours to replace, and an install never replaces at all.
                if stale and not (replace and all(
                        all(f"/hooks/{script}" in json.dumps(handler)
                            for handler in other["hooks"]) for other in stale)):
                    raise ValueError(f"managed {event} registration for {script} "
                                     "differs; reconcile it manually")
                existing[:] = [other for other in existing if other not in stale]
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


def merge_agent(current, incoming, name="AGENTS.md"):
    if any(variant in current for variant in (incoming, incoming.replace(b"\n", b"\r\n"))):
        return current
    if AGENT_MARKER.encode() in current:
        raise ValueError(f"Existing {name} workflow block differs; reconcile it before installation.")
    return current + b"\n\n" + incoming


def plan_install(source, target, host="codex", hooks=True):
    changes = []
    conflicts = []
    other = ".claude" if host == "codex" else ".codex"
    if (target / other / "runtime/phase.py").exists() and (target / other / "RULES.md").exists():
        raise ValueError(f"An existing workflow is installed under {other}; use that host or "
                         "migrate it on a branch before switching. Nothing was installed.")
    old_root = target / ".ai"
    safe_path(old_root)
    if old_root.exists():
        raise ValueError("Existing .ai requires --migrate-existing on a review branch; "
                         "nothing was installed.")
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
            if name in PROJECT_RECORDS:
                continue  # Existing intent, execution history and config remain authoritative.
            elif name in ("AGENTS.md", "CLAUDE.md"):
                require_utf8(current, destination)
                incoming = merge_agent(current, incoming, name)
                if current == incoming:
                    continue
            elif name in (".codex/config.toml", ".claude/settings.json"):
                merge = merge_codex_config if name.endswith(".toml") else merge_hooks
                incoming = merge(current, incoming, destination)
                if current == incoming:
                    continue
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
        require_utf8(current, ignore)
        addition = ignore_addition(current, "." + host)
        if addition:
            changes.append((ignore, current + addition))
    if conflicts:
        raise ValueError("Existing files conflict; nothing was installed. Reconcile these paths "
                         "on a review branch, then retry:\n  " + "\n  ".join(sorted(set(conflicts))))
    return sorted(changes, key=lambda item: item[1] is None)


def backup_migration(target, files):
    """Preserve and verify every original before any migration mutation."""
    backup_root = target / ".workflow-backups"
    safe_path(backup_root)
    backup = backup_root / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                            + "-" + uuid.uuid4().hex[:8])
    safe_path(backup)
    backup.mkdir(parents=True, exist_ok=False)
    # Ignore this complete snapshot even when migration fails before root ignores
    # are updated. Keep original .gitignore files below a separate files folder.
    (backup / ".gitignore").write_bytes(b"*\n")
    manifest = {}
    modes = {}
    for path in sorted(set(files)):
        safe_path(path)
        relative = path.relative_to(target)
        original = path.read_bytes()
        saved = backup / "files" / relative
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_bytes(original)
        shutil.copymode(path, saved)
        digest = hashlib.sha256(original).hexdigest()
        if hashlib.sha256(saved.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Backup verification failed for {relative}; originals retained.")
        manifest[relative.as_posix()] = digest
        modes[relative.as_posix()] = stat.S_IMODE(path.stat().st_mode)
    (backup / "MANIFEST.json").write_bytes(json_bytes({"original_root": str(target), "sha256": manifest,
                                                       "file_modes": modes}))
    # Detect a concurrent edit during backup before changing any original.
    for relative, digest in manifest.items():
        path = target / relative
        safe_path(path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Original changed during backup: {relative}; migration stopped.")
    return backup


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
                           text=True, encoding="utf-8", capture_output=True)
    in_git = probe.returncode == 0
    if in_git and Path(probe.stdout.strip()).resolve() != target:
        raise ValueError("Target is inside another repository. Choose its root.")
    namespace = "." + args.host
    if not args.skip_deps:
        environment = target / (namespace + "-venv")
        safe_path(environment)
        if environment.exists() and not args.update:
            raise ValueError(f"{namespace}-venv already exists; preserve it and rerun with --skip-deps. "
                             f"See {namespace}/commands/install.md for dependency repair.")
    with ExitStack() as stack:
        temporary = stack.enter_context(tempfile.TemporaryDirectory(prefix="ai-template-"))
        source = Path(temporary)
        run("git", "init", "--quiet", str(source))
        run("git", "fetch", "--quiet", "--depth=1", "--", args.source, args.ref, cwd=source)
        run("git", "checkout", "--quiet", "--detach", "FETCH_HEAD", cwd=source)
        revision = run("git", "rev-parse", "HEAD", cwd=source, capture=True).strip()
        # The revision the project was installed from, fetched into its own tree
        # so an update can tell a local customization from an upstream change.
        previous = None
        if args.from_ref:
            baseline = stack.enter_context(tempfile.TemporaryDirectory(prefix="ai-baseline-"))
            previous = Path(baseline)
            run("git", "init", "--quiet", str(previous))
            run("git", "fetch", "--quiet", "--depth=1", "--", args.source, args.from_ref,
                cwd=previous)
            run("git", "checkout", "--quiet", "--detach", "FETCH_HEAD", cwd=previous)
        backup_files = []
        notes = []
        if args.migrate_existing:
            migration = runpy.run_path(str(source / ".ai/install_migration.py"))
            changes, backup_files, notes = migration["plan_migration"](
                source, target, args.host, not args.no_hooks, SimpleNamespace(**globals()))
        elif args.update:
            update = runpy.run_path(str(source / ".ai/install_update.py"))
            changes, backup_files, notes = update["plan_update"](
                source, target, args.host, not args.no_hooks, SimpleNamespace(**globals()),
                prune=args.prune, previous=previous)
        else:
            changes = plan_install(source, target, args.host, not args.no_hooks)
        originals = {destination_path(name, args.host): source / name
                     for name in run("git", "ls-files", "-z", cwd=source, capture=True).split("\0")
                     if name}
        for original in backup_files:
            relative = original.relative_to(target).as_posix()
            originals.setdefault(destination_path(relative, args.host), original)
        mode = ("update" if args.update else
                "migrate" if args.migrate_existing else "install")
        print(f"Template revision: {revision}\nTarget: {target}\nHost: {args.host}; "
              f"mode: {mode}; "
              f"hook registration: {'skip' if args.no_hooks else 'advisory'}", flush=True)
        print(f"{'Would change' if args.dry_run else 'Changing'} {len(changes)} workflow files.", flush=True)
        for note in notes:
            print(note)
        if args.dry_run:
            for path, content in changes:
                print(f"  {'remove' if content is None else 'write'} {path.relative_to(target)}")
            print(f"Git: {'preserve repository' if in_git else 'initialize repository'}; "
                  f"dependencies: {'skip' if args.skip_deps else 'create ' + namespace + '-venv and install PyYAML'}")
            if backup_files:
                print(f"Would back up and verify {len(backup_files)} original files under "
                      f".workflow-backups/ before {'updating' if args.update else 'migration'}.")
            return
        target.mkdir(parents=True, exist_ok=True)
        if backup_files:
            backup = backup_migration(target, backup_files)
            print(f"Verified original-data backup: {backup}", flush=True)
        for destination, content in changes:
            if content is None:
                if destination.is_dir():
                    destination.rmdir()
                else:
                    destination.unlink()
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            existed = destination.exists()
            destination.write_bytes(content)
            original = originals.get(destination.relative_to(target).as_posix())
            if not existed and original is not None and original.is_file():
                shutil.copymode(original, destination)
        if not in_git:
            run("git", "init", "--quiet", str(target))
        if not args.skip_deps:
            run(sys.executable, "-m", "venv", str(environment))
            interpreter = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            run(str(interpreter), "-m", "pip", "install", "-r",
                str(target / namespace / "runtime/requirements.txt"))
            run(str(interpreter), str(target / namespace / "runtime/phase.py"),
                "query", "runtime-identity", cwd=target)
        print("Installed. No project files were committed and no remote was changed.\n"
              "A human must review and commit the bootstrap before handing off to an "
              f"agent (see {namespace}/commands/install.md).\n"
              f"Next: follow {namespace}/commands/onboard.md to fill project intent, configure "
              "the project's real verification commands, and commit setup.")
        if not args.no_hooks:
            print("Review project hook registrations in /hooks in each selected host. "
                  "Codex requires project and hook trust before running them; existing "
                  "host policies remain in effect. No personal configuration was changed.")


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default=".", help="Project root (default: current directory)")
    parser.add_argument("--source", default=SOURCE, help="Template Git URL or local repository")
    parser.add_argument("--ref", default="main", help="Template branch, tag or commit (default: main)")
    location = Path(globals().get("__file__", ".ai/install.py")).parent.name
    default_host = "claude" if location == ".claude" else "codex"
    parser.add_argument("--host", choices=("codex", "claude"), default=default_host,
                        help=f"Install commands, agents and runtime under .codex or .claude (default: {default_host})")
    parser.add_argument("--no-hooks", action="store_true",
                        help="Skip adding hook registrations; preserve existing hooks")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and check without changing the target")
    parser.add_argument("--skip-deps", action="store_true", help="Skip virtual environment and dependency setup")
    parser.add_argument("--migrate-existing", action="store_true",
                        help="Rebuild an existing .ai workflow for the selected host, preserving project data and verified originals")
    parser.add_argument("--update", action="store_true",
                        help="Refresh an already-installed .codex or .claude workflow onto "
                             "this revision, preserving project records and merging host settings")
    parser.add_argument("--from-ref", default=None,
                        help="With --update, the revision this project was installed from; lets "
                             "the report name local customizations it is about to replace")
    parser.add_argument("--prune", action="store_true",
                        help="With --update, also remove installed workflow files this revision "
                             "no longer ships (backed up and verified first)")
    args = parser.parse_args()
    if args.update and args.migrate_existing:
        parser.error("--update refreshes an installed host tree and --migrate-existing "
                     "rebuilds an older .ai one; run the migration first, then update.")
    for flag, value in (("--from-ref", args.from_ref), ("--prune", args.prune)):
        if value and not args.update:
            parser.error(flag + " applies only to --update.")
    try:
        if sys.version_info < (3, 11):
            raise ValueError("Python 3.11 or newer is required.")
        if not shutil.which("git"):
            raise ValueError("Git is required on PATH.")
        install(args)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Setup failed: {error}\nIf setup had already started, files are retained for "
              "inspection; fix the error and retry with --skip-deps when the host venv exists.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
