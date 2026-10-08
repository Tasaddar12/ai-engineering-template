"""Reusable source/context packets, never execution or verification authority.

The coordinator supplies a JSON contract and stores an agent's structured result.
Every lookup hashes the caller's live scope, including ignored/untracked files.
Revision binding is the default; a complete declared scope is an explicit opt-in
to identical-content reuse across commits. This is not provider prompt caching.
"""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import time

from .results import VerbError, require

SCHEMA = "source-evidence/v1"
STATE_SCHEMA = 1
HEX = re.compile(r"^[0-9a-f]{64}$")
REV = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


def _json(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise VerbError("request must contain finite JSON values", "invalid-evidence") from exc


def _digest(value):
    return hashlib.sha256(_json(value)).hexdigest()


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def parse_request(value):
    """Decode strict JSON or detach a caller-owned mapping before validation."""
    try:
        result = json.loads(value if isinstance(value, str) else _json(value),
                            object_pairs_hook=_unique_object,
                            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
    except (ValueError, TypeError, UnicodeError) as exc:
        raise VerbError("invalid evidence JSON", "invalid-evidence") from exc
    require(isinstance(result, dict), "evidence request must be an object", "invalid-evidence")
    return result


def _text(value, name):
    require(isinstance(value, str) and bool(value.strip()),
            name + " must be a nonempty string", "invalid-evidence")
    return value


def _paths(value, name):
    require(isinstance(value, list) and bool(value), name + " must be a nonempty list", "invalid-evidence")
    normalized = []
    for entry in value:
        _text(entry, name)
        directory = entry.endswith("/")
        parts = entry.rstrip("/").split("/")
        require(not (entry.startswith("/") or "\\" in entry or ":" in entry
                     or any(p in ("", ".", "..") or p.endswith((".", " ")) for p in parts)
                     or any(p.lower() == ".git" for p in parts)
                     or any(re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", p) for p in parts)
                     or any(ord(c) < 32 for c in entry)),
                "unsafe evidence path: " + entry, "unsafe-evidence-path")
        require(name != "inputs" or not directory, "inputs must be exact files", "invalid-evidence")
        normalized.append(entry)
    require(len(set(normalized)) == len(normalized), name + " contains duplicate paths", "invalid-evidence")
    return sorted(normalized)


def _git(root, *args):
    try:
        result = subprocess.run(["git", *args], cwd=root, capture_output=True,
                                text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VerbError("cannot inspect evidence repository", "evidence-repository") from exc
    require(result.returncode == 0, "cannot inspect evidence repository", "evidence-repository")
    return result.stdout.strip()


def _no_links(path):
    for item in (path, *path.parents):
        require(not item.is_symlink() and not (hasattr(item, "is_junction") and item.is_junction()),
                "symlink/junction evidence path rejected", "unsafe-evidence-path")


def _repository(cwd):
    root = Path(cwd if isinstance(cwd, (str, os.PathLike)) else cwd.root).absolute()
    _no_links(root)
    require(Path(_git(root, "rev-parse", "--show-toplevel")).resolve() == root.resolve(),
            "evidence requires the repository root", "evidence-repository")
    _no_links(root / ".git")
    common = Path(_git(root, "rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = root / common
    _no_links(common.absolute())
    common = common.resolve()
    cache = common / "ai-phase" / "evidence"
    _no_links(cache)
    return root, cache


def _contract(root, request):
    require(request.get("schema") == SCHEMA, "unsupported evidence schema", "invalid-evidence")
    revision = request.get("source_revision")
    require(isinstance(revision, str) and REV.fullmatch(revision),
            "source_revision must be a full commit SHA", "invalid-evidence")
    require(root is None or _git(root, "rev-parse", "HEAD") == revision,
            "source_revision differs from current HEAD", "stale-evidence-revision")
    inputs = _paths(request.get("inputs"), "inputs")
    scope = _paths(request.get("scope"), "scope")
    require(all(any(path == s or (s.endswith("/") and path.startswith(s)) for s in scope)
                for path in inputs), "every input must be inside scope", "invalid-evidence")
    acceptance = request.get("acceptance")
    require(isinstance(acceptance, list) and bool(acceptance), "acceptance must be a nonempty list", "invalid-evidence")
    for item in acceptance:
        _text(item, "acceptance")
    require(len(set(acceptance)) == len(acceptance), "duplicate acceptance", "invalid-evidence")
    provenance = request.get("provenance")
    require(isinstance(provenance, dict), "provenance is required", "invalid-evidence")
    for name in ("role", "model", "prompt_version"):
        _text(provenance.get(name), "provenance." + name)
    require(isinstance(request.get("config"), dict), "explicit config object required", "invalid-evidence")
    reuse = request.get("reuse", {"cross_revision": False, "complete_scope": False})
    require(isinstance(reuse, dict) and set(reuse) == {"cross_revision", "complete_scope"}
            and all(type(v) is bool for v in reuse.values()), "invalid reuse contract", "invalid-evidence")
    require(not reuse["cross_revision"] or reuse["complete_scope"],
            "cross revision reuse requires a complete scope contract", "invalid-evidence")
    contract = {"schema": SCHEMA, "task_class": _text(request.get("task_class"), "task_class"),
                "question": _text(request.get("question"), "question"), "inputs": inputs,
                "scope": scope, "acceptance": sorted(acceptance), "provenance": provenance,
                "config": request["config"], "reuse": reuse}
    return contract, revision


def _file(root, relative):
    path = root / relative
    _no_links(path)
    require(path.is_file(), "missing evidence input: " + relative, "stale-evidence-input")
    try:
        before = path.stat()
        with path.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            data = stream.read()
            after_open = os.fstat(stream.fileno())
        after = path.stat()
    except OSError as exc:
        raise VerbError("unreadable evidence input: " + relative, "stale-evidence-input") from exc
    # Windows stat/fstat can report different ctime meanings. Compare ctime
    # within each API while comparing file identity/mtime across both APIs.
    signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_mode)
    require(signature(before) == signature(opened) == signature(after_open) == signature(after)
            and before.st_ctime_ns == after.st_ctime_ns and opened.st_ctime_ns == after_open.st_ctime_ns,
            "input changed while hashing: " + relative, "stale-evidence-input")
    return {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
            "executable": bool(before.st_mode & stat.S_IXUSR)}


def _fingerprint(root, contract):
    def inventory():
        files = set()
        directories = set()
        for scope in contract["scope"]:
            path = root / scope.rstrip("/")
            _no_links(path)
            if not scope.endswith("/"):
                require(path.is_file(), "missing scope file: " + scope, "stale-evidence-input")
                files.add(scope)
                continue
            require(path.is_dir(), "missing scope directory: " + scope, "stale-evidence-input")
            for base, dirs, names in os.walk(path, followlinks=False):
                for entry in [*dirs, *names]:
                    child = Path(base) / entry
                    _no_links(child)
                    require(entry.lower() != ".git", "scope contains Git metadata", "unsafe-evidence-path")
                    relative = child.relative_to(root).as_posix()
                    _paths([relative], "scope")
                    if child.is_dir():
                        directories.add(relative + "/")
                    elif child.is_file():
                        files.add(relative)
                    else:
                        raise VerbError("nonregular scope entry", "unsafe-evidence-path")
        return sorted(files), sorted(directories)
    files, directories = inventory()
    require(set(contract["inputs"]).issubset(files), "missing declared input", "stale-evidence-input")
    hashes = {name: _file(root, name) for name in files}
    require((files, directories) == inventory(), "scope changed while hashing", "stale-evidence-input")
    require(hashes == {name: _file(root, name) for name in files},
            "input bytes changed during capture", "stale-evidence-input")
    return {"files": hashes, "directories": directories}


@contextlib.contextmanager
def _locked(cache):
    _no_links(cache)
    cache.mkdir(parents=True, exist_ok=True)
    lock = cache / "state.lock"
    _no_links(lock)
    with lock.open("a+b") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"\0")
            stream.flush()
        deadline = time.monotonic() + 30
        while True:
            try:
                stream.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                require(time.monotonic() < deadline, "evidence cache is busy", "evidence-lock")
                time.sleep(0.02)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def _read(cache):
    path = cache / "state.json"
    _no_links(path)
    if not path.exists():
        return {"schema": STATE_SCHEMA, "packets": {}, "invalidations": {}}
    try:
        envelope = parse_request(path.read_text(encoding="utf-8"))
        state = envelope["state"]
        require(envelope["digest"] == _digest(state), "corrupt evidence state digest", "corrupt-evidence")
        require(state["schema"] == STATE_SCHEMA and isinstance(state["packets"], dict)
                and isinstance(state["invalidations"], dict), "corrupt evidence state", "corrupt-evidence")
        for artifact_id, packet in state["packets"].items():
            require(HEX.fullmatch(artifact_id) and _digest(packet) == artifact_id,
                    "corrupt evidence packet digest", "corrupt-evidence")
            require(set(packet) == {"contract", "source_revision", "fingerprint", "status", "outputs", "evidence"}
                    and REV.fullmatch(packet["source_revision"])
                    and packet["contract"]["schema"] == SCHEMA,
                    "incomplete evidence packet", "corrupt-evidence")
            canonical, _ = _contract(None, dict(packet["contract"], source_revision=packet["source_revision"]))
            require(canonical == packet["contract"], "noncanonical evidence contract", "corrupt-evidence")
            _payload(packet)
            fingerprint = packet["fingerprint"]
            require(isinstance(fingerprint, dict) and set(fingerprint) == {"files", "directories"}
                    and isinstance(fingerprint["files"], dict)
                    and isinstance(fingerprint["directories"], list), "invalid fingerprint", "corrupt-evidence")
            files = fingerprint["files"]
            require(set(canonical["inputs"]).issubset(files), "missing input hashes", "corrupt-evidence")
            _paths(list(files), "inputs")
            for name, info in files.items():
                require(any(name == s or (s.endswith("/") and name.startswith(s)) for s in canonical["scope"])
                        and isinstance(info, dict) and set(info) == {"sha256", "size", "executable"}
                        and isinstance(info["sha256"], str) and HEX.fullmatch(info["sha256"])
                        and type(info["size"]) is int and info["size"] >= 0
                        and type(info["executable"]) is bool, "invalid input digest", "corrupt-evidence")
            dirs = fingerprint["directories"]
            require(dirs == sorted(set(dirs)), "invalid directory inventory", "corrupt-evidence")
            if dirs:
                _paths(dirs, "scope")
                require(all(d.endswith("/") and any(s.endswith("/") and d.startswith(s) for s in canonical["scope"])
                            for d in dirs), "invalid directory scope", "corrupt-evidence")
        for artifact_id, invalidation in state["invalidations"].items():
            require(artifact_id in state["packets"] and isinstance(invalidation, str) and invalidation.strip(),
                    "corrupt invalidation", "corrupt-evidence")
        return state
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, VerbError) as exc:
        raise VerbError("corrupt evidence cache; no packet reused", "corrupt-evidence") from exc


def _write(cache, state):
    path = cache / "state.json"
    _no_links(path)
    descriptor, name = tempfile.mkstemp(prefix="state-", suffix=".tmp", dir=cache)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(_json({"state": state, "digest": _digest(state)}))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _payload(request):
    require(request.get("status") in ("complete", "incomplete", "blocked", "failed"),
            "explicit packet status required", "invalid-evidence")
    outputs, evidence = request.get("outputs"), request.get("evidence")
    require(isinstance(outputs, dict) and bool(outputs), "structured outputs required", "invalid-evidence")
    require(isinstance(evidence, list) and bool(evidence), "cited evidence required", "invalid-evidence")
    for item in evidence:
        require(isinstance(item, dict), "evidence must be structured", "invalid-evidence")
        for name in ("claim", "citation", "excerpt"):
            _text(item.get(name), "evidence." + name)
    return outputs, evidence


def store(cwd, request):
    """Persist a coordinator-supplied packet; incomplete results remain history."""
    request = parse_request(request)
    root, cache = _repository(cwd)
    contract, revision = _contract(root, request)
    outputs, evidence = _payload(request)
    with _locked(cache):
        state = _read(cache)
        packet = {"contract": contract, "source_revision": revision,
                  "fingerprint": _fingerprint(root, contract), "status": request["status"],
                  "outputs": outputs, "evidence": evidence}
        require(_git(root, "rev-parse", "HEAD") == revision, "HEAD changed during capture", "stale-evidence-revision")
        artifact_id = _digest(packet)
        state["packets"][artifact_id] = packet
        _write(cache, state)
    return {"artifact_id": artifact_id, "source_revision": revision,
            "reusable": packet["status"] == "complete" and artifact_id not in state["invalidations"],
            "reused": False, "reasons": ["stored"]}


def lookup(cwd, request):
    """Revalidate the live contract/bytes before returning any reusable payload."""
    request = parse_request(request)
    require(type(request.get("include_payload", False)) is bool, "include_payload must be boolean", "invalid-evidence")
    root, cache = _repository(cwd)
    contract, revision = _contract(root, request)
    with _locked(cache):
        try:
            state = _read(cache)
            fingerprint = _fingerprint(root, contract)
        except VerbError as exc:
            if exc.code not in ("corrupt-evidence", "stale-evidence-input"):
                raise
            return {"reused": False, "artifact_id": None, "reasons": [exc.code]}
        reasons = set()
        for artifact_id, packet in sorted(state["packets"].items()):
            if packet["contract"] != contract:
                reasons.add("contract-changed")
                continue
            if artifact_id in state["invalidations"]:
                reasons.add("explicitly-invalidated")
            elif packet["status"] != "complete":
                reasons.add("packet-not-complete")
            elif packet["source_revision"] != revision and not contract["reuse"]["cross_revision"]:
                reasons.add("revision-changed")
            elif packet["fingerprint"] != fingerprint:
                reasons.add("inputs-or-scope-changed")
            else:
                require(_git(root, "rev-parse", "HEAD") == revision, "HEAD changed during lookup", "stale-evidence-revision")
                result = {"reused": True, "artifact_id": artifact_id,
                          "source_revision": packet["source_revision"], "reasons": ["validated"]}
                if request.get("include_payload"):
                    result.update(outputs=packet["outputs"], evidence=packet["evidence"],
                                  provenance=contract["provenance"])
                return result
    return {"reused": False, "artifact_id": None, "reasons": sorted(reasons) or ["not-found"]}


def invalidate(cwd, request):
    """Keep a packet and its explicit invalidation reason; never erase history."""
    request = parse_request(request)
    artifact_id = request.get("artifact_id")
    require(isinstance(artifact_id, str) and HEX.fullmatch(artifact_id), "invalid artifact_id", "invalid-evidence")
    reason = _text(request.get("reason"), "reason")
    _, cache = _repository(cwd)
    with _locked(cache):
        state = _read(cache)
        require(artifact_id in state["packets"], "unknown evidence artifact", "unknown-evidence")
        state["invalidations"][artifact_id] = reason
        _write(cache, state)
    return {"artifact_id": artifact_id, "invalidated": True, "reason": reason}
