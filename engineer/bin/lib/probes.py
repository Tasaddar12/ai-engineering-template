"""Deterministic specification boundary probes and section extraction."""
import json
import re
from .core import Failure, read, safe_path

PROBES = {
    "adjacency": (r"merge|overlap|interval|dedup|duplicates?|equal|touch|collid", "When two things are exactly equal or just touch, do they merge, collide, or separate?"),
    "boundary": (r"round|decimals?|amount|price|threshold|min(?:imum)?|max(?:imum)?|limit|range", "What happens exactly at each min/max/threshold — and one step either side?"),
    "empty": (r"list|array|string|collection|items|elements|truncate|interval", "What is the result for empty, single-element, or null input?"),
    "encoding": (r"string|characters?|unicode|grapheme|encoding|bytes?", "Whose definition of length/equality applies — bytes, code points, grapheme clusters, or normalized form?"),
    "ordering": (r"list|sort|order|merge|dedup|duplicates?|interval", "When elements compare equal, is output order specified and stable?"),
    "precision": (r"round|decimal|float|amount|price|money|precision|number|overflow", "Where can precision loss, overflow, or rounding/tie-breaking occur — and what is the exact contract (e.g. half-up vs half-to-even, ceil/floor/truncate)?"),
}


def edge(args):
    source = args.arg(0, args.get("requirements"))
    try:
        requirements = json.loads(read(safe_path(source)))
        resolutions = json.loads(read(safe_path(args.get("resolutions")))) if args.has("resolutions") else []
    except (ValueError, TypeError, OSError) as exc:
        raise Failure("invalid-probe-input", str(exc), 2) from exc
    if not isinstance(requirements, list) or not isinstance(resolutions, list):
        raise Failure("invalid-probe-input", "Requirements and resolutions must be arrays", 2)
    indexed = {}
    for item in resolutions:
        if not isinstance(item, dict) or not item.get("requirement_id") or item.get("category") not in PROBES:
            raise Failure("invalid-resolution", "Resolution requires requirement_id and recognized category", 2)
        if item.get("status") == "resolved" and (item.get("verification") not in ("explicit", "backstop") or not item.get("resolution")):
            raise Failure("invalid-resolution", "Resolved probes require verification and resolution", 2)
        if item.get("status") == "dismissed" and not item.get("reason"):
            raise Failure("invalid-resolution", "Dismissed probes require a reason", 2)
        if item.get("status") not in ("resolved", "dismissed", "unresolved"):
            raise Failure("invalid-resolution", "Unknown resolution status", 2)
        indexed[(str(item["requirement_id"]), item["category"])] = item
    items, unclassified = [], 0
    for requirement in requirements:
        if not isinstance(requirement, dict) or not isinstance(requirement.get("id"), str) or not isinstance(requirement.get("text"), str):
            raise Failure("invalid-requirement", "Each requirement requires string id and text", 2)
        categories = [category for category, (pattern, _) in PROBES.items() if re.search(pattern, requirement["text"], re.I)]
        if not categories:
            unclassified += 1
        for category in categories:
            item = {"requirement_id": requirement["id"], "category": category, "status": "unresolved",
                    "verification": None, "resolution": None, "reason": None, "probe": PROBES[category][1]}
            resolution = indexed.get((requirement["id"], category))
            if resolution:
                item.update({key: resolution.get(key) for key in ("status", "verification", "resolution", "reason")})
            items.append(item)
    resolved = sum(item["status"] in ("resolved", "dismissed") for item in items)
    return {"items": items, "coverage": {"applicable": len(items), "resolved": resolved, "unresolved": len(items)-resolved,
            "unclassified": unclassified, "byVerification": {key: sum(item["verification"] == key for item in items) for key in ("explicit", "backstop")}}}


def section(args):
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
    items = [m.group(1).strip() for m in re.finditer(r"(?m)^\s*(?:[-*]|\d+[.)])\s+(.+)$", body)]
    return {"supplied": True, "items": items}
