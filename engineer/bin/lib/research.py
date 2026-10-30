"""Cited research caching and bounded evidence inputs; no implicit network calls."""
import datetime as dt
import hashlib
import json
import math
import re
from urllib.parse import urlparse
from . import records
from .core import Args, Failure, digest, load_json, now, planning_lock, read, safe_path, write_json
from .text import split_frontmatter


def _key(value):
    if not re.fullmatch(r"[a-f0-9]{64}", str(value)):
        raise Failure("invalid-research-key", "Research keys must be SHA256 values", 2)
    return safe_path(records.planning()/"research-cache"/(value+".json"))


def _cited_entry(entry):
    """Reuse only actual cited cache content; a tier is not a truth judgment."""
    if not isinstance(entry, dict) or not isinstance(entry.get("content"), str) or not entry["content"].strip():
        return False
    sources = entry.get("sources")
    if not isinstance(sources, list) or not sources:
        return False
    for source in sources:
        if not isinstance(source, str):
            return False
        parsed = urlparse(source)
        if parsed.scheme in ("https", "http") and parsed.hostname:
            continue
        try:
            if not safe_path(source).is_file():
                return False
        except Failure:
            return False
    return True


def confidence(args):
    provider = str(args.get("provider", "unknown"))
    verified = args.has("verified") and str(args.get("verified")).lower() in ("true", "1", "yes")
    # This is provider authority only, never a claim-truth/goal-verification tier.
    if provider in ("context7", "ref", "official", "primary"):
        return "HIGH" if verified else "MEDIUM"
    return "MEDIUM" if verified else "LOW"


def store(args, action):
    if action in ("list", "query"):
        query = str(args.get("query", args.arg(0, ""))).casefold()
        items = []
        for path in sorted((records.planning()/"research-cache").glob("*.json")):
            path = safe_path(path)
            item = load_json(path)
            if query in json.dumps(item, ensure_ascii=False).casefold():
                items.append(item)
        return {"items": items, "count": len(items), "claimJudgment": False}
    path = _key(args.need())
    if action == "get":
        item = load_json(path)
        return {"hit": item is not None, "entry": item}
    if action != "put":
        raise Failure("unknown-research-action", action, 2)
    content = str(args.get("content", "")).strip()
    sources = list(args.all("sources") or args.all("urls"))
    if args.has("url"):
        sources.append(args.get("url"))
    if not content or not sources:
        raise Failure("uncited-research", "Cache entries require content and actual --sources/--url citations", 2)
    for source in sources:
        parsed = urlparse(str(source))
        if parsed.scheme not in ("https", "http") or not parsed.hostname:
            if not safe_path(source).is_file():
                raise Failure("invalid-research-source", str(source), 2)
    tier = str(args.get("confidence", "LOW"))
    if tier not in ("HIGH", "MEDIUM", "LOW"):
        raise Failure("invalid-confidence", tier, 2)
    item = {"key": path.stem, "content": content, "sources": sources, "provider": args.get("provider", "unknown"),
            "source": args.get("source", "web"), "kind": args.get("kind", "docs"), "confidence": tier,
            "recorded": now(), "claimJudgment": False}
    with planning_lock():
        write_json(path, item)
    return {"stored": True, "entry": item}


def store_command(args):
    action = args.need()
    tail = Args([])
    tail.pos, tail.opts = args.pos[1:], dict(args.opts)
    return store(tail, action)


def plan(args):
    source = safe_path(args.get("input", args.arg(0, "")))
    payload = load_json(source)
    if not isinstance(payload, dict) or not isinstance(payload.get("questions"), list):
        raise Failure("invalid-research-input", "Research input requires a questions array", 2)
    try:
        max_age = float(args.get("max-age-hours", 168))
    except (ValueError, TypeError) as exc:
        raise Failure("invalid-research-age", "Supply nonnegative finite --max-age-hours", 2) from exc
    if not math.isfinite(max_age) or max_age < 0:
        raise Failure("invalid-research-age", "Supply nonnegative finite --max-age-hours", 2)
    availability = payload.get("config", {})
    if not isinstance(availability, dict):
        raise Failure("invalid-research-input", "Research provider availability must be a mapping", 2)
    items = []
    for question in payload["questions"]:
        if not isinstance(question, dict) or not isinstance(question.get("text"), str) or not question["text"].strip() or question.get("kind", "docs") not in ("docs", "web", "scrape"):
            raise Failure("invalid-research-question", "Each question needs text and docs/web/scrape kind", 2)
        identity = {"ecosystem": payload.get("ecosystem"), **question}
        key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        entry = load_json(_key(key))
        stale = True
        if entry:
            try:
                age = (dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(entry["recorded"])).total_seconds()
                stale = not _cited_entry(entry) or age < 0 or age > max_age*3600
            except (KeyError, ValueError, TypeError, AttributeError):
                stale = True
        kind = question.get("kind", "docs")
        order = (("context7", "ref", "websearch") if kind == "docs" else
                 ("firecrawl", "webfetch") if kind == "scrape" else ("exa", "tavily", "brave", "websearch"))
        provider = next((name for name in order if availability.get(name, availability.get(name+"_search", False)) is True), None)
        item = {"question": question["text"], "key": key, "cache": {"hit": bool(entry), "stale": stale, "entry": entry}}
        if not entry or stale:
            item["fetch"] = {"provider": provider, "query": question["text"], "library": question.get("library"),
                             "version": question.get("version"), "url": question.get("url"), "available": provider is not None}
            if provider is None:
                item["blocked"] = "No caller-declared source provider; use an available primary-documentation tool and record the actual citation"
        items.append(item)
    return {"items": items, "executesFetch": False}


def inputs(args, kind):
    directory = records.phase_dir(args.arg(0, args.get("phase")))
    suffixes = {"discuss": ("SPEC", "CONTEXT", "DISCUSSION-LOG"), "research": ("SPEC", "CONTEXT", "RESEARCH"),
                "patterns": ("CONTEXT", "RESEARCH", "PATTERNS")}
    if kind not in suffixes:
        raise Failure("unknown-research-input-kind", kind, 2)
    paths = [safe_path(p) for suffix in suffixes[kind] for p in sorted(directory.glob("*-"+suffix+".md"))]
    shared = [records.planning()/name for name in ("PROJECT.md", "REQUIREMENTS.md", "ROADMAP.md", "STATE.md")]
    artifacts = [{"path": str(path), "digest": digest([path]), "content": read(path)} for path in paths+shared if path.is_file()]
    # Only explicit path tokens become mapping candidates. They are evidence
    # inputs, not a determination of which implementation pattern is correct.
    candidates, missing = set(), set()
    for artifact in artifacts:
        for value in re.findall(r"`([^`\n]+)`", artifact["content"]):
            if "/" not in value and "\\" not in value:
                continue
            try:
                path = safe_path(value)
                (candidates if path.is_file() else missing).add(str(path))
            except (Failure, OSError):
                continue
    return {"phase_dir": str(directory), "kind": kind, "artifacts": artifacts, "source_candidates": sorted(candidates),
            "missing_candidates": sorted(missing), "approval": "Requires actual recorded human decisions; not inferred from source presence"}
