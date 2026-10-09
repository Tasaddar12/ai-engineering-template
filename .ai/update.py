#!/usr/bin/env python3
"""Review a pinned workflow update; dry-run is the default (Python 3.11+)."""
import argparse
import ast
import base64
import copy
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import tomllib

_spec = importlib.util.spec_from_file_location("workflow_install", Path(__file__).with_name("install.py"))
installer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(installer)


def digest(content):
    return hashlib.sha256(content).hexdigest() if content is not None else None


def destination(target, name):
    """Validate portable relative paths and every existing ancestor before use."""
    if (not isinstance(name, str) or not name or "\\" in name or ":" in name
            or PurePosixPath(name).is_absolute() or any(p in ("", ".", "..") for p in name.split("/"))
            or name.split("/")[0].lower() == ".git"):
        raise ValueError(f"Unsafe update path: {name!r}")
    path = target / name
    installer.safe_path(path)
    for parent in path.parents:
        if parent.exists() and not parent.is_dir():
            raise ValueError(f"Destination parent is not a directory: {parent}")
    if path.exists() and not path.is_file():
        raise ValueError(f"Destination is not a file: {path}")
    return path


def read(target, name):
    path = destination(target, name)
    return path.read_bytes() if path.is_file() else None


def check_target(target, host):
    installer.safe_path(target)
    target = target.resolve()
    root = installer.run("git", "rev-parse", "--show-toplevel", cwd=target, capture=True).strip()
    if Path(root).resolve() != target:
        raise ValueError("Update target must be the Git repository root")
    if (target / ".ai").exists():
        raise ValueError("Migrate the source/legacy .ai layout before using the installed updater")
    if read(target, f".{host}/runtime/phase.py") is None:
        raise ValueError(f"No installed .{host} runtime")
    other = "claude" if host == "codex" else "codex"
    if read(target, f".{other}/runtime/phase.py") is not None:
        raise ValueError("Reconcile dual workflow installations before updating")
    return target


def fetch(source, ref, checkout):
    if not isinstance(ref, str) or not ref or ref.startswith("-"):
        raise ValueError("Invalid upstream ref")
    installer.run("git", "init", "--quiet", str(checkout))
    installer.run("git", "fetch", "--quiet", "--depth=1", "--", source, ref, cwd=checkout)
    installer.run("git", "checkout", "--quiet", "--detach", "FETCH_HEAD", cwd=checkout)
    return installer.run("git", "rev-parse", "HEAD", cwd=checkout, capture=True).strip()


def load_manifest(target, host):
    raw = read(target, f".{host}/{installer.OWNERSHIP_NAME}")
    if raw is None:
        return None
    value = json.loads(raw, object_pairs_hook=installer.unique_json_object)
    if value.get("schema") != 1 or value.get("host") != host or not isinstance(value.get("files"), dict):
        raise ValueError("Unsupported ownership manifest")
    current = value.get("current", {})
    if not isinstance(current.get("source"), str) or not re.fullmatch(r"[0-9a-f]{40,64}", current.get("revision", "")):
        raise ValueError("Invalid ownership provenance")
    for name, entry in value["files"].items():
        destination(target, name)
        if not (name.startswith((f".{host}/", installer.skill_root(host) + "/"))
                or name in installer.PROJECT_RECORDS | installer.PLANNING_RESOURCES
                or name in ("AGENTS.md", "CLAUDE.md")):
            raise ValueError(f"Ownership cannot claim project code: {name}")
        if (not isinstance(entry, dict) or entry.get("classification") not in
                ("upstream-managed", "customized", "generated", "project")):
            raise ValueError(f"Invalid ownership classification: {name}")
        for key in ("installed_sha256", "upstream_sha256"):
            if entry.get(key) is not None and not re.fullmatch(r"[0-9a-f]{64}", entry[key]):
                raise ValueError(f"Invalid ownership digest: {name}")
    return value


def config_defaults(source):
    """Read the pinned runtime's literal defaults without executing upstream code."""
    path = source / ".ai/runtime/lib/config.py"
    installer.safe_path(path)
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "DEFAULTS" for t in node.targets):
            defaults = ast.literal_eval(node.value)
            if isinstance(defaults, dict):
                return defaults
    raise ValueError("Pinned runtime has no literal DEFAULTS configuration contract")


# Only these operational safety fields are materialized. Other defaults work via
# runtime fallback and are reported as optional; template examples are not schema.
REQUIRED_CONFIG_PATHS = {"workflow.isolation", "worktree.root", "handoff.context_percent",
                         "handoff.context_tokens", "verification.commands"}


def config_candidate(current, incoming, defaults):
    import yaml
    old = yaml.safe_load(current.decode("utf-8-sig")) if current else {}
    new = yaml.safe_load(incoming.decode("utf-8-sig")) or {}
    if not isinstance(old, dict) or not isinstance(new, dict):
        raise ValueError("Project configuration must be a mapping")
    result = copy.deepcopy(old)
    required, optional, conflicts = [], [], []

    def fill(node, schema, supplied, prefix=""):
        for key, default in schema.items():
            dotted = prefix + key
            if key not in node:
                if isinstance(default, dict):
                    child = {}
                    fill(child, default, supplied.get(key, {}) if isinstance(supplied, dict) else {}, dotted + ".")
                    if child:
                        node[key] = child
                elif dotted in REQUIRED_CONFIG_PATHS:
                    node[key] = copy.deepcopy(default)
                    required.append(dotted)
                else:
                    optional.append(dotted)
            elif isinstance(default, dict):
                if not isinstance(node[key], dict):
                    conflicts.append(dotted + ": expected mapping")
                else:
                    fill(node[key], default, supplied.get(key, {}) if isinstance(supplied, dict) else {}, dotted + ".")
            elif default is not None and type(node[key]) is not type(default):
                conflicts.append(dotted + ": expected " + type(default).__name__)
            elif default is None and node[key] is not None and not isinstance(node[key], str):
                conflicts.append(dotted + ": expected string or null")
            elif dotted == "workflow.isolation" and node[key] not in ("auto", "harness-worktree", "orchestrator-worktree"):
                conflicts.append(dotted + ": unsupported isolation mode")
            elif dotted == "delivery.merge_method" and node[key] not in ("squash", "merge", "rebase"):
                conflicts.append(dotted + ": unsupported merge method")
            elif dotted == "handoff.context_percent" and not 0 < node[key] <= 100:
                conflicts.append(dotted + ": expected percentage in (0, 100]")
            elif dotted in ("context_window", "handoff.context_tokens") and node[key] <= 0:
                conflicts.append(dotted + ": expected positive integer")
            elif dotted == "worktree.root" and not node[key].strip():
                conflicts.append(dotted + ": expected nonempty path")
        for key, value in supplied.items():
            if key not in schema and key not in node:
                optional.append(prefix + key)
            elif isinstance(value, dict) and isinstance(node.get(key), dict) and key not in schema:
                fill(node[key], {}, value, prefix + key + ".")
    fill(result, defaults, new)
    # No formatting-only writes; comments survive when no required fields are missing.
    content = (yaml.safe_dump(result, sort_keys=False, allow_unicode=True).encode()
               if required else current)
    return content, required, sorted(set(optional)), conflicts


def managed_block(content):
    if content is None:
        return None
    start, end = installer.AGENT_MARKER.encode(), installer.AGENT_END.encode()
    if content.count(start) != 1 or content.count(end) != 1 or content.index(end) < content.index(start):
        raise ValueError("Entry file needs exactly one ordered managed block")
    first, last = content.index(start), content.index(end) + len(end)
    return first, last, content[first:last].replace(b"\r\n", b"\n")


def content_diff(name, current, candidate):
    def lines(data):
        return (data or b"").decode("utf-8", errors="replace").splitlines(keepends=True)
    return "".join(difflib.unified_diff(lines(current), lines(candidate),
                                         fromfile=name + " (installed)", tofile=name + " (candidate)"))


def inventory(target, roots):
    names = set()
    for root_name in roots:
        root = target / root_name
        installer.safe_path(root)
        if not root.exists():
            continue
        pending = [root]
        while pending:
            directory = pending.pop()
            for path in sorted(directory.iterdir()):
                installer.safe_path(path)
                if path.name == "__pycache__" or path.suffix == ".pyc" or path.name.startswith("settings.local."):
                    continue
                if path.is_dir():
                    pending.append(path)
                elif path.is_file():
                    names.add(path.relative_to(target).as_posix())
                else:
                    raise ValueError(f"Unsupported installed entry: {path}")
    return names


def build_plan(source, target, host, hooks, source_url, revision, baseline=None, baseline_source=None):
    """Pure comparison: ownership is evidence, never a version-stamp shortcut."""
    manifest = load_manifest(target, host)
    incoming = installer.payload(source, host, hooks)
    prior = installer.payload(baseline, host, hooks) if baseline else {}
    manifest_name = f".{host}/{installer.OWNERSHIP_NAME}"
    names = set(incoming) | set(manifest["files"] if manifest else {})
    names |= inventory(target, (f".{host}", installer.skill_root(host))) - {manifest_name}
    entries = []
    for name in sorted(names):
        current = read(target, name)
        candidate = incoming.get(name)
        record = (manifest or {}).get("files", {}).get(name, {})
        known = record.get("installed_sha256") == digest(current) and current is not None
        classification = ("project" if name in installer.PROJECT_RECORDS else
                          "generated" if name in ("AGENTS.md", "CLAUDE.md", ".codex/config.toml", ".claude/settings.json") else
                          record.get("classification", "unproven"))
        if classification == "unproven" and name not in incoming:
            classification = "project"
        conflict, required, optional = None, [], []
        action = "keep"
        if name == ".planning/config.yaml":
            try:
                candidate, required, optional, errors = config_candidate(current, candidate, config_defaults(source))
                conflict = "; ".join(errors) or None
                action = "write" if candidate != current else "keep"
            except (ValueError, UnicodeError) as error:
                conflict = str(error)
                candidate = current
        elif classification == "project":
            candidate = current  # Never recreate missing intent or planning records during update.
        elif classification == "generated" and candidate is not None:
            try:
                if current is None:
                    action = "write"
                elif name in ("AGENTS.md", "CLAUDE.md"):
                    block = managed_block(current)
                    old = managed_block(prior.get(name)) if prior.get(name) else None
                    # Installed hashes also record deliberately kept customizations;
                    # they cannot prove that this managed block belongs to upstream.
                    # Compare the block with the actual pinned baseline independently
                    # of surrounding project guidance and whole-file manifest matches.
                    if old is None or block[2] != old[2]:
                        conflict = "Customized or unproven managed instruction block"
                    candidate = current[:block[0]] + managed_block(candidate)[2] + current[block[1]:]
                    action = "write" if candidate != current else "keep"
                elif name.endswith(".toml"):
                    candidate = installer.merge_codex_config(current, candidate, name, preserve_agents=True)
                    action = "write" if candidate != current else "keep"
                else:
                    candidate = installer.merge_hooks(current, candidate, name)
                    action = "write" if candidate != current else "keep"
            except (ValueError, UnicodeError) as error:
                conflict, candidate = str(error), current
        elif candidate is None:
            # Retirement is reported but never automatically deletes project additions.
            if current is not None and classification == "upstream-managed" and known:
                conflict = "Retired upstream file; review keep or remove"
        elif current == candidate:
            if classification == "unproven":
                conflict = "Content matches upstream but ownership is unproven; classify and review"
        elif current is None:
            action = "write"
            classification = "upstream-managed"
        elif classification == "upstream-managed" and known:
            action = "write"
        else:
            classification = "customized" if record else "unproven"
            action = "write"
            conflict = "Local customization" if record else "Ownership unproven; reviewed classification required"
        entries.append({"path": name, "classification": classification, "action": action,
                        "before_sha256": digest(current), "candidate_sha256": digest(candidate),
                        "upstream_sha256": digest(incoming.get(name)),
                        "candidate_base64": base64.b64encode(candidate).decode() if candidate is not None else None,
                        "diff": content_diff(name, current, candidate), "conflict": conflict,
                        "required_config": required, "optional_defaults": optional})
    return {"schema": 1, "target": str(target), "host": host, "hooks": hooks,
            "source": source_url, "revision": revision,
            "previous": manifest.get("current") if manifest else None,
            "baseline_revision": installer.run("git", "rev-parse", "HEAD", cwd=baseline, capture=True).strip() if baseline else None,
            "baseline_source": (baseline_source or source_url) if baseline else None,
            "manifest_sha256": digest(read(target, manifest_name)), "entries": entries, "resolutions": {}}


def apply_plan(plan, source, baseline=None):
    """Recompute all candidates and fingerprints before backing up or mutating."""
    target = check_target(Path(plan["target"]), plan["host"])
    fresh = build_plan(source, target, plan["host"], plan["hooks"], plan["source"], plan["revision"], baseline, plan["baseline_source"])
    expected = dict(plan, resolutions={})
    if fresh != expected:
        raise ValueError("Reviewed plan is stale or candidates changed; generate and review a new plan")
    resolutions = plan.get("resolutions", {})
    if set(resolutions) - {e["path"] for e in plan["entries"]}:
        raise ValueError("Resolution names an unplanned file")
    writes, files = [], {}
    old = load_manifest(target, plan["host"])
    for entry in plan["entries"]:
        name = entry["path"]
        choice = resolutions.get(name, {})
        action = choice.get("action", entry["action"])
        classification = choice.get("classification", entry["classification"])
        if name == ".planning/config.yaml" and entry["conflict"]:
            raise ValueError(f"Reconcile invalid project configuration before updating: {entry['conflict']}")
        if entry["conflict"] and not choice:
            raise ValueError(f"Unresolved conflict: {name}: {entry['conflict']}")
        if classification not in ("upstream-managed", "customized", "generated", "project"):
            raise ValueError(f"Reviewed classification required for {name}")
        if action not in ("keep", "write", "remove"):
            raise ValueError(f"Invalid resolution action for {name}")
        # Project and mixed/generated files cannot be reclassified to bypass guards.
        if entry["classification"] in ("project", "generated") and classification != entry["classification"]:
            raise ValueError(f"Cannot reclassify protected file: {name}")
        if classification == "project" and (name != ".planning/config.yaml" or entry["conflict"]):
            if action != "keep":
                raise ValueError(f"Project file must be preserved: {name}")
        if classification == "generated" and entry["conflict"] and action != "keep":
            raise ValueError(f"Reconcile generated-file conflict before replanning: {name}")
        content = read(target, name)
        if action == "write":
            if entry["candidate_base64"] is None:
                raise ValueError(f"No candidate content: {name}")
            content = base64.b64decode(entry["candidate_base64"], validate=True)
            if digest(content) != entry["candidate_sha256"]:
                raise ValueError(f"Candidate hash mismatch: {name}")
            writes.append((destination(target, name), content))
        elif action == "remove":
            if classification not in ("upstream-managed", "customized") or entry["upstream_sha256"] is not None:
                raise ValueError(f"Only reviewed retired workflow files can be removed: {name}")
            content = None
            writes.append((destination(target, name), None))
        if content is not None:
            # Keeping local changes must never relabel them as clean upstream bytes.
            if classification == "upstream-managed" and digest(content) != entry["upstream_sha256"]:
                classification = "customized"
            files[name] = {"classification": classification, "installed_sha256": digest(content),
                           "upstream_sha256": entry["upstream_sha256"]}
    provenance = {"source": plan["source"], "revision": plan["revision"]}
    manifest = {"schema": 1, "host": plan["host"], "hooks": plan["hooks"], "current": provenance,
                "previous": old.get("previous") if old and old["current"] == provenance else plan["previous"],
                "files": files}
    manifest_path = destination(target, f".{plan['host']}/{installer.OWNERSHIP_NAME}")
    writes.append((manifest_path, installer.json_bytes(manifest)))
    changed = [(p, data) for p, data in writes if (p.read_bytes() if p.is_file() else None) != data]
    if not changed:
        return []
    backup = installer.backup_migration(target, [p for p, _ in changed if p.is_file()])
    # Recheck every read fingerprint after backup (not just files being written).
    for entry in plan["entries"]:
        if digest(read(target, entry["path"])) != entry["before_sha256"]:
            raise ValueError("Installed files changed during backup; update stopped")
    if digest(read(target, manifest_path.relative_to(target).as_posix())) != plan["manifest_sha256"]:
        raise ValueError("Ownership manifest changed during backup")
    for path, content in changed:
        installer.safe_path(path)
        if content is None:
            path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    for name, record in files.items():
        if digest(read(target, name)) != record["installed_sha256"]:
            raise ValueError(f"Installed result hash validation failed: {name}; originals at {backup}")
    # Syntax validation is separate from independent runtime/project behavioral checks.
    import yaml
    if not isinstance(yaml.safe_load(read(target, ".planning/config.yaml")), dict):
        raise ValueError("Installed configuration validation failed")
    for name in (".codex/config.toml", ".claude/settings.json"):
        content = read(target, name)
        if content is not None:
            (tomllib.loads(content.decode("utf-8-sig")) if name.endswith("toml") else json.loads(content))
    return [p.relative_to(target).as_posix() for p, _ in changed]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default=".")
    parser.add_argument("--source", default=installer.SOURCE)
    parser.add_argument("--ref", default="main")
    parser.add_argument("--host", choices=("codex", "claude"), default="claude" if Path(__file__).parent.name == ".claude" else "codex")
    parser.add_argument("--no-hooks", action="store_true")
    parser.add_argument("--from-ref", help="Explicit legacy content baseline; ownership still requires review")
    parser.add_argument("--plan", help="Save dry-run JSON to this path outside installed workflow roots")
    parser.add_argument("--apply", metavar="PLAN", help="Apply a saved reviewed plan")
    parser.add_argument("--reviewed-plan-sha256", help="SHA256 of the entire reviewed plan file, including resolutions")
    args = parser.parse_args(argv)
    try:
        with tempfile.TemporaryDirectory(prefix="workflow-update-") as temp:
            source, baseline = Path(temp) / "source", None
            if args.apply:
                if args.plan or args.from_ref or args.no_hooks:
                    raise ValueError("Apply uses saved source/host/options; do not combine planning options")
                raw = Path(args.apply).read_bytes()
                if digest(raw) != args.reviewed_plan_sha256:
                    raise ValueError("--apply requires the exact --reviewed-plan-sha256")
                plan = json.loads(raw, object_pairs_hook=installer.unique_json_object)
                revision = fetch(plan["source"], plan["revision"], source)
                if revision != plan["revision"]:
                    raise ValueError("Pinned revision changed")
                if plan["baseline_revision"]:
                    baseline = Path(temp) / "baseline"
                    fetch(plan["baseline_source"], plan["baseline_revision"], baseline)
                print(json.dumps({"revision": revision, "changed": apply_plan(plan, source, baseline)}, indent=2))
            else:
                target = check_target(Path(os.path.abspath(args.target)), args.host)
                revision = fetch(args.source, args.ref, source)
                manifest = load_manifest(target, args.host)
                previous_ref = args.from_ref or (manifest or {}).get("current", {}).get("revision")
                previous_source = args.source if args.from_ref else (manifest or {}).get("current", {}).get("source", args.source)
                if previous_ref:
                    baseline = Path(temp) / "baseline"
                    fetch(previous_source, previous_ref, baseline)
                plan = build_plan(source, target, args.host, not args.no_hooks, args.source, revision, baseline, previous_source)
                if args.plan:
                    output = Path(os.path.abspath(args.plan))
                    installer.safe_path(output)
                    if output.is_relative_to(target) and output.relative_to(target).parts[0] in (".codex", ".claude", ".agents", ".planning", ".ai", ".git"):
                        raise ValueError("Save review plans outside workflow and project-record roots")
                    output.write_bytes(installer.json_bytes(plan))
                    print(f"Review plan: {output}\nSHA256: {digest(output.read_bytes())}")
                print(f"Pinned upstream: {revision}; previous: {plan['previous']}")
                for entry in plan["entries"]:
                    if entry["diff"] or entry["conflict"] or entry["optional_defaults"]:
                        print(f"{entry['classification']} {entry['action']} {entry['path']}: {entry['conflict'] or 'ready'}")
                        print(entry["diff"], end="")
                        if entry["optional_defaults"]:
                            print("Optional defaults (not applied): " + ", ".join(entry["optional_defaults"]))
                print("Dry-run only. Review conflicts/resolutions and candidate diffs before --apply.")
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(f"Update failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
