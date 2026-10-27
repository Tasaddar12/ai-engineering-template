"""Installed provenance, pinned change inspection and exact custom-file backup."""
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
from .core import Failure, load_json, now, read, root, run, write_json


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _contained(base, value):
    base = Path(base).resolve()
    path = base/str(value)
    if not path.resolve().is_relative_to(base) or path.resolve() == base:
        raise Failure("install-path-outside-root", str(path))
    cursor = path
    while cursor != base:
        if cursor.is_symlink():
            raise Failure("linked-install-path", str(cursor))
        cursor = cursor.parent
    return path


def _bytes(path, content, mode):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix="."+path.name, dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def context(args):
    requested = args.get("config-dir")
    host = args.get("runtime", args.get("host"))
    if host and host not in ("claude", "codex"):
        raise Failure("unsupported-host", str(host), 2)
    candidates = [Path(requested).expanduser().resolve()] if requested else [root()/name for name in (".claude", ".codex")]
    if not requested:
        candidates += [Path.home()/".claude", Path(os.environ.get("CODEX_HOME", str(Path.home()/".codex")))]
    matches = []
    for namespace in dict.fromkeys(candidates):
        path = namespace/"engineer-install/manifest.json"
        if not path.is_file():
            continue
        if path.is_symlink():
            raise Failure("linked-install-manifest", str(path))
        manifest = load_json(path)
        if not isinstance(manifest, dict) or manifest.get("host") not in ("claude", "codex"):
            raise Failure("invalid-install-manifest", str(path))
        if host and manifest["host"] != host:
            continue
        matches.append((namespace, path, manifest))
    if not matches:
        return {"resolved": False, "reason": "No pinned Engineer installation was found", "candidates": list(map(str, candidates))}
    if len(matches) > 1:
        raise Failure("ambiguous-installation", "Select --config-dir and --runtime", candidates=[str(item[0]) for item in matches])
    namespace, path, manifest = matches[0]
    return {"resolved": True, "installedVersion": manifest.get("revision"), "revision": manifest.get("revision"),
            "source_path": manifest.get("source"), "source": manifest.get("source"), "scope": manifest.get("scope"),
            "runtime": manifest["host"], "host": manifest["host"], "target": str(namespace.parent),
            "config_dir": str(namespace), "gsdDir": str(namespace), "manifest": str(path),
            "complete": bool(manifest.get("complete")), "owned_files": manifest.get("files", {})}


def _require(args):
    packet = context(args)
    if not packet["resolved"]:
        raise Failure("installation-unresolved", packet["reason"])
    return packet, Path(packet["config_dir"])


def custom_files(args):
    packet, namespace = _require(args)
    owned = packet["owned_files"]
    files, snapshots = [], {}
    for path in sorted(namespace.rglob("*")):
        if path.is_symlink():
            raise Failure("linked-install-path", str(path))
        relative = path.relative_to(namespace)
        if any(part in ("engineer-install", "engineer-user-files-backup", "gsd-user-files-backup", "__pycache__", ".git") for part in relative.parts):
            continue
        if path.is_file() and (namespace.name+"/"+relative.as_posix()) not in owned:
            name = relative.as_posix()
            files.append(name)
            snapshots[name] = {"sha256": _hash(path), "mode": stat.S_IMODE(path.stat().st_mode)}
    return {"custom_files": files, "custom_count": len(files), "count": len(files), "snapshots": snapshots,
            "config_dir": str(namespace), "host": packet["host"], "revision": packet["revision"]}


def backup(args):
    packet, namespace = _require(args)
    selected = args.json("custom-json") if args.has("custom-json") else custom_files(args)
    if not isinstance(selected, dict) or not isinstance(selected.get("custom_files"), list):
        raise Failure("invalid-custom-files", "Expected the complete custom-file preview packet", 2)
    backup_dir = Path(str(args.get("backup-dir", namespace/"engineer-user-files-backup"))).resolve()
    if not backup_dir.is_relative_to(namespace.resolve()) or backup_dir == namespace.resolve():
        raise Failure("backup-outside-installation", str(backup_dir))
    entries = []
    for name in selected["custom_files"]:
        source = _contained(namespace, name)
        if not source.is_file():
            raise Failure("custom-file-drift", str(source))
        expected = selected.get("snapshots", {}).get(name)
        observed = {"sha256": _hash(source), "mode": stat.S_IMODE(source.stat().st_mode)}
        if expected is not None and expected != observed:
            raise Failure("custom-file-drift", name)
        target = _contained(backup_dir, name)
        if target.exists() and _hash(target) != observed["sha256"]:
            raise Failure("backup-conflict", "Existing backup differs: "+str(target))
        _bytes(target, source.read_bytes(), observed["mode"])
        if _hash(target) != observed["sha256"]:
            raise Failure("backup-readback", name)
        entries.append({"path": name, **observed})
    manifest = {"schema": 1, "created": now(), "config_dir": str(namespace), "host": packet["host"], "entries": entries}
    write_json(backup_dir/"manifest.json", manifest)
    return {"backed_up": len(entries), "backup_dir": str(backup_dir), "entries": entries}


def restore(args):
    _, namespace = _require(args)
    backup_dir = Path(str(args.get("backup-dir", namespace/"engineer-user-files-backup"))).resolve()
    if not backup_dir.is_relative_to(namespace.resolve()) or backup_dir == namespace.resolve():
        raise Failure("backup-outside-installation", str(backup_dir))
    manifest = load_json(backup_dir/"manifest.json", {"entries": []})
    if manifest.get("config_dir", str(namespace)) != str(namespace):
        raise Failure("backup-owner-mismatch", str(backup_dir))
    entries = []
    for entry in manifest["entries"]:
        source, destination = _contained(backup_dir, entry["path"]), _contained(namespace, entry["path"])
        current = _hash(destination)
        intact = source.is_file() and _hash(source) == entry["sha256"]
        eligible = intact and not destination.exists()
        entries.append({**entry, "current": current, "eligible": eligible,
                        "reason": "restore" if eligible else "already-present" if intact and current == entry["sha256"] else "preserved-conflict"})
    snapshot = json.dumps({"entries": entries, "owner": str(namespace), "backup": str(backup_dir)}, sort_keys=True)
    token = hashlib.sha256(snapshot.encode()).hexdigest()
    restored = []
    if args.has("apply"):
        if str(args.get("preview-token", "")) != token:
            raise Failure("restore-preview-required", "Supply the exact current --preview-token", preview_token=token)
        selection = set(args.all("select"))
        if not selection:
            raise Failure("restore-selection-required", "Select the exact previewed paths with --select", 2)
        indexed = {entry["path"]: entry for entry in entries}
        if any(name not in indexed or not indexed[name]["eligible"] for name in selection):
            raise Failure("restore-selection-invalid", "A selected path is absent or blocked")
        for name in sorted(selection):
            entry = indexed[name]
            source, destination = _contained(backup_dir, name), _contained(namespace, name)
            if destination.exists() or _hash(source) != entry["sha256"]:
                raise Failure("restore-drift", name, restored=restored)
            _bytes(destination, source.read_bytes(), entry["mode"])
            restored.append(name)
    return {"entries": entries, "eligible_count": sum(entry["eligible"] for entry in entries),
            "skipped_count": sum(not entry["eligible"] for entry in entries), "backup_dir": str(backup_dir),
            "preview_token": token, "restored": restored, "restored_count": len(restored)}


def changes(args):
    packet = context(args)
    source = Path(str(args.get("source", packet.get("source_path", "")))).expanduser().resolve()
    target = args.get("ref")
    previous = args.get("from", packet.get("revision"))
    if not target or not previous or not source.is_dir():
        raise Failure("pinned-update-required", "Select an existing --source, current --from revision and exact --ref", 2)
    old = run(["git", "rev-parse", "--verify", str(previous)+"^{commit}"], source, timeout=30).stdout.strip()
    new = run(["git", "rev-parse", "--verify", str(target)+"^{commit}"], source, timeout=30).stdout.strip()
    lines = run(["git", "log", "--format=%H%x09%s", old+".."+new], source, timeout=30).stdout.splitlines()
    entries = [{"sha": line.partition("\t")[0], "subject": line.partition("\t")[2]} for line in lines]
    return {"source": str(source), "from_revision": old, "to_revision": new, "changes": entries, "count": len(entries)}
