"""Durable local idea capture, seed matching and explicitly selected promotion."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat
import uuid

from . import records
from .core import Args, Failure, load_json, now, planning_lock, read, root, slug, write, write_json
from .text import join_frontmatter, split_frontmatter

KINDS = {"note", "todo", "backlog", "seed"}
STATUSES = {"captured", "deferred", "promoted", "archived"}
FIELDS = {"title", "content", "why", "scope", "trigger_when", "breadcrumbs", "planted_during", "tags", "status", "context"}
ALIASES = {"add": "capture", "create": "capture", "init-seeds": "init", "init seeds": "init",
           "list-seeds": "seeds", "seed-enrich": "enrich", "match-seeds": "match"}


def _safe(path):
    """Contain writes and refuse linked ancestors, including Windows junctions."""
    base = root().resolve()
    path = Path(path)
    try:
        relative = path.absolute().relative_to(base)
    except ValueError as exc:
        raise Failure("idea-path-outside-repository", str(path), 2) from exc
    current = base
    for part in relative.parts:
        if part in ("..", "."):
            raise Failure("unsafe-idea-path", str(path), 2)
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if current.is_symlink() or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            raise Failure("linked-idea-path", str(current), 2)
    if not path.resolve().is_relative_to(base):
        raise Failure("idea-path-outside-repository", str(path), 2)
    return path


def _directories():
    planning = _safe(records.planning())
    return _safe(planning / "ideas"), _safe(planning / "seeds")


def _text(value, field):
    if value is None:
        return ""
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return "\n".join(value)
    if not isinstance(value, str):
        raise Failure("invalid-idea-field", field + " must be text or an array of text", 2)
    if "\x00" in value:
        raise Failure("invalid-idea-field", field + " contains NUL", 2)
    return value


def _input(args):
    values = {}
    for option in ("fields", "data", "payload"):
        if args.has(option):
            incoming = args.json(option, {})
            if not isinstance(incoming, dict):
                raise Failure("invalid-idea-fields", "--" + option + " must contain a JSON object", 2)
            values.update(incoming)
    for field in FIELDS | {"kind", "key", "source_id", "rationale", "to", "goals", "body", "description", "breadcrumb"}:
        key = field.replace("_", "-")
        for option in (field, key):
            if args.has(option):
                words = args.all(option)
                if not words:
                    raise Failure("missing-idea-field", "--" + option + " needs a value", 2)
                if field in ("tags", "breadcrumbs") and len(words) == 1 and words[0].lstrip().startswith("["):
                    values[field] = args.json(option)
                else:
                    values[field] = words if field in ("tags", "breadcrumbs") else " ".join(words)
    for key in list(values):
        canonical = key.replace("-", "_")
        if canonical != key:
            values[canonical] = values.pop(key)
    for old, new in (("body", "content"), ("description", "content"), ("breadcrumb", "breadcrumbs")):
        if old in values and new not in values:
            values[new] = values[old]
    return values


def _items(kind=None):
    ideas, seeds = _directories()
    result = []
    for path in sorted(ideas.glob("IDEA-*.json")):
        _safe(path)
        try:
            item = load_json(path)
        except (ValueError, OSError) as exc:
            raise Failure("invalid-idea-record", str(path), 2) from exc
        if not isinstance(item, dict) or item.get("id") != path.stem or not re.fullmatch(r"IDEA-[a-f0-9]{12}", str(item.get("id", ""))) or item.get("kind") not in KINDS:
            raise Failure("invalid-idea-record", str(path), 2)
        result.append((path, item))
    for path in sorted(seeds.glob("SEED-*.md")):
        _safe(path)
        metadata, body = split_frontmatter(read(path))
        identifier = re.match(r"^(SEED-\d+)(?:[-.]|$)", path.name)
        if not identifier:
            continue
        heading = re.search(r"(?m)^#\s+(?:SEED-\d+:?\s*)?(.+)$", body)
        item = {**metadata, "id": identifier[1], "kind": "seed",
                "title": metadata.get("title", heading[1] if heading else path.stem),
                "content": metadata.get("content", body), "status": metadata.get("status", "captured")}
        item["_body"] = body
        result.append((path, item))
    if len({item["id"] for _, item in result}) != len(result):
        raise Failure("duplicate-idea-id", "Existing idea records have duplicate IDs; preserve them and resolve the collision", 2)
    return [(path, item) for path, item in result if kind is None or item["kind"] == kind]


def _public(path, item):
    return {key: value for key, value in item.items() if not key.startswith("_")} | {"path": str(path), "source_id": item["id"]}


def _find(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(r"(?:IDEA-[a-f0-9]{12}|SEED-\d+)", identifier):
        raise Failure("invalid-idea-id", str(identifier), 2)
    for path, item in _items():
        if item["id"] == identifier:
            return path, item
    raise Failure("idea-not-found", identifier)


def _save(path, item, addition=""):
    _safe(path)
    if item["kind"] == "seed":
        body = item.get("_body", "")
        if not body:
            body = ("# " + item["id"] + ": " + item["title"] + "\n\n" + item["content"] +
                    "\n\n## When to Surface\n\n" + item.get("trigger_when", "") +
                    "\n\n## Why This Matters\n\n" + item.get("why", "") +
                    "\n\n## Scope\n\n" + item.get("scope", "") +
                    "\n\n## Breadcrumbs\n\n" + _text(item.get("breadcrumbs", ""), "breadcrumbs") + "\n")
        if addition:
            body += "\n\n## Enrichment " + now() + "\n\n" + addition + "\n"
        metadata = {key: value for key, value in item.items() if not key.startswith("_")}
        write(path, join_frontmatter(metadata, body))
    else:
        write_json(path, item)


def _capture(args, values):
    words = list(args.pos)
    kind = values.get("kind")
    if kind is None:
        kind = words.pop(0) if words and words[0] in KINDS else "note"
    if kind not in KINDS:
        raise Failure("invalid-idea-kind", str(kind), 2)
    content = _text(values.get("content", " ".join(args.all("_body") or words)), "content").strip()
    title = _text(values.get("title", content.splitlines()[0] if content else ""), "title").strip()
    if not title:
        raise Failure("missing-idea-content", "Supply idea text or --title; no enrichment questions are required", 2)
    snapshot = {"kind": kind, "title": title, "content": content or title}
    for field in ("why", "scope", "trigger_when", "breadcrumbs", "planted_during", "tags", "context"):
        if field in values:
            snapshot[field] = values[field] if field == "tags" else _text(values[field], field)
    if "tags" in snapshot and (not isinstance(snapshot["tags"], list) or not all(isinstance(tag, str) for tag in snapshot["tags"])):
        raise Failure("invalid-idea-field", "tags must be an array of strings", 2)
    fingerprint = hashlib.sha256(json.dumps(snapshot, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    key = _text(values.get("key", values.get("source_id", "")), "key")
    _directories()
    with planning_lock():
        items = _items()
        for path, item in items:
            if key and item.get("capture_key") == key:
                if item.get("fingerprint") != fingerprint:
                    raise Failure("idea-key-conflict", "Capture key already refers to different original content", 2)
                return {"created": False, "duplicate": True, "idea": _public(path, item)}
            if item.get("fingerprint") == fingerprint:
                return {"created": False, "duplicate": True, "idea": _public(path, item)}
        ideas, seeds = _directories()
        if kind == "seed":
            sequence = max([int(item["id"].split("-")[1]) for _, item in items if item["kind"] == "seed"], default=0) + 1
            identifier = "SEED-" + str(sequence).zfill(3)
            path = seeds / (identifier + ".md")
        else:
            identifier = "IDEA-" + uuid.uuid4().hex[:12]
            path = ideas / (identifier + ".json")
        if path.exists():
            raise Failure("idea-id-collision", str(path))
        item = {**snapshot, "id": identifier, "schema": 1, "status": "captured", "created": now(), "updated": now(),
                "capture_key": key, "fingerprint": fingerprint, "original": dict(snapshot), "history": [], "promotions": {}}
        _save(path, item)
        return {"created": True, "idea": _public(path, item), "local_only": True}


def _update(args, values, enrich=False):
    identifier = args.arg(0, values.get("source_id", args.get("id")))
    _directories()
    with planning_lock():
        path, item = _find(identifier)
        changes = {field: values[field] for field in FIELDS if field in values}
        trailing = args.all("_body") or args.pos[1:]
        if trailing and "context" not in changes and "content" not in changes:
            changes["context"] = " ".join(trailing)
        if "status" in changes and changes["status"] not in STATUSES:
            raise Failure("invalid-idea-status", str(changes["status"]), 2)
        if changes.get("status") == "promoted":
            raise Failure("explicit-promotion-required", "Use promote to record a source-linked promotion", 2)
        for field in changes:
            if field == "tags":
                if not isinstance(changes[field], list) or not all(isinstance(tag, str) for tag in changes[field]):
                    raise Failure("invalid-idea-field", "tags must be an array of strings", 2)
            else:
                changes[field] = _text(changes[field], field)
        if enrich and item["kind"] != "seed":
            raise Failure("not-a-seed", identifier, 2)
        changes = {field: value for field, value in changes.items() if item.get(field) != value}
        if not changes:
            return {"updated": False, "idea": _public(path, item)}
        item.setdefault("original", {key: value for key, value in item.items() if key in FIELDS or key == "kind"})
        rationale = _text(values.get("rationale", "Manual enrichment" if enrich else "Manual update"), "rationale")
        item.setdefault("history", []).append({"at": now(), "action": "enrich" if enrich else "update", "rationale": rationale,
                                                 "before": {field: item.get(field) for field in changes}, "changes": changes})
        item.update(changes)
        item["updated"] = now()
        addition = rationale + "\n\n" + "\n".join(field + ": " + _text(value, field) for field, value in changes.items())
        _save(path, item, addition if item["kind"] == "seed" else "")
        return {"updated": True, "idea": _public(path, item)}


def _source_todos(marker):
    _safe(records.planning() / "todos")
    _safe(records.planning() / "todos" / "pending")
    items = records.todo(Args([]), "list")["todos"]
    for item in items:
        _safe(item["path"])
    completed = _safe(records.planning() / "todos" / "completed")
    for path in sorted(completed.glob("*.md")):
        _safe(path)
        metadata, body = split_frontmatter(read(path))
        items.append({**metadata, "path": str(path), "body": body, "completed": True})
    return [item for item in items if marker in item.get("body", "")]


def _promote(args, values):
    identifier = args.arg(0, values.get("source_id", args.get("id")))
    target = values.get("to", args.get("to"))
    if target not in ("todo", "phase", "pipeline"):
        raise Failure("promotion-target-required", "Explicit promote requires --to todo, phase or pipeline", 2)
    rationale = _text(values.get("rationale", "Explicit manual promotion"), "rationale")
    _directories()
    with planning_lock():
        path, item = _find(identifier)
        previous = item.setdefault("promotions", {}).get(target)
        if previous and previous.get("state") == "complete":
            return {"promoted": False, "duplicate": True, "source_id": identifier, **previous}
        if item.get("status") == "archived":
            raise Failure("idea-archived", "Restore an archived idea before promotion", 2)
        title = item["title"] + " [" + identifier + "]"
        marker = "Idea source: " + identifier + " (" + str(path.relative_to(root())) + ")"
        description = marker + "\n\n" + item.get("content", "") + "\n\nRationale: " + rationale
        proposal = {"source_id": identifier, "kind": target, "title": title, "description": description, "rationale": rationale}
        intent = previous or {"state": "pending", "at": now(), "proposal": proposal}
        if previous:
            proposal = previous["proposal"]
            title, description = proposal["title"], proposal["description"]
        item["promotions"][target] = intent
        _save(path, item)
    # records.todo and pipelines.command own their locks; never nest planning locks.
    if target == "todo":
        existing = _source_todos(marker)
        if len(existing) > 1:
            raise Failure("duplicate-source-todos", "Multiple todos already reference " + identifier)
        if existing:
            result = existing[0]
        else:
            try:
                result = records.todo(Args([title, "--description", description]), "add")
            except Failure as exc:
                if exc.code != "todo-exists":
                    raise
                existing = _source_todos(marker)
                if len(existing) != 1:
                    raise Failure("todo-source-collision", "Existing todo does not prove this source transition") from exc
                result = existing[0]
    elif target == "pipeline":
        try:
            from . import pipelines
        except ImportError as exc:
            raise Failure("pipeline-unavailable", "Pipeline module is unavailable; retained promotion intent can be retried") from exc
        task = {"id": identifier.lower(), "description": title, "prompt": description}
        result = pipelines.command(Args(["--id", "idea-" + slug(identifier), "--tasks", json.dumps([task])]), "create")
    else:
        # A phase promotion proposes selected scope; only the coordinator creates phases.
        result = {"proposal": proposal, "requires_coordinator": True, "phase_created": False}
    with planning_lock():
        path, item = _find(identifier)
        completed_before = item.get("promotions", {}).get(target)
        if completed_before and completed_before.get("state") == "complete":
            return {"promoted": False, "duplicate": True, "source_id": identifier, **completed_before}
        item.setdefault("history", []).append({"at": now(), "action": "promote", "target": target,
                                                 "rationale": proposal["rationale"], "source_id": identifier})
        completed = {"state": "complete", "at": now(), "proposal": proposal, "result": result}
        item.setdefault("promotions", {})[target] = completed
        item["status"], item["updated"] = "promoted", now()
        _save(path, item)
    return {"promoted": True, "source_id": identifier, "target": target, **completed}


def command(args, action):
    """Accept core.Args or an argv list; capture performs no external dispatch."""
    if isinstance(args, (list, tuple)):
        args = Args(list(args))
    action = ALIASES.get(action, action)
    values = _input(args)
    if action in KINDS:
        values["kind"] = action
        action = "capture"
    if action == "capture":
        return _capture(args, values)
    if action in ("update", "enrich"):
        return _update(args, values, action == "enrich")
    if action == "promote":
        return _promote(args, values)
    if action in ("list", "seeds", "init", "match", "get"):
        kind = "seed" if action in ("seeds", "init", "match") else values.get("kind")
        if action == "get":
            path, item = _find(args.arg(0, values.get("source_id", args.get("id"))))
            return {"idea": _public(path, item)}
        if kind is not None and kind not in KINDS:
            raise Failure("invalid-idea-kind", str(kind), 2)
        items = [_public(path, item) for path, item in _items(kind)]
        if args.has("status"):
            items = [item for item in items if item.get("status") == args.get("status")]
        if action == "match":
            goals = _text(values.get("goals", " ".join(args.pos)), "goals")
            tokens = set(re.findall(r"[\w]{3,}", goals.casefold())) - {"the", "and", "for", "with", "this", "that"}
            matches = []
            for item in items:
                if item.get("status") in ("archived", "promoted"):
                    continue
                evidence = " ".join(_text(item.get(field, ""), field) for field in ("title", "trigger_when", "scope", "why", "content"))
                overlap = sorted(tokens & set(re.findall(r"[\w]{3,}", evidence.casefold())))
                if overlap:
                    matches.append({**item, "matched_terms": overlap, "selected": False})
            return {"seeds": matches, "matches": matches, "count": len(matches), "manual_opt_in": True, "goals": goals}
        return {"ideas": items, "seeds": items if kind == "seed" else [], "count": len(items),
                "seed_count": len(items) if kind == "seed" else 0, "has_seeds": bool(items) if kind == "seed" else False,
                "seed_files": [item["path"] for item in items] if kind == "seed" else [], "local_only": True}
    raise Failure("unsupported-idea-action", str(action), 2)
