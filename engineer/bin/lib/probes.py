"""Deterministic specification boundary probes and section extraction."""
import json
import re
from .core import Failure, input_json, read, safe_path

PROBES = {
    "adjacency": (r"merge|overlap|interval|dedup|duplicates?|equal|touch|collid", "When two things are exactly equal or just touch, do they merge, collide, or separate?"),
    "boundary": (r"round|decimals?|amount|price|threshold|min(?:imum)?|max(?:imum)?|limit|range", "What happens exactly at each min/max/threshold — and one step either side?"),
    "empty": (r"list|array|string|collection|items|elements|truncate|interval", "What is the result for empty, single-element, or null input?"),
    "encoding": (r"string|characters?|unicode|grapheme|encoding|bytes?", "Whose definition of length/equality applies — bytes, code points, grapheme clusters, or normalized form?"),
    "ordering": (r"list|sort|order|merge|dedup|duplicates?|interval", "When elements compare equal, is output order specified and stable?"),
    "precision": (r"round|decimal|float|amount|price|money|precision|number|overflow", "Where can precision loss, overflow, or rounding/tie-breaking occur — and what is the exact contract (e.g. half-up vs half-to-even, ceil/floor/truncate)?"),
    "idempotency": (r"state|updat|sav|creat|persist|retry|retries|submit|delet", "What happens if this runs twice on the same input?"),
    "concurrency": (r"state|updat|sav|creat|persist|retry|submit|delet|network|request|file|read|write|api|database", "If interrupted or run in parallel, what is guaranteed?"),
}
SHAPES = {
    "numeric-range": (r"\bround|decimal|amount|price|threshold|minimum|maximum|limit|range|number|precision", ("boundary", "precision")),
    "collection": (r"\blist|array|collection|items|elements|sort|merge|dedup|interval", ("adjacency", "empty", "ordering")),
    "text": (r"\bstring|character|text|unicode|encoding|grapheme|bytes", ("empty", "encoding")),
    "stateful": (r"\bstate|updat|sav|creat|persist|retry|retries|submit|delet", ("idempotency", "concurrency")),
    "io": (r"\bnetwork|request|file|read|write|api|database|socket", ("concurrency",)),
}


def edge(args):
    source = args.arg(0, args.get("requirements", args.get("input")))
    try:
        requirements = input_json(None if args.has("stdin") else source)
        resolutions = input_json(args.get("resolutions")) if args.has("resolutions") else []
    except (ValueError, TypeError, OSError) as exc:
        raise Failure("invalid-probe-input", str(exc), 2) from exc
    if not isinstance(requirements, list) or not isinstance(resolutions, list):
        raise Failure("invalid-probe-input", "Requirements and resolutions must be arrays", 2)
    indexed = {}
    for item in resolutions:
        if not isinstance(item, dict) or not item.get("requirement_id") or item.get("category") not in (*PROBES, "unclassified"):
            raise Failure("invalid-resolution", "Resolution requires requirement_id and recognized category", 2)
        if item.get("status") == "resolved" and (item.get("verification") not in ("explicit", "backstop") or not item.get("resolution")):
            raise Failure("invalid-resolution", "Resolved probes require verification and resolution", 2)
        if item.get("status") == "dismissed" and not item.get("reason"):
            raise Failure("invalid-resolution", "Dismissed probes require a reason", 2)
        if item.get("status") not in ("resolved", "dismissed", "unresolved"):
            raise Failure("invalid-resolution", "Unknown resolution status", 2)
        key = (str(item["requirement_id"]), item["category"])
        if key in indexed:
            raise Failure("duplicate-resolution", str(key), 2)
        indexed[key] = item
    items, unclassified, seen, classifications = [], 0, set(), []
    for requirement in requirements:
        if not isinstance(requirement, dict) or not isinstance(requirement.get("id"), str) or not isinstance(requirement.get("text"), str):
            raise Failure("invalid-requirement", "Each requirement requires string id and text", 2)
        if not requirement["text"].strip() or requirement["id"] in seen:
            raise Failure("invalid-requirement", "Requirement text must be concrete and identifiers unique", 2)
        seen.add(requirement["id"])
        shapes = requirement.get("shapes")
        if shapes is None:
            shapes = [shape for shape, (pattern, _) in SHAPES.items() if re.search(pattern, requirement.get("text_en", requirement["text"]), re.I)]
        if not isinstance(shapes, list) or any(shape not in SHAPES for shape in shapes):
            raise Failure("invalid-shape", "Use numeric-range, collection, text, stateful or io", 2)
        classifications.append({"id": requirement["id"], "shapes": shapes, "requiresConfirmation": "shapes" not in requirement})
        categories = sorted({category for shape in shapes for category in SHAPES[shape][1]})
        if not categories:
            unclassified += 1
            categories = ["unclassified"]
        for category in categories:
            item = {"requirement_id": requirement["id"], "category": category, "status": "unresolved",
                    "verification": None, "resolution": None, "reason": None,
                    "probe": PROBES[category][1] if category in PROBES else "Review the requirement shape manually; no finite shape was recognized"}
            resolution = indexed.get((requirement["id"], category))
            if resolution:
                if category == "unclassified" and resolution.get("status") == "resolved":
                    raise Failure("unclassified-resolution", "Classify the requirement before resolving an invented edge", 2)
                item.update({key: resolution.get(key) for key in ("status", "verification", "resolution", "reason")})
            items.append(item)
    raised = {(item["requirement_id"], item["category"]) for item in items}
    if set(indexed)-raised:
        raise Failure("orphan-resolution", "A resolution does not match a raised edge", entries=sorted(set(indexed)-raised))
    resolved = sum(item["status"] in ("resolved", "dismissed") for item in items)
    return {"items": items, "classifications": classifications, "behaviorVerified": False,
            "coverage": {"applicable": len(items), "resolved": resolved, "unresolved": len(items)-resolved,
            "unclassified": unclassified, "byVerification": {key: sum(item["verification"] == key for item in items) for key in ("explicit", "backstop")}}}


def section(args):
    from .issue_format import visible_lines
    path, kind = safe_path(args.need()), args.need(1)
    if kind not in ("edges", "prohibitions"):
        raise Failure("unknown-spec-section", kind, 2)
    content = read(path)
    heading = r"edge(?: cases?)?|boundar" if kind == "edges" else r"prohibition|must.not|non.goals|forbidden"
    match = re.search(r"(?mi)^(#{1,6})\s+[^\n]*(?:"+heading+r")[^\n]*$", content)
    if not match:
        return {"supplied": False, "items": []}
    end = re.search(r"(?m)^#{1,"+str(len(match[1]))+r"}\s", content[match.end():])
    body = content[match.end():match.end()+end.start() if end else len(content)]
    items, in_table = [], False
    for line in visible_lines(body):
        bullet = re.match(r"^\s*(?:[-*]|\d+[.)])\s+(.+)$", line)
        if bullet:
            item = bullet[1].strip()
            if not re.fullmatch(r"(?:\[[ xX]\]\s*)?(?:TBD|TODO|none|n/a|—|-)", item, re.I):
                items.append(item)
        if "|" not in line:
            in_table = False
            continue
        cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if len(cells) > 1 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            in_table = True
        elif in_table and any(cell and not re.fullmatch(r"TBD|TODO|none|n/a|—|-", cell, re.I) for cell in cells):
            items.append(" | ".join(cells))
    return {"supplied": bool(items), "items": items}
