"""Ephemeral dispatch projections. Handoffs remain the only mutable owner."""
import hashlib
import json
from pathlib import Path

from . import evidence
from .results import VerbError, require

DEFAULT_MAX_BYTES = 65536


def source(workspace, name):
    """Read full UTF-8 input, refusing paths outside this checkout."""
    path = (workspace.root / name).resolve()
    require(path.is_relative_to(workspace.root.resolve()),
            "packet source escapes checkout: " + name, "path-escape")
    try:
        data = path.read_bytes()
        content = data.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        return {"path": name, "missing": str(exc)}
    return {"path": name, "sha256": hashlib.sha256(data).hexdigest(),
            "content": content}


def snapshot(workspace, names):
    """Bind agent-supplied context to the current revision and input bytes."""
    try:
        revision = evidence.revision(workspace, "HEAD")
    except VerbError:
        revision = None
    return {"revision": revision, "inputs": {
        name: source(workspace, name).get("sha256") for name in names}}


def evidence_hash(name):
    if name is None:
        return None
    try:
        return hashlib.sha256(Path(name).read_bytes()).hexdigest()
    except OSError as exc:
        raise VerbError("cannot read check evidence: " + str(exc), "bad-evidence") from None


def build(workspace, record, required_sources, base, evidence_file=None,
          max_bytes=DEFAULT_MAX_BYTES):
    require(isinstance(required_sources, list) and required_sources
            and all(isinstance(name, str) and name for name in required_sources),
            "--sources requires all mandatory core, acceptance, security, plan and dependency inputs",
            "missing-sources")
    require(not isinstance(max_bytes, bool), "--max-bytes requires a positive integer", "bad-packet-limit")
    try:
        maximum = int(max_bytes)
    except (ValueError, TypeError):
        raise VerbError("--max-bytes must be a positive integer", "bad-packet-limit") from None
    require(maximum > 0, "--max-bytes must be a positive integer", "bad-packet-limit")
    previous = record.get("input_snapshot") or {}
    previous_inputs = previous.get("inputs") or {}
    # Include every prior input: a changed dependency must be read even when
    # the dispatcher omitted it from the explicit required-source list.
    previously_read = record.get("files_read", [])
    if isinstance(previously_read, str):
        previously_read = [previously_read]
    names = list(dict.fromkeys(required_sources + list(previous_inputs) + previously_read))
    sources = [source(workspace, name) for name in names]
    missing = [row["path"] for row in sources if "missing" in row]
    recorded_hash = evidence_hash(evidence_file)
    changes = evidence.extract(workspace, base, "HEAD", evidence_file)
    current = {row["path"]: row.get("sha256") for row in sources}
    stale = (not previous.get("revision") or not previous_inputs
             or previous["revision"] != changes["head_revision"]
             or any(name not in previous_inputs for name in current)
             or any(current.get(name) != digest or digest is None
                    for name, digest in previous_inputs.items()))
    packet = {
        "schema": 1, "kind": "work-packet", "authority": "local-ephemeral-context-only",
        "dispatchable": not missing, "handoff_id": record["id"],
        "input_revision": changes["head_revision"], "input_hashes": current,
        "required_sources": sources, "changes": changes,
        "unresolved_findings": [{"finding": item, "status": "unverified" if stale else "context-only"}
                                for item in record.get("findings", [])],
        "reusable_context": not stale,
        "reusable_evidence": {"validation": "recorded-only; qualify through verification before reuse",
                              "source_sha256": recorded_hash,
                              "fields": changes["check_evidence"]},
        "missing_inputs": missing,
        "remaining": record.get("remaining", []),
        "handoff": {key: value for key, value in record.items()
                    if key not in ("continuation", "input_snapshot")},
        "instructions": ("Read full required sources, including acceptance and security constraints. "
                         "If inputs changed, re-read them; re-establish unverified findings. Treat handoff "
                         "claims as context, never verification evidence. Check revision and input hashes "
                         "again immediately before dispatch; rebuild if they changed."),
    }
    require(evidence.revision(workspace, "HEAD") == changes["head_revision"]
            and all(source(workspace, row["path"]).get("sha256") == row.get("sha256")
                    for row in sources)
            and evidence_hash(evidence_file) == recorded_hash,
            "packet inputs changed while reading; rebuild before dispatch", "packet-input-changed")
    # Match the CLI's success envelope and pretty-printed wire format exactly.
    size = len((json.dumps({"ok": True, **packet}, ensure_ascii=False, indent=2)
                + "\n").encode("utf-8"))
    require(size <= maximum,
            f"packet is {size} bytes, exceeds {maximum}; no content was truncated; "
            "do not dispatch; narrow remaining work or explicitly raise --max-bytes; "
            "required full-source refs: " + json.dumps(names, ensure_ascii=False),
            "packet-too-large")
    return packet
