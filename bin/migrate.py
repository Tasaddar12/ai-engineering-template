"""Migrate adopting-project legacy paths without replacing project planning records."""
from __future__ import annotations
import argparse
import importlib.util
from pathlib import Path
import re
import sys

_spec = importlib.util.spec_from_file_location("engineer_installer_for_migration", Path(__file__).with_name("install.py"))
installer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(installer)
ALIASES = {"coder": "executor", "phase-preparer": "planner", "phase-checker": "plan-checker", "researcher": "phase-researcher"}


def relocate_paths(value, host):
    """Relocate legacy references in data; no legacy implementation is used as source."""
    namespace = "." + host
    text = value.decode("utf-8") if isinstance(value, bytes) else value
    for old in (".ai/runtime/phase.py", namespace + "/runtime/phase.py"):
        text = text.replace(old, namespace + "/engineer/bin/engineer.py")
    for old in (".ai/runtime", namespace + "/runtime"):
        text = re.sub(re.escape(old) + r"(?=/|\b)", namespace + "/engineer/bin", text)
    for folder in ("templates", "workflows", "references", "guides", "rules"):
        text = text.replace(".ai/" + folder, namespace + "/engineer/" + folder)
    text = text.replace(".ai/RULES.md", namespace + "/engineer/RULES.md")
    for folder in ("agents", "commands", "hooks", "workers"):
        text = text.replace(".ai/" + folder, namespace + "/" + folder)
    text = re.sub(r"(?<![\w.-])\.ai/", namespace + "/", text)
    text = re.sub(r"\bphase_run\b", "engineer_run", text)
    return text.encode("utf-8") if isinstance(value, bytes) else text


def relocated_name(name, host):
    ns = "." + host
    if name.startswith(".ai/"):
        suffix = name[4:]
        if suffix.startswith("runtime/"):
            suffix = "engineer/bin/" + suffix[len("runtime/"):]
        elif suffix.startswith(("templates/", "workflows/", "references/", "guides/", "rules/")) or suffix == "RULES.md":
            suffix = "engineer/" + suffix
        if suffix.startswith("agents/") and suffix.endswith(".md"):
            role = Path(suffix).stem
            suffix = "agents/" + ALIASES.get(role, role.removeprefix("gsd-")) + ".md"
        return ns + "/" + suffix
    if name.startswith(ns + "/runtime/"):
        return ns + "/engineer/bin/" + name.split("/runtime/", 1)[1]
    return name


def legacy_inventory(target, host):
    target = Path(target).resolve()
    result = {}
    for prefix in (".ai", "." + host + "/runtime"):
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
    if not legacy:
        raise ValueError("migration requires an existing .ai directory or host runtime directory")
    other = ".claude" if host == "codex" else ".codex"
    if (target / other / "engineer/bin/engineer.py").exists():
        raise ValueError("second host installation conflicts")
    backup_root = target / ".workflow-backups"
    if backup_root.exists() and (not backup_root.is_dir() or installer.linked(backup_root)):
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
        if new_path.exists() and new_name != name:
            raise ValueError("native collision at " + new_name)
        try:
            relocated = relocate_paths(data, host)
        except UnicodeError:
            relocated = data
        if "/agents/" in new_name and new_name.endswith(".md"):
            relocated = installer.render_asset("agents/" + Path(new_name).name, relocated, host)
        # Old runtime entry points never replace the freshly authored runtime.
        if new_name in migrated:
            raise ValueError("two old paths both map to " + new_name)
        if new_name.endswith("/engineer/bin/phase.py"):
            continue
        migrated[new_name] = relocated
    for name, candidate in incoming.items():
        path = installer.destination(target, name)
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
        if name in migrated and (("/agents/" in name and name.endswith(".md")) or name.endswith("/engineer/RULES.md")):
            candidate = migrated.pop(name)
        changes[path] = candidate
    for name, data in migrated.items():
        path = installer.destination(target, name)
        if path not in changes:
            changes[path] = data
    config = installer.destination(target, ".planning/config.yaml")
    if config.is_file():
        original = config.read_bytes()
        candidate = relocate_paths(original, host)
        if candidate != original:
            originals[config] = original
            changes[config] = candidate
    return list(changes.items()), originals, {"migrated": sorted(legacy), "preserved_project_records": True}


def finish_migration(target, host):
    """Remove only now-empty legacy directories, never recursively delete a tree."""
    target = Path(target).resolve()
    for prefix in (".ai", "." + host + "/runtime"):
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
