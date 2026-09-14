"""Plan a lossless, backed-up migration from .ai to one host's workflow tree.

This module performs no writes. The installer must back up and verify every
returned backup file before applying any of the planned changes.
"""

from pathlib import Path
import json
import re


LEGACY_RECORDS = ("PROJECT.md", "REQUIREMENTS.md", "ROADMAP.md", "STATE.md",
                  "config.yaml", "phases", "codebase", "specs", "decisions")
TEXT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".toml", ".sh", ".ps1"}


def relocate_paths(content, host):
    """Translate local workflow paths without reserializing config or URLs."""
    namespace = ("." + host).encode()
    parts = re.split(rb"(https?://[^\s<>\"')\]]+)", content)
    for index, part in enumerate(parts):
        if part.startswith((b"http://", b"https://")):
            continue
        for separator in (b"/", b"\\\\", b"\\"):
            for old, new in ((b".ai" + separator + b"agents", namespace + separator + b"roles"),
                             (b".ai" + separator + b"commands", namespace + separator + b"workflows"),
                             (b".agents" + separator + b"skills", namespace + separator + b"skills")):
                part = part.replace(old + separator, new + separator)
            part = part.replace(b".ai" + separator, namespace + separator)
        part = part.replace(b".ai-venv", namespace + b"-venv")
        parts[index] = part
    return b"".join(parts)


def inventory(root, installer):
    """Walk without following links, including Windows directory junctions."""
    installer.safe_path(root)
    if not root.exists():
        return [], []
    if not root.is_dir():
        raise ValueError(f"Migration requires a directory: {root}")
    files, directories = [], [root]
    pending = [root]
    while pending:
        for path in sorted(pending.pop().iterdir()):
            installer.safe_path(path)
            if path.is_dir():
                directories.append(path)
                pending.append(path)
            elif path.is_file():
                files.append(path)
            else:
                raise ValueError(f"Unsupported migration entry: {path}; nothing was installed.")
    return files, sorted(directories, key=lambda path: len(path.parts), reverse=True)


def render_existing(name, content, host, installer):
    # Opaque project assets are data, even when a UTF-8 decoder accepts them.
    if Path(name).suffix.lower() not in TEXT_SUFFIXES or b"\0" in content:
        return content
    try:
        return installer.render_asset(name, content, host)
    except UnicodeError:
        return content


def entry_remainder(content, installer, name):
    """Remove exactly one complete managed block, never guessed user content."""
    start, end = installer.AGENT_MARKER.encode(), installer.AGENT_END.encode()
    if start not in content and end not in content:
        return content
    if content.count(start) == 1 and end not in content:
        # Older installers had no closing marker. Its ending cannot safely be
        # distinguished from appended project instructions, so preserve it all.
        return content
    if content.count(start) != 1 or content.count(end) != 1:
        raise ValueError(f"Ambiguous managed workflow block in {name}; nothing was installed.")
    first, last = content.index(start), content.index(end)
    if last < first:
        raise ValueError(f"Malformed managed workflow block in {name}; nothing was installed.")
    return content[:first] + content[last + len(end):]


def relocate_hook_commands(content, host, installer):
    """Move only hook command paths; preserve unrelated settings and values."""
    settings = json.loads(content.decode("utf-8-sig"),
                          object_pairs_hook=installer.unique_json_object,
                          parse_constant=installer.invalid_json_constant)
    if not isinstance(settings, dict):
        raise ValueError("Host settings must be a JSON object.")
    changed = False
    def walk(value):
        nonlocal changed
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ("command", "commandWindows") and isinstance(item, str):
                    updated = relocate_paths(item.encode("utf-8"), host).decode("utf-8")
                    if updated != item:
                        value[key] = updated
                        changed = True
                else:
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    walk(settings.get("hooks", {}))
    return installer.json_bytes(settings) if changed else content


def plan_migration(source, target, host, hooks, installer):
    """Return writes/exact deletions, original files to back up, and report notes."""
    if host not in ("codex", "claude"):
        raise ValueError(f"Unknown host: {host}")
    source, target = Path(source), Path(target)
    old_root = target / ".ai"
    installer.safe_path(target)
    backup_root = target / ".workflow-backups"
    installer.safe_path(backup_root)
    if backup_root.exists() and not backup_root.is_dir():
        raise ValueError(f"Migration backup location is not a directory: {backup_root}")
    if not old_root.exists():
        raise ValueError("--migrate-existing requires an existing .ai directory.")
    old_files, old_dirs = inventory(old_root, installer)
    legacy = [name for name in LEGACY_RECORDS if (old_root / name).exists()]
    if legacy:
        raise ValueError("Legacy project records remain under .ai: " + ", ".join(legacy)
                         + ". Preserve and reconcile them into .planning with their compatible "
                         "original runtime first; finish or inspect old attempts without copying "
                         "or reinterpreting checkpoints. Nothing was installed.")
    planning_files, _ = inventory(target / ".planning", installer)
    skill_files, skill_dirs = inventory(target / ".agents/skills", installer)
    incoming = installer.payload(source, host, hooks)
    namespace = "." + host
    other = ".claude" if host == "codex" else ".codex"
    if (target / other / "runtime/phase.py").exists() or (target / other / "RULES.md").exists():
        raise ValueError(f"A second workflow exists under {other}; reconcile dual cores before migration.")
    backups = set(old_files + planning_files + skill_files)
    notes = ["Project history in .planning is preserved; only config runtime paths may change.",
             "Git checkpoints and existing worktrees are not modified or copied.",
             "The old .ai-venv is preserved without traversal; the selected host uses a separate environment."]
    desired = dict(incoming)
    refreshed = []
    relocated = {}
    for old in old_files + skill_files:
        name = old.relative_to(target).as_posix()
        destination = installer.destination_path(name, host)
        current = old.read_bytes()
        if destination in relocated:
            raise ValueError(f"Old paths {relocated[destination]} and {name} both map to "
                             f"{destination}; reconcile them before migration.")
        relocated[destination] = name
        refresh = (name.startswith((".ai/runtime/", ".ai/hooks/"))
                   or name in (".ai/install.py", ".ai/install_migration.py"))
        if refresh and destination in incoming:
            if current != incoming[destination]:
                refreshed.append(name)
        else:
            desired[destination] = render_existing(name, current, host, installer)
    if refreshed:
        notes.append("Refresh shipped implementation; original versions remain in backup: "
                     + ", ".join(sorted(refreshed)))
    # The full customized skills, including their metadata, determine discovery.
    # Remove the source payload's wrappers before regenerating the complete set.
    for name in list(desired):
        if name.startswith(".agents/skills/"):
            del desired[name]
    desired.update(installer.host_payload(desired, host, hooks))
    for path in planning_files:
        name = path.relative_to(target).as_posix()
        current = path.read_bytes()
        desired[name] = current
        if name == ".planning/config.yaml":
            original_default = source / name
            if original_default.is_file() and current.replace(b"\r\n", b"\n") == original_default.read_bytes().replace(b"\r\n", b"\n"):
                desired[name] = incoming[name]
                notes.append("Select host worker defaults from the unchanged template config.")
            else:
                # Byte replacement preserves comments, custom commands and formatting.
                desired[name] = relocate_paths(current, host)
                notes.append("Custom worker commands and checks are retained; review their host compatibility.")
    entry = "CLAUDE.md" if host == "claude" else "AGENTS.md"
    entry_paths = {name: target / name for name in ("AGENTS.md", "CLAUDE.md")}
    remainders = {}
    for name, path in entry_paths.items():
        installer.safe_path(path)
        if path.exists():
            if not path.is_file():
                raise ValueError(f"Entry point is not a file: {path}")
            current = path.read_bytes()
            installer.require_utf8(current, path)
            backups.add(path)
            remainders[name] = entry_remainder(current, installer, name)
    custom = remainders.get(entry, b"")
    if host == "claude" and "AGENTS.md" in remainders:
        previous = remainders["AGENTS.md"]
        if previous.strip() and previous not in custom:
            custom += b"\n\n" + previous
    mapping = ("\n\nHistorical plans keep their original paths. When following them, resolve "
               f"`.ai/agents/` to `{namespace}/roles/`, `.ai/commands/` to "
               f"`{namespace}/workflows/`, `.agents/skills/` to `{namespace}/skills/`, "
               f"and other `.ai/` paths to `{namespace}/`. Project records remain in "
               "`.planning/`; do not rewrite completed history or reuse incompatible old checkpoints. "
               "Before execution, reconcile pending PLAN ownership and Read first paths with "
               "the installed layout, then recheck and reverify; the runtime does not translate "
               "PLAN ownership from this prose mapping. "
               "The current managed entry and its delivery rules govern current work.\n").encode()
    desired[entry] = custom + (b"\n\n" if custom else b"") + incoming[entry] + mapping
    if host == "claude" and "AGENTS.md" in remainders:
        desired["AGENTS.md"] = remainders["AGENTS.md"]
    for name in (".codex/hooks.json", ".claude/settings.json"):
        path = target / name
        installer.safe_path(path)
        if path.exists():
            if not path.is_file():
                raise ValueError(f"Host settings are not a file: {path}")
            backups.add(path)
            if name.startswith(namespace + "/"):
                current = relocate_hook_commands(path.read_bytes(), host, installer)
                desired[name] = (installer.merge_hooks(current, desired[name], path)
                                 if name in desired else current)
    ignore = target / ".gitignore"
    installer.safe_path(ignore)
    if ignore.exists() and not ignore.is_file():
        raise ValueError(f"Not a file: {ignore}")
    current_ignore = ignore.read_bytes() if ignore.exists() else b""
    installer.require_utf8(current_ignore, ignore)
    if ignore.exists():
        backups.add(ignore)
    # Keep ignored custom workflow data ignored after it changes directory.
    current_ignore = relocate_paths(current_ignore, host)
    current_ignore = re.sub(rb"(?m)^(!?/?)[.]ai(?=\r?$)",
                            lambda match: match[1] + namespace.encode(), current_ignore)
    block = installer.IGNORE_BLOCK.replace(".ai-venv", namespace + "-venv").encode()
    desired[".gitignore"] = current_ignore if block in current_ignore.replace(b"\r\n", b"\n") else current_ignore + block
    writes = []
    for name, content in sorted(desired.items()):
        destination = target / name
        installer.safe_path(destination)
        for parent in destination.parents:
            if parent.exists() and not parent.is_dir():
                raise ValueError(f"Migration destination parent is not a directory: {parent}")
        if destination.exists():
            if not destination.is_file():
                raise ValueError(f"Migration destination is not a file: {destination}")
            current = destination.read_bytes()
            if current == content:
                continue
            if destination not in backups:
                raise ValueError(f"Existing destination conflicts: {destination}; nothing was installed.")
        writes.append((destination, content))
    # Only exact inventoried old files are removed, after all writes. Codex
    # discovery wrappers stay; their former support files move into .codex.
    retained = {target / name for name in desired}
    deletes = [(path, None) for path in old_files + skill_files if path not in retained]
    deletes.extend((path, None) for path in old_dirs + skill_dirs
                   if not any(path == kept or path in kept.parents for kept in retained))
    return writes + deletes, sorted(backups), notes
