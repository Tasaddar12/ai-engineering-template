"""Installed provenance and pinned update change inspection."""
import os
from pathlib import Path
from .core import Failure, load_json, root, run


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
            "config_dir": str(namespace), "manifest": str(path),
            "complete": bool(manifest.get("complete")), "owned_files": manifest.get("files", {})}


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
