"""Preview and apply pinned workflow updates with explicit reviewed-byte guards."""
from __future__ import annotations
import argparse
import base64
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

_spec = importlib.util.spec_from_file_location("engineer_installer_for_update", Path(__file__).with_name("install.py"))
installer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(installer)
SCHEMA = 2
PROTECTED_ROOTS = ("engineer", "hooks", "skills", "agents", "commands", "scripts", "bin")
digest = installer.digest
fetch = installer.fetch
inventory = installer.inventory
same_text = installer.same_text


def compare_content(current, candidate):
    if current == candidate:
        return "unchanged"
    if current is None:
        return "added"
    if candidate is None:
        return "retired"
    return "line-ending-only" if same_text(current, candidate) else "substantive"


def destination(target, name):
    allowed = name in ("AGENTS.md", "CLAUDE.md", ".gitignore") or name.startswith((".claude/", ".codex/", ".agents/skills/"))
    if not allowed:
        raise ValueError("project code is outside workflow ownership: " + str(name))
    return installer.destination(target, name)


def manifest_path(target, host):
    return installer.destination(target, "." + host + "/workflow-ownership.json")


def load_manifest(target, host):
    path = manifest_path(target, host)
    if not path.exists():
        return {"schema": 1, "host": host, "files": {}, "current": {}}
    value = json.loads(path.read_bytes())
    if value.get("host") != host or not isinstance(value.get("files"), dict):
        raise ValueError("invalid workflow ownership manifest")
    for name, record in value["files"].items():
        destination(target, name)
        if record.get("classification") not in ("upstream-managed", "customized", "unproven"):
            raise ValueError("Invalid ownership classification: " + name)
    return value


def record_install(target, host, source, revision, incoming, preexisting=()):
    existing = load_manifest(target, host)
    files = {}
    for name, upstream in incoming.items():
        if name.startswith(".planning/"):
            continue
        path = destination(target, name)
        if path.is_file():
            content = path.read_bytes()
            # A preexisting equal file is not evidence of installer ownership.
            prior = existing.get("files", {}).get(name)
            classification = prior.get("classification", "customized") if prior else "customized" if name in preexisting else "upstream-managed"
            if prior and prior.get("installed_sha256") != digest(content):
                classification = "customized"
            if content != upstream and name not in ("AGENTS.md", "CLAUDE.md", ".gitignore", ".codex/config.toml", ".claude/settings.json"):
                classification = "customized"
            files[name] = {"installed_sha256": digest(content), "upstream_sha256": digest(upstream), "classification": classification}
    manifest = {"schema": 1, "host": host, "current": {"source": str(source), "revision": revision}, "files": files}
    path = manifest_path(target, host)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(installer.json_bytes(manifest))


def encoded(data):
    return base64.b64encode(data).decode() if data is not None else None


def tree_digest(root):
    return digest(installer.json_bytes({name: digest(data) for name, data in inventory(root).items()})) if root else None


def text_diff(name, before, candidate):
    try:
        a = (before or b"").decode("utf-8").splitlines(keepends=True)
        b = (candidate or b"").decode("utf-8").splitlines(keepends=True)
        if any("\x00" in line for line in a + b):
            return "Binary content changed"
        return "".join(difflib.unified_diff(a, b, fromfile=name + " (installed)", tofile=name + " (candidate)"))
    except UnicodeError:
        return "Binary content changed"


def build_plan(source, target, host="codex", hooks=True, source_url=None, revision=None, baseline=None):
    target = Path(target).resolve()
    source = Path(source).resolve()
    installer.skill_root(host)
    if (target / ".ai").exists():
        raise ValueError("legacy .ai installation must migrate first")
    if not (target / ("." + host) / "engineer/bin/engineer.py").is_file():
        raise ValueError("update requires an existing installation")
    other = "claude" if host == "codex" else "codex"
    if (target / ("." + other) / "engineer/bin/engineer.py").exists():
        raise ValueError("second host installation conflicts")
    manifest_file = manifest_path(target, host)
    manifest_raw = manifest_file.read_bytes() if manifest_file.exists() else None
    manifest = load_manifest(target, host)
    incoming = {name: data for name, data in installer.payload(source, host, hooks).items() if not name.startswith(".planning/")}
    base_payload = installer.payload(baseline, host, hooks) if baseline else {}
    owned = manifest["files"]
    entries = []
    for name in sorted(incoming.keys() | owned.keys()):
        path = destination(target, name)
        before = path.read_bytes() if path.is_file() else None
        upstream = incoming.get(name)
        record = owned.get(name, {})
        known = record.get("classification", "unproven")
        unchanged = digest(before) == record.get("installed_sha256") and bool(record)
        classification = known if unchanged else "customized" if record else "unproven"
        candidate = upstream
        if before is not None and upstream is not None and name in ("AGENTS.md", "CLAUDE.md", ".gitignore", ".codex/config.toml", ".claude/settings.json"):
            candidate = installer.merge_file(name, before, upstream, host, hooks)
            if name in ("AGENTS.md", "CLAUDE.md") and base_payload.get(name):
                # Surrounding user instructions never turn the managed block into a conflict.
                current_block = installer.managed_block(installer.utf8(before, name))
                old_block = installer.managed_block(installer.utf8(base_payload[name], name))
                if current_block == old_block and known != "customized":
                    classification = "upstream-managed"
                    unchanged = True
            elif name in (".gitignore", ".codex/config.toml", ".claude/settings.json"):
                classification = "upstream-managed"
                unchanged = True
        comparison = compare_content(before, candidate)
        conflict = comparison != "unchanged" and (classification != "upstream-managed" or upstream is None)
        # Retired files require an explicit reviewed deletion; never prune user files implicitly.
        action = "keep" if upstream is None or conflict or comparison == "unchanged" else "write"
        entries.append({"path": name, "classification": classification, "conflict": conflict,
                        "action": action, "comparison": comparison, "candidate_comparison": compare_content(before, upstream),
                        "before_sha256": digest(before), "candidate_sha256": digest(candidate),
                        "upstream_sha256": digest(upstream), "candidate_base64": encoded(candidate),
                        "diff": text_diff(name, before, candidate)})
    return {"schema": SCHEMA, "target": str(target), "host": host, "hooks": hooks,
            "source": str(source_url or source), "revision": revision,
            "baseline": manifest.get("current", {}), "source_inventory_sha256": tree_digest(source),
            "baseline_inventory_sha256": tree_digest(baseline), "manifest_sha256": digest(manifest_raw),
            "entries": entries, "resolutions": {}}


def apply_plan(plan, source, baseline=None):
    if plan.get("schema") != SCHEMA:
        raise ValueError("unsupported schema; create a new plan")
    expected = build_plan(source, plan["target"], plan["host"], plan["hooks"], plan["source"], plan["revision"], baseline)
    reviewed = dict(plan)
    resolutions = reviewed.pop("resolutions", {})
    rebuilt = dict(expected)
    rebuilt.pop("resolutions")
    if reviewed != rebuilt:
        raise ValueError("stale or tampered review plan; create a new plan")
    changes, originals = [], {}
    allowed = {entry["path"] for entry in plan["entries"]}
    if set(resolutions) - allowed:
        raise ValueError("resolution names a path outside the reviewed plan")
    for entry in plan["entries"]:
        resolution = resolutions.get(entry["path"], {})
        if entry["conflict"] and not resolution:
            raise ValueError("conflict requires reviewed resolution: " + entry["path"])
        action = resolution.get("action", entry["action"])
        classification = resolution.get("classification", entry["classification"])
        if action == "remove":
            action = "delete"
        if action not in ("write", "keep", "delete") or classification not in ("upstream-managed", "customized", "unproven"):
            raise ValueError("invalid resolution for " + entry["path"])
        if action == "write" and entry["candidate_base64"] is None:
            raise ValueError("retired path has no write candidate")
        if action == "delete" and entry["candidate_base64"] is not None:
            raise ValueError("cannot delete a live candidate")
        path = destination(plan["target"], entry["path"])
        before = path.read_bytes() if path.is_file() else None
        if digest(before) != entry["before_sha256"]:
            raise ValueError("stale installed bytes: " + entry["path"])
        candidate = base64.b64decode(entry["candidate_base64"], validate=True) if action == "write" else None
        if action == "delete" or action == "write" and candidate != before:
            changes.append((path, candidate))
            if before is not None:
                originals[path] = before
    # Complete every guard before backups or source mutations.
    if originals:
        installer.backup_migration(plan["target"], originals)
    if tree_digest(source) != plan["source_inventory_sha256"] or tree_digest(baseline) != plan["baseline_inventory_sha256"]:
        raise ValueError("Source inputs changed during backup")
    current_manifest = manifest_path(plan["target"], plan["host"])
    if digest(current_manifest.read_bytes() if current_manifest.exists() else None) != plan["manifest_sha256"]:
        raise ValueError("manifest changed during backup")
    for entry in plan["entries"]:
        path = destination(plan["target"], entry["path"])
        if digest(path.read_bytes() if path.is_file() else None) != entry["before_sha256"]:
            raise ValueError("installed bytes changed during backup: " + entry["path"])
    installer.write_changes(plan["target"], changes)
    manifest = load_manifest(plan["target"], plan["host"])
    manifest["current"] = {"source": plan["source"], "revision": plan["revision"]}
    for entry in plan["entries"]:
        resolution = resolutions.get(entry["path"], {})
        action = resolution.get("action", entry["action"])
        if action in ("delete", "remove"):
            manifest["files"].pop(entry["path"], None)
            continue
        path = destination(plan["target"], entry["path"])
        if path.is_file():
            classification = resolution.get("classification", entry["classification"])
            if action == "keep" and entry["conflict"]:
                classification = "customized"
            manifest["files"][entry["path"]] = {"classification": classification,
                "installed_sha256": digest(path.read_bytes()), "upstream_sha256": entry["upstream_sha256"]}
    manifest_path(plan["target"], plan["host"]).write_bytes(installer.json_bytes(manifest))
    return [str(path) for path, _ in changes]


def plan_update(source, target, host, hooks, installer_module=None, baseline=None, prune=False, previous=None):
    """Compatibility planner; expose proposed writes but never apply unreviewed conflicts."""
    plan = build_plan(source, target, host, hooks, str(source), None, baseline or previous)
    changes, originals = [], {}
    report = {"plan": plan, "conflicts": [], "orphans": [], "customizations": [], "unproven": []}
    for entry in plan["entries"]:
        name = entry["path"]
        path = destination(target, name)
        if entry["comparison"] == "retired":
            report["orphans"].append(name)
        if entry["conflict"]:
            report["conflicts"].append(name)
            report["customizations" if entry["classification"] == "customized" else "unproven"].append(name)
            continue
        if entry["action"] == "write":
            changes.append((path, base64.b64decode(entry["candidate_base64"])))
            if path.is_file():
                originals[path] = path.read_bytes()
    return changes, originals, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target")
    parser.add_argument("--source")
    parser.add_argument("--ref")
    parser.add_argument("--host", choices=installer.HOSTS, default="codex")
    parser.add_argument("--no-hooks", action="store_true")
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--apply", type=Path)
    parser.add_argument("--reviewed-plan-sha256")
    args = parser.parse_args(argv)
    try:
        if args.apply:
            raw = args.apply.read_bytes()
            if not args.reviewed_plan_sha256 or digest(raw) != args.reviewed_plan_sha256:
                raise ValueError("--reviewed-plan-sha256 must match the exact reviewed plan bytes")
            plan = json.loads(raw)
            with tempfile.TemporaryDirectory(prefix="engineer-update-") as temp:
                source = Path(temp) / "source"
                resolved = fetch(plan["source"], plan["revision"], source)
                if resolved != plan["revision"]:
                    raise ValueError("reviewed source revision is not pinned")
                old = plan.get("baseline", {})
                baseline = None
                if old.get("source") and old.get("revision"):
                    baseline = Path(temp) / "baseline"
                    fetch(old["source"], old["revision"], baseline)
                changed = apply_plan(plan, source, baseline)
                print("Applied " + str(len(changed)) + " reviewed changes")
        else:
            if not args.target or not args.source or not args.ref:
                raise ValueError("preview requires --target, --source and pinned --ref")
            with tempfile.TemporaryDirectory(prefix="engineer-update-") as temp:
                source = Path(temp) / "source"
                revision = fetch(args.source, args.ref, source)
                manifest = load_manifest(args.target, args.host)
                old = manifest.get("current", {})
                baseline = None
                if old.get("source") and old.get("revision"):
                    baseline = Path(temp) / "baseline"
                    fetch(old["source"], old["revision"], baseline)
                plan = build_plan(source, args.target, args.host, not args.no_hooks, args.source, revision, baseline)
                for entry in plan["entries"]:
                    print(entry["comparison"] + " " + entry["classification"] + " " + entry["path"])
                    if entry["comparison"] == "substantive":
                        print(entry["diff"])
                if args.plan:
                    args.plan.write_bytes(installer.json_bytes(plan))
                    print("Plan SHA256: " + digest(args.plan.read_bytes()))
                else:
                    print(json.dumps(plan, indent=2))
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
