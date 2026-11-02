"""Explicit, recoverable planning archival with content-bound provenance."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
import shutil
import uuid
from .core import Failure, load_json, now, planning_lock, read, root, slug, write_json
from .planning import safe


def _inventory(directory):
    directory = safe(directory)
    result = {}
    if not directory.is_dir():
        raise Failure("archive-source-missing", str(directory))
    for path in sorted(directory.rglob("*")):
        safe(path)
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        elif not path.is_dir():
            raise Failure("unsupported-archive-entry", str(path))
    return result


def _directory(args):
    identifier = args.arg(0, args.get("id"))
    if not isinstance(identifier, str) or not identifier or not all(character.isalnum() or character in "-_." for character in identifier) or identifier in (".", ".."):
        raise Failure("invalid-archive-id", str(identifier), 2)
    path = safe(root()/".planning/archive/operations"/identifier)
    manifest = load_json(safe(path/"manifest.json"))
    if not isinstance(manifest, dict) or manifest.get("id") != identifier:
        raise Failure("archive-not-found", identifier)
    return path, manifest


def capture(args):
    scope = args.get("scope", "phases")
    if scope not in ("phases", "quick", "phase"):
        raise Failure("invalid-archive-scope", str(scope), 2)
    label = args.arg(0, args.get("milestone"))
    if not isinstance(label, str) or not label.strip():
        raise Failure("missing-archive-label", "Provide a milestone or archive label", 2)
    base = safe(root()/".planning")
    if scope == "phase":
        from . import records
        if not args.has("phase"):
            raise Failure("missing-phase", "Single-phase archival requires --phase", 2)
        source = safe(records.phase_dir(args.get("phase")))
    else:
        source = safe(base/scope)
    if not args.has("confirm"):
        inventory = _inventory(source)
        return {"preview": True, "scope": scope, "label": label, "source": str(source), "files": inventory,
                "approval_required": True, "count": len(inventory)}
    with planning_lock():
        identifier = args.get("id", now()[:10]+"-"+slug(label)+"-"+uuid.uuid4().hex[:10])
        if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,150}", identifier):
            raise Failure("invalid-archive-id", str(identifier), 2)
        destination = safe(base/"archive/operations"/identifier)
        payload = safe(destination/"payload")
        if destination.exists():
            manifest = load_json(safe(destination/"manifest.json"))
            if not isinstance(manifest, dict) or manifest.get("id") != identifier or manifest.get("source") != str(source.relative_to(root())) or manifest.get("label") != label or manifest.get("scope") != scope:
                raise Failure("archive-collision", str(destination))
            expected = manifest.get("files")
            if not isinstance(expected, dict) or _inventory(payload) != expected:
                raise Failure("archive-content-drift", "Retained archive bytes do not match the manifest", archive_id=identifier)
            retired = safe(destination/"retired")
            if manifest.get("state") == "prepared":
                if retired.exists():
                    if _inventory(retired) != expected or source.exists() and any(source.iterdir()):
                        raise Failure("archive-resume-conflict", identifier)
                elif source.exists() and _inventory(source) == expected:
                    source.rename(retired)
                else:
                    raise Failure("archive-resume-conflict", identifier)
                if scope != "phase" and not source.exists():
                    source.mkdir()
                manifest["state"], manifest["completed"] = "archived", now()
                write_json(destination/"manifest.json", manifest)
            if manifest.get("state") != "archived" or source.exists() and any(source.iterdir()):
                raise Failure("archive-resume-conflict", identifier)
            return {"archived": True, "duplicate": True, "id": identifier, "archive_id": identifier,
                    "path": str(destination), "scope": scope, "label": label, "source": str(source), "file_count": len(expected), "provenance": manifest}
        inventory = _inventory(source)
        destination.mkdir(parents=True)
        manifest = {"schema": 1, "id": identifier, "label": label, "scope": scope,
                    "source": str(source.relative_to(root())), "created": now(), "state": "prepared", "files": inventory}
        write_json(destination/"manifest.json", manifest)
        # Copy first, verify both source and copy, then rename the source atomically.
        shutil.copytree(source, payload)
        if _inventory(source) != inventory or _inventory(payload) != inventory:
            raise Failure("archive-source-drift", "Archive inputs changed; source and prepared recovery copy are preserved", archive_id=identifier)
        retired = safe(destination/"retired")
        source.rename(retired)
        if scope != "phase":
            source.mkdir()
        manifest["state"], manifest["completed"] = "archived", now()
        write_json(destination/"manifest.json", manifest)
    return {"archived": True, "id": identifier, "archive_id": identifier, "label": label, "scope": scope,
            "path": str(destination), "source": str(source), "file_count": len(inventory), "provenance": manifest}


def recover(args):
    path, manifest = _directory(args)
    source = safe(root()/manifest["source"])
    allowed = {root()/".planning/phases", root()/".planning/quick"}
    single_phase = manifest.get("scope") == "phase" and source.parent == root()/".planning/phases" and bool(re.fullmatch(r"\d+(?:\.\d+)?-.+", source.name))
    if not single_phase and (source not in allowed or manifest.get("scope") != source.name):
        raise Failure("invalid-archive-source", str(source))
    payload = safe(path/"payload")
    inventory = manifest.get("files")
    if not isinstance(inventory, dict) or _inventory(payload) != inventory:
        raise Failure("archive-content-drift", "Archived bytes differ from provenance")
    if manifest.get("state") == "recovered":
        if source.is_dir() and _inventory(source) == inventory:
            return {"recovered": False, "duplicate": True, "id": manifest["id"], "source": str(source)}
        raise Failure("archive-recovery-drift", "Previously restored destination has changed")
    if not args.has("confirm"):
        return {"preview": True, "id": manifest["id"], "destination": str(source), "files": inventory, "approval_required": True}
    with planning_lock():
        _, current = _directory(args)
        if current != manifest or _inventory(payload) != inventory:
            raise Failure("archive-content-drift", "Archive changed before recovery")
        if source.exists() and any(source.iterdir()):
            raise Failure("archive-recovery-conflict", "Recovery never overwrites active planning records")
        temporary = safe(source.parent/(".restore-"+manifest["id"]))
        if temporary.exists():
            raise Failure("archive-recovery-conflict", str(temporary))
        shutil.copytree(payload, temporary)
        if _inventory(temporary) != inventory:
            raise Failure("archive-recovery-copy-failed", str(temporary))
        if source.exists():
            source.rmdir()
        temporary.rename(source)
        manifest["state"], manifest["recovered"] = "recovered", now()
        write_json(path/"manifest.json", manifest)
    return {"recovered": True, "id": manifest["id"], "source": str(source), "provenance_preserved": True}


def list_archives(args):
    directory = safe(root()/".planning/archive/operations")
    items = []
    for path in sorted(directory.glob("*/manifest.json")):
        safe(path)
        manifest = load_json(path)
        if not isinstance(manifest, dict):
            raise Failure("invalid-archive-manifest", str(path))
        items.append({**manifest, "path": str(path.parent)})
    return {"archives": items, "count": len(items)}


def command(args, action):
    if action in ("capture", "archive", "preview"):
        if action == "preview" and args.has("confirm"):
            raise Failure("invalid-archive-preview", "Preview cannot include --confirm", 2)
        return capture(args)
    if action in ("recover", "restore"):
        return recover(args)
    if action == "list":
        return list_archives(args)
    raise Failure("unsupported-archive-action", action, 2)
