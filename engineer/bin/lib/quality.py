"""Cross-phase defect ledger with explicit, cited dispositions."""
import hashlib
import json
import re
from . import records
from .core import Failure, load_json, now, planning_lock, read, root, run, safe_path, write_json

KINDS = ("stub", "todo", "fixme", "skipped-test", "lint-warning", "unmet-truth", "unrun-verify", "deviation")


def _revision():
    return run(["git", "rev-parse", "HEAD"], root()).stdout.strip()


def _load():
    path = records.planning()/"windows.json"
    if not path.is_file() and (records.planning()/"WINDOWS.md").is_file():
        raise Failure("windows-legacy-ledger", "Existing WINDOWS.md must be explicitly reconciled before using a new JSON ledger")
    packet = load_json(path, {"version": 1, "entries": []})
    if not isinstance(packet, dict) or packet.get("version") != 1 or not isinstance(packet.get("entries"), list):
        raise Failure("windows-invalid-ledger", str(path))
    seen = set()
    for item in packet["entries"]:
        if not isinstance(item, dict) or not re.fullmatch(r"W-[a-f0-9]{16}", str(item.get("id", ""))) or item.get("status") not in ("open", "fixed", "waived") or item["id"] in seen:
            raise Failure("windows-invalid-ledger", "Malformed, duplicated or untyped ledger entry")
        seen.add(item["id"])
    return path, packet


def command(args, action):
    if action == "status":
        path, ledger = _load()
        count = sum(item["status"] == "open" for item in ledger["entries"])
        return {"ledger": {**ledger, "open_count": count}, "open_count": count, "path": str(path), "block": count > 0}
    if action not in ("append", "fixed", "waive"):
        raise Failure("unknown-windows-action", action, 2)
    revision = _revision()
    with planning_lock():
        path, ledger = _load()
        if action == "append":
            kind = args.get("kind")
            description = str(args.get("description", "")).strip()
            if kind not in KINDS or not description:
                raise Failure("invalid-window", "Defect needs a supported kind and concrete description", 2)
            source = safe_path(args.get("file", ""))
            if source == root():
                raise Failure("window-source-required", "Supply the actual defect source file", 2)
            line = int(args.get("line", 1))
            if line < 1:
                raise Failure("invalid-window-line", "Line must be positive", 2)
            identity = {"kind": kind, "file": str(source.relative_to(root())), "line": line,
                        "phase": args.get("phase"), "description": description}
            fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
            identifier = "W-"+fingerprint[:16]
            existing = next((item for item in ledger["entries"] if item["id"] == identifier), None)
            if existing and existing.get("fingerprint") != fingerprint:
                raise Failure("window-id-collision", identifier)
            if existing:
                if existing["status"] != "open":
                    raise Failure("window-already-dispositioned", "A recurrence requires a distinct concrete occurrence; disposition is never silently reversed", id=identifier)
                existing["last_observed_revision"] = revision
                existing["last_observed"] = now()
                item = existing
            else:
                item = {**identity, "id": identifier, "fingerprint": fingerprint, "status": "open", "created": now(),
                        "revision": revision, "source_exists": source.is_file(), "history": []}
                ledger["entries"].append(item)
        else:
            identifier = args.need()
            item = next((item for item in ledger["entries"] if item["id"] == identifier), None)
            if not item:
                raise Failure("window-not-found", identifier)
            if item["status"] != "open":
                raise Failure("window-already-dispositioned", "Do not overwrite a previous disposition", id=identifier)
            authority_value = args.get("authority", "")
            authority = str(authority_value).strip() if not isinstance(authority_value, bool) else ""
            if not authority:
                raise Failure("window-authority-required", "Supply the actual authorization reference for this exact disposition")
            disposition = {"action": action, "authority": authority, "recorded": now(), "revision": revision}
            if action == "waive":
                reason = str(args.get("reason", args.arg(1, ""))).strip()
                if not reason:
                    raise Failure("window-waiver-reason-required", "An explicit per-entry waiver needs its actual rationale")
                disposition["reason"] = reason
            else:
                evidence = load_json(safe_path(args.get("evidence-file", "")))
                if not isinstance(evidence, dict) or evidence.get("revision") != revision or type(evidence.get("exitCode")) is not int or evidence.get("exitCode") != 0 or not isinstance(evidence.get("command"), list) or not evidence["command"] or not isinstance(evidence.get("output"), str):
                    raise Failure("window-fix-evidence-required", "Fixed requires actual command/result evidence at the current revision")
                from .workflow_ops import _citations
                evidence["citations"] = _citations(evidence.get("citations"))
                disposition["evidence"] = evidence
            item["history"].append(disposition)
            item.update({"status": "fixed" if action == "fixed" else "waived", "disposition": disposition})
        write_json(path, ledger)
    return {"recorded": True, "entry": item, "path": str(path), "block": any(entry["status"] == "open" for entry in ledger["entries"])}
