"""Migrate adopting-project legacy paths without replacing project planning records."""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys

# Loading helpers during a preview must not create installed bytecode caches.
sys.dont_write_bytecode = True

_spec = importlib.util.spec_from_file_location("engineer_installer_for_migration", Path(__file__).with_name("install.py"))
installer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(installer)
ALIASES = {"coder": "executor", "phase-preparer": "planner", "phase-checker": "plan-checker", "researcher": "phase-researcher"}


def relocate_paths(value, host):
    """Relocate legacy references in data; no legacy implementation is used as source."""
    namespace = "." + host
    if isinstance(value, bytes) and b"\x00" in value:
        return value
    text = value.decode("utf-8") if isinstance(value, bytes) else value
    text = re.sub(r"(?<![\w./:-])\.ai(\\+)runtime\1phase\.py\b",
                  lambda match: namespace + match[1] + "engineer" + match[1] + "bin" + match[1] + "engineer.py", text)
    # Match path tokens, not URL path components. Keep escaped Windows
    # separators exactly as represented by their surrounding YAML/JSON string.
    def windows(match):
        separator = match[1]
        suffix = match[2]
        if suffix == "runtime":
            suffix = "engineer" + separator + "bin"
        elif suffix in ("templates", "workflows", "references", "guides", "rules", "RULES.md"):
            suffix = "engineer" + separator + suffix
        return namespace + separator + suffix
    text = re.sub(r"(?<![\w./:-])\.ai(\\+)([\w.-]+)", windows, text)
    text = re.sub(r"(?<![\w./:-])\.agents/skills(?=/|\b)", installer.skill_root(host), text)
    # Slash references use the same boundary rule so https://.../.ai is data.
    def slash(match):
        suffix = match[1] or ""
        if suffix == "runtime/phase.py":
            suffix = "engineer/bin/engineer.py"
        elif suffix == "runtime" or suffix.startswith("runtime/"):
            suffix = "engineer/bin" + suffix[len("runtime"):]
        elif suffix.split("/", 1)[0] in ("templates", "workflows", "references", "guides", "rules", "RULES.md"):
            suffix = "engineer/" + suffix
        elif suffix == "skills" or suffix.startswith("skills/"):
            return installer.skill_root(host) + suffix[len("skills"):]
        if suffix.startswith("agents/") and suffix.endswith(".md"):
            role = suffix[len("agents/"):-3]
            suffix = "agents/" + ALIASES.get(role, role) + ".md"
            if host == "claude" and role == "code-fixer":
                suffix = "engineer/references/code-fixer.md"
        return namespace + "/" + suffix
    text = re.sub(r"(?<![\w./:-])\.ai/([\w./-]*)", slash, text)
    for old, final in ALIASES.items():
        text = re.sub(re.escape(namespace) + r"(\\+)agents\1" + re.escape(old) + r"\.md\b",
                      lambda match: namespace + match[1] + "agents" + match[1] + final + ".md", text)
    for old in (namespace + "/runtime/phase.py",):
        text = re.sub(r"(?<![\w./:-])" + re.escape(old), namespace + "/engineer/bin/engineer.py", text)
    for old in (namespace + "/runtime",):
        text = re.sub(r"(?<![\w./:-])" + re.escape(old) + r"(?=/|\b)", namespace + "/engineer/bin", text)
    text = re.sub(r"\bphase_run\b", "engineer_run", text)
    return text.encode("utf-8") if isinstance(value, bytes) else text


def relocated_name(name, host):
    ns = "." + host
    if name.startswith(".ai/"):
        suffix = name[4:]
        if suffix.startswith("skills/"):
            return installer.skill_root(host) + suffix[len("skills"):]
        if suffix.startswith("runtime/"):
            suffix = "engineer/bin/" + suffix[len("runtime/"):]
        elif suffix.startswith(("templates/", "workflows/", "references/", "guides/", "rules/")) or suffix == "RULES.md":
            suffix = "engineer/" + suffix
        if suffix.startswith("agents/") and suffix.endswith(".md"):
            role = Path(suffix).stem
            suffix = "agents/" + ALIASES.get(role, role.removeprefix("gsd-")) + ".md"
            if host == "claude" and role == "code-fixer":
                suffix = "engineer/references/code-fixer.md"
        return ns + "/" + suffix
    if name.startswith(ns + "/runtime/"):
        return ns + "/engineer/bin/" + name.split("/runtime/", 1)[1]
    if name.startswith(".agents/skills/"):
        return installer.skill_root(host) + name[len(".agents/skills"):]
    return name


def legacy_inventory(target, host):
    target = Path(target).resolve()
    result = {}
    for prefix in (".ai", "." + host + "/runtime", ".agents/skills"):
        folder = installer.destination(target, prefix)
        if not folder.exists():
            continue
        if not folder.is_dir():
            raise ValueError("legacy input must be a directory: " + prefix)
        for path in folder.rglob("*"):
            if installer.linked(path):
                raise ValueError("linked path refused: " + str(path))
            if path.is_file():
                result[path.relative_to(target).as_posix()] = path.read_bytes()
    return result


def plan_migration(source, target, host="codex", hooks=True, installer_module=None):
    target = Path(target).resolve()
    legacy = legacy_inventory(target, host)
    if not any(name.startswith((".ai/", "." + host + "/runtime/")) for name in legacy):
        raise ValueError("migration requires an existing .ai directory or host runtime directory")
    other = ".claude" if host == "codex" else ".codex"
    if (target / other / "engineer/bin/engineer.py").exists():
        raise ValueError("second host installation conflicts")
    backup_root = target / ".workflow-backups"
    if installer.linked(backup_root) or backup_root.exists() and not backup_root.is_dir():
        raise ValueError("backup location is not a safe directory")
    incoming = installer.payload(source, host, hooks)
    changes, originals, migrated = {}, {}, {}
    # Preserve every legacy original in a verified backup before removing its path.
    for name, data in legacy.items():
        original = installer.destination(target, name)
        originals[original] = data
        changes[original] = None
        new_name = relocated_name(name, host)
        new_path = installer.destination(target, new_name)
        if new_path.exists() and new_name != name and new_name not in legacy:
            raise ValueError("native collision at " + new_name)
        try:
            relocated = relocate_paths(installer.render_asset(new_name, data, host) if "/skills/" in new_name else data, host)
        except UnicodeError:
            relocated = data
        if ("/agents/" in new_name and new_name.endswith(".md")) or new_name.endswith("/engineer/references/code-fixer.md"):
            relocated = installer.render_asset("agents/" + Path(new_name).name, relocated, host)
        # Old runtime entry points never replace the freshly authored runtime.
        if new_name in migrated:
            raise ValueError("two old paths both map to " + new_name)
        if new_name.endswith("/engineer/bin/phase.py"):
            continue
        migrated[new_name] = relocated
    for name, candidate in incoming.items():
        path = installer.destination(target, name)
        if path.exists() and not path.is_file():
            raise ValueError("directory occupies installed file: " + name)
        before = path.read_bytes() if path.is_file() else None
        if name.startswith(".planning/") and before is not None:
            # Planning narratives, decisions and traceability are never rewritten.
            continue
        if before is not None:
            if name in ("AGENTS.md", "CLAUDE.md", ".gitignore", ".codex/config.toml", ".claude/settings.json"):
                candidate = installer.merge_file(name, before, candidate, host, hooks)
            elif not installer.same_text(before, candidate):
                raise ValueError("native collision at " + name)
            originals[path] = before
        # Explicit adopting-project custom agents retain their complete body.
        if name in migrated and (("/agents/" in name and name.endswith(".md")) or name.endswith(("/engineer/RULES.md", "/engineer/references/code-fixer.md"))):
            candidate = migrated.pop(name)
        changes[path] = candidate
    for name, data in migrated.items():
        path = installer.destination(target, name)
        if path not in changes or changes[path] is None:
            changes[path] = data
    if host == "codex":
        for path, body in list(changes.items()):
            if path.parent == target / ".codex/agents" and path.suffix == ".md" and path.stem not in {"AGENT", "code-fixer"} and body is not None:
                description = re.search(r"^description: (.+)$", body.decode("utf-8"), re.M)
                native = path.with_suffix(".toml")
                changes[native] = installer.agent_native(path.stem, description[1] if description else path.stem, body.decode("utf-8"))
    config = installer.destination(target, ".planning/config.yaml")
    if config.is_file():
        original = config.read_bytes()
        candidate = relocate_paths(original, host)
        if candidate != original:
            originals[config] = original
            changes[config] = candidate
    # Relocate only hook commands in host settings; unrelated user values stay
    # byte-identical. JSON is parsed to avoid rewriting non-command strings.
    settings = installer.destination(target, "." + host + ("/settings.json" if host == "claude" else "/config.toml"))
    if settings.is_file():
        raw = settings.read_bytes()
        if host == "claude":
            value = installer.settings_json(installer.utf8(raw, str(settings)))
            for groups in value.get("hooks", {}).values():
                for group in groups:
                    for hook in group.get("hooks", []):
                        for key in ("command", "commandWindows"):
                            if isinstance(hook.get(key), str):
                                hook[key] = relocate_paths(hook[key], host)
            relocated_settings = installer.json_bytes(value)
        else:
            lines = raw.decode("utf-8-sig").splitlines(keepends=True)
            for index, line, inside in installer.toml_lines(raw.decode("utf-8-sig")):
                if not inside and re.match(r"\s*command(?:Windows)?\s*=", line):
                    lines[index] = relocate_paths(line, host)
            relocated_settings = (b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b"") + "".join(lines).encode()
        candidate = installer.merge_file(settings.relative_to(target).as_posix(), relocated_settings,
                                        incoming.get(settings.relative_to(target).as_posix(), b"{}"), host, hooks) if hooks or host == "codex" else relocated_settings
        if candidate != raw:
            originals[settings] = raw
            changes[settings] = candidate
    # A host switch carries the user's entry prose and removes only the old
    # managed block. Unmarked instructions remain in their original file too.
    old_entry = installer.destination(target, "AGENTS.md")
    if host == "claude" and old_entry.is_file():
        raw = old_entry.read_bytes()
        text = installer.utf8(raw, "AGENTS.md")
        block = installer.managed_block(text)
        destination_entry = installer.destination(target, "CLAUDE.md")
        if not destination_entry.exists():
            changes[destination_entry] = installer.merge_entry(raw, incoming["CLAUDE.md"])
        if block:
            originals[old_entry] = raw
            changes[old_entry] = text.replace(block, "", 1).encode()
    ignore = installer.destination(target, ".gitignore")
    if ignore.is_file():
        raw = ignore.read_bytes()
        candidate = installer.merge_file(".gitignore", relocate_paths(raw, host), incoming[".gitignore"], host, hooks)
        if candidate != raw:
            originals[ignore] = raw
            changes[ignore] = candidate
    return list(changes.items()), originals, {"migrated": sorted(legacy), "preserved_project_records": True}


def finish_migration(target, host):
    """Remove only now-empty legacy directories, never recursively delete a tree."""
    target = Path(target).resolve()
    for prefix in (".ai", "." + host + "/runtime", *([".agents/skills"] if host == "claude" else [])):
        folder = installer.destination(target, prefix)
        if not folder.exists():
            continue
        for path in sorted(folder.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if installer.linked(path):
                raise ValueError("linked legacy path appeared during migration")
            if path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    pass
        try:
            folder.rmdir()
        except OSError:
            pass


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if "--migrate-existing" not in arguments:
        arguments.append("--migrate-existing")
    return installer.main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
