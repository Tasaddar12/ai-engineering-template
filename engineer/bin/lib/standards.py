"""Resolve standards routing IDs to the exact sections of the curated standards.

The domain indexes under ``engineer/standards/*/index.md`` are the only routing
source. Each table row maps an ID suffix to a document and, unless the document
is marked **whole**, a main section selector (``§N`` or heading text). Offsets
are computed at read time; nothing about line positions is stored.
"""
import re
from .core import Failure, read
from .markdown_sectionizer import tokenize_headings
from . import models

ROW = re.compile(r"^\| `([\w.-]+)` — ([^|]+?) \| (.+?) \|\s*$")
PATH = re.compile(r"`(engineer/standards/[^`]+\.md)`")
MAIN = re.compile(r"\s*§(.+?)(?=;|\s+or\s|$)")
NUMBER = re.compile(r"\d+(?:\.\d+)*")
INCLUDE = re.compile(r"\binclude [^§;|]*?§(\d+(?:\.\d+)*)")
EVERY = re.compile(r"Every `([\w.-]+)\.\*` row includes `(engineer/standards/[^`]+\.md)` §([^.\n]+)\.")


def _base():
    return models.NAMESPACE


def catalog():
    """Every routing ID with its concern, document, main selector and required companions."""
    entries = {}
    for index in sorted((_base()/"engineer/standards").glob("*/index.md")):
        domain, text = index.parent.name, read(index)
        every = [(prefix, path, selector.strip()) for prefix, path, selector in EVERY.findall(text)]
        for line in text.splitlines():
            row = ROW.match(line)
            if not row:
                continue
            suffix, concern, cell = row.groups()
            found = PATH.search(cell)
            if not found:
                raise Failure("standards-index-invalid", f"No standards path in {index.name} row {suffix}", 2)
            rest = cell[found.end():]
            main = MAIN.match(rest)
            selector = None
            if main:
                number = NUMBER.match(main.group(1).strip())
                selector = number.group(0) if number else main.group(1).strip()
            includes = [(path, sel) for prefix, path, sel in every if suffix.startswith(prefix + ".")]
            includes += [(found.group(1), sel) for sel in INCLUDE.findall(rest)]
            entries[f"{domain}.{suffix}"] = {
                "concern": concern.strip(), "path": found.group(1), "selector": selector,
                "whole": "**whole**" in rest, "includes": includes}
    return entries


def _norm(text):
    return re.sub(r"\s+", " ", text.replace("`", "")).strip().lower()


def _find(headings, selector):
    # Selectors address sections, never the document title.
    headings = [h if h["level"] >= 2 else {**h, "text": ""} for h in headings]
    if NUMBER.fullmatch(selector):
        pattern = re.compile(re.escape(selector) + r"\.?(?:\s|$)")
        return next((i for i, h in enumerate(headings) if pattern.match(h["text"])), -1)
    wanted = _norm(selector)
    names = [_norm(h["text"]) for h in headings]
    unnumbered = [re.sub(r"^\d+(?:\.\d+)*\.?\s+", "", name) for name in names]
    for candidates in (names, unnumbered):
        exact = next((i for i, name in enumerate(candidates) if name == wanted), -1)
        if exact != -1:
            return exact
    for candidates in (names, unnumbered):
        prefix = next((i for i, name in enumerate(candidates) if name.startswith(wanted)), -1)
        if prefix != -1:
            return prefix
    return -1


def _ranges(path, selector, rid):
    """Line ranges (1-based, end exclusive) for a section plus its ancestors' introductions."""
    if not (_base()/path).is_file():
        raise Failure("standards-document-missing", f"{rid}: {path} does not exist", 2, id=rid, path=path)
    text = read(_base()/path)
    lines, headings = text.split("\n"), tokenize_headings(text)
    total = len(lines) + 1
    if selector is None:
        return [(1, total)], lines
    index = _find(headings, selector)
    if index == -1:
        raise Failure("standards-heading-missing", f"{rid}: no heading §{selector} in {path}", 2, id=rid, path=path)
    target = headings[index]
    end = next((h["line"] for h in headings[index+1:] if h["level"] <= target["level"]), total)
    ranges = [(target["line"], end)]
    level = target["level"]
    for position in range(index - 1, -1, -1):
        heading = headings[position]
        if 1 < heading["level"] < level:
            ranges.append((heading["line"], headings[position+1]["line"]))
            level = heading["level"]
    first = next((h["line"] for h in headings if h["level"] >= 2), total)
    ranges.append((1, first))
    return ranges, lines


def _merge(ranges):
    merged = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def split_ids(values):
    """Split on commas or newlines that precede another ID, so ``@Heading, text`` stays whole."""
    parts = [part.strip() for value in values for part in re.split(r"[,\n]\s*(?=[a-z]+\.[a-z])", str(value))]
    return [part.strip(" ,") for part in parts if part.strip(" ,")]


def resolve(ids):
    """Resolve IDs (optionally ``id@selector``) into per-document text blocks in request order."""
    entries, files = catalog(), {}
    for requested in ids:
        rid, _, alternative = requested.partition("@")
        entry = entries.get(rid)
        if entry is None:
            raise Failure("unknown-standard", f"Unknown standards routing ID: {rid}", 2, id=rid)
        selector = alternative.lstrip("§").strip() or entry["selector"]
        targets = [(entry["path"], selector)] + entry["includes"]
        for path, sel in targets:
            ranges, lines = _ranges(path, sel, rid)
            block = files.setdefault(path, {"path": path, "ids": [], "ranges": [], "lines": lines})
            if requested not in block["ids"]:
                block["ids"].append(requested)
            block["ranges"].extend(ranges)
    result = []
    for block in files.values():
        parts = ["\n".join(block["lines"][start-1:end-1]).rstrip() for start, end in _merge(block["ranges"])]
        text = f"<!-- standards: {', '.join(block['ids'])} | {block['path']} -->\n" + "\n\n[…]\n\n".join(parts)
        result.append({"path": block["path"], "ids": block["ids"], "chars": len(text), "text": text})
    return result


def plan_ids(path, task=None):
    from . import plans
    if not path.is_file():
        raise Failure("file-not-found", str(path), 2)
    tasks = plans.tasks(read(path))
    if task is not None:
        if not 1 <= task <= len(tasks):
            raise Failure("task-not-found", f"Plan has no task {task}", 2)
        tasks = [tasks[task-1]]
    ordered = []
    for item in tasks:
        for rid in split_ids([item.get("standards", "")]):
            if rid not in ordered:
                ordered.append(rid)
    return ordered


def read_command(args):
    from .core import safe_path
    ids = list(dict.fromkeys(split_ids(args.pos)))
    if args.has("task") and not args.has("plan"):
        raise Failure("invalid-argument", "--task requires --plan", 2)
    if args.has("plan"):
        plan, task = args.get("plan"), args.get("task")
        if not isinstance(plan, str):
            raise Failure("missing-argument", "--plan requires a PLAN.md path", 2)
        if task is not None and not (isinstance(task, str) and task.isdigit()):
            raise Failure("invalid-argument", "--task requires a task number", 2)
        pinned = plan_ids(safe_path(plan), int(task) if task else None)
        if not pinned and not ids:
            raise Failure("no-pinned-standards", f"{plan} pins no standards; pick IDs with standards-list", 3)
        ids += [rid for rid in pinned if rid not in ids]
    if not ids:
        raise Failure("missing-argument", "Name routing IDs or --plan PLAN.md", 2)
    blocks = resolve(ids)
    text = "\n\n".join(block["text"] for block in blocks)
    if args.has("raw"):
        return text
    return {"ids": ids, "chars": len(text), "documents": [{k: b[k] for k in ("path", "ids", "chars")} for b in blocks], "text": text}


def list_command(args):
    domain = args.arg(0)
    rows = [{"id": rid, "concern": entry["concern"]} for rid, entry in catalog().items()
            if domain is None or rid.split(".", 1)[0] == domain]
    if domain is not None and not rows:
        raise Failure("unknown-standard", f"Unknown standards domain: {domain}", 2, id=domain)
    if args.has("raw"):
        return "\n".join(f"{row['id']} — {row['concern']}" for row in rows)
    return {"standards": rows, "count": len(rows)}


def validate_catalog():
    """Resolve every row's main section and companions; return findings."""
    findings = []
    for rid, entry in catalog().items():
        if entry["selector"] is None and not entry["whole"]:
            findings.append(f"{rid}: neither a §selector nor **whole**")
            continue
        try:
            resolve([rid])
        except Failure as exc:
            findings.append(exc.message)
    return findings
