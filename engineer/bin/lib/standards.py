"""Resolve standards routing IDs to the exact sections of the curated standards.

``engineer/standards/routing.json`` is the routing source of truth; the index
tables are generated from it by ``gen_standards_routing``. Each entry maps an ID
to a document and, unless the document is read **whole**, a main section
selector (``§N`` number or heading text). Offsets are computed at read time;
nothing about line positions is stored.
"""
import json
import re
from pathlib import Path
from .core import Failure, read
from .markdown_sectionizer import tokenize_headings
from . import models

ROUTING = "engineer/standards/routing.json"
# Consistency between an entry's rendered menu text and its structured fields.
MAIN = re.compile(r"\s*§(.+?)(?=;|\s+or\s|$)")
NUMBER = re.compile(r"\d+(?:\.\d+)*")
INCLUDE = re.compile(r"\binclude [^§;|]*?§(\d+(?:\.\d+)*)")
ID = re.compile(r"[a-z]+(?:\.[a-z0-9-]+)+")
ENTRY_KEYS = {"id", "concern", "path", "section", "whole", "includes", "menu"}


def _base():
    return models.NAMESPACE


def load_routing(root=None):
    path = Path(root or _base())/ROUTING
    if not path.is_file():
        raise Failure("standards-routing-missing", f"{ROUTING} does not exist", 2)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise Failure("standards-routing-invalid", f"{ROUTING}: {exc}", 2)


def _menu_section(menu):
    """The main selector a rendered menu shows: a section number, or heading text up to ';' / ' or '."""
    main = MAIN.match(menu)
    if not main:
        return None
    text = main.group(1).strip()
    number = NUMBER.match(text)
    return number.group(0) if number else text


def validate_routing(data, root=None):
    """Structural findings for routing.json: schema, IDs, paths and menu/field agreement."""
    base, findings, seen = Path(root or _base()), [], set()
    if not isinstance(data, dict) or data.get("schema") != 1:
        return ["schema must be 1"]
    if not isinstance(data.get("domains"), list) or not isinstance(data.get("aliases", {}), dict):
        return ["domains must be a list and aliases an object"]
    names = [domain.get("domain") if isinstance(domain, dict) else None for domain in data["domains"]]
    if names != sorted(n for n in names if isinstance(n, str)) or len(set(names)) != len(names):
        findings.append("domains must be unique and sorted by name")
    for domain in data["domains"]:
        if not isinstance(domain, dict) or not {"domain", "index", "groups"} <= set(domain) or not isinstance(domain["groups"], list):
            findings.append("each domain needs domain, index and a groups list")
            continue
        name, regions, suffixes = domain["domain"], set(), []
        for group in domain["groups"]:
            if not isinstance(group, dict) or set(group) != {"region", "entries"} or not isinstance(group["entries"], list):
                findings.append(f"{name}: each group needs exactly region and an entries list")
                continue
            if group["region"] in regions:
                findings.append(f"{name}: duplicate region {group['region']}")
            regions.add(group["region"])
            suffixes += [e.get("id", "")[len(name) + 1:] for e in group["entries"] if isinstance(e, dict)]
        for prefix in domain.get("prefix_includes", []):
            if not isinstance(prefix, dict) or set(prefix) != {"prefix", "path", "section"}:
                findings.append(f"{name}: each prefix include needs exactly prefix, path and section")
                continue
            if not (base/prefix["path"]).is_file():
                findings.append(f"{name}: prefix include {prefix['path']} does not exist")
            if not any(s.startswith(prefix["prefix"] + ".") for s in suffixes):
                findings.append(f"{name}: prefix include {prefix['prefix']}.* matches no entry")
        for group in domain["groups"]:
            if not isinstance(group, dict) or not isinstance(group.get("entries"), list):
                continue
            for entry in group["entries"]:
                rid = entry.get("id", "?") if isinstance(entry, dict) else "?"
                if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS:
                    findings.append(f"{rid}: keys must be {sorted(ENTRY_KEYS)}")
                    continue
                if "|" in entry["concern"] + entry["menu"]:
                    findings.append(f"{rid}: concern and menu must not contain '|'")
                if not ID.fullmatch(rid) or not rid.startswith(name + "."):
                    findings.append(f"{rid}: ID must start with '{name}.' and use lowercase dotted words")
                if rid in seen:
                    findings.append(f"{rid}: duplicate ID")
                seen.add(rid)
                if not entry["path"].startswith("engineer/standards/") or not (base/entry["path"]).is_file():
                    findings.append(f"{rid}: {entry['path']} does not exist")
                menu = entry["menu"]
                if entry["whole"] == (entry["section"] is not None):
                    findings.append(f"{rid}: set exactly one of section or whole")
                elif entry["whole"] and "**whole**" not in menu:
                    findings.append(f"{rid}: whole entry menu must say **whole**")
                elif not entry["whole"] and _menu_section(menu) != entry["section"]:
                    findings.append(f"{rid}: menu must start with §{entry['section']}")
                if INCLUDE.findall(menu) != entry["includes"]:
                    findings.append(f"{rid}: includes must match the menu's 'include §N' text")
    for alias, target in data.get("aliases", {}).items():
        if alias in seen:
            findings.append(f"alias {alias} shadows an ID")
        if target not in seen:
            findings.append(f"alias {alias} targets unknown ID {target}")
    return findings


def checked_routing():
    """Load routing.json and fail closed with a structured error when it is malformed."""
    data = load_routing()
    findings = validate_routing(data)
    if findings:
        raise Failure("standards-routing-invalid", "; ".join(findings[:5]), 2, findings=findings)
    return data


def catalog():
    """Every routing ID with its concern, document, main selector and required companions."""
    entries = {}
    for domain in checked_routing()["domains"]:
        name = domain["domain"]
        for group in domain["groups"]:
            for entry in group["entries"]:
                suffix = entry["id"][len(name) + 1:]
                includes = [(p["path"], p["section"]) for p in domain.get("prefix_includes", [])
                            if suffix.startswith(p["prefix"] + ".")]
                includes += [(entry["path"], section) for section in entry["includes"]]
                entries[entry["id"]] = {"concern": entry["concern"], "path": entry["path"],
                                        "selector": entry["section"], "whole": entry["whole"], "includes": includes}
    return entries


def aliases():
    return checked_routing().get("aliases", {})


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
    entries, renamed, files = catalog(), aliases(), {}
    for requested in ids:
        rid, _, alternative = requested.partition("@")
        entry = entries.get(renamed.get(rid, rid))
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
    """Structural findings plus every row's main section and companions resolving to real headings."""
    findings = validate_routing(load_routing())
    if findings:
        return findings
    for rid, entry in catalog().items():
        if entry["selector"] is None and not entry["whole"]:
            findings.append(f"{rid}: neither a §selector nor **whole**")
            continue
        try:
            resolve([rid])
        except Failure as exc:
            findings.append(exc.message)
    return findings
