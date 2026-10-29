"""Deterministic specification boundary probes and section extraction."""
import re
from . import edge_probe
from .core import Failure, input_json, read, safe_path

def edge(args):
    """Edge probe CLI verb: input handling here, the oracle algorithm in ``edge_probe``."""
    source = args.arg(0, args.get("requirements", args.get("input")))
    try:
        requirements = input_json(None if args.has("stdin") else source)
        resolutions = input_json(args.get("resolutions")) if args.has("resolutions") else []
    except (ValueError, TypeError, OSError) as exc:
        raise Failure("invalid-probe-input", str(exc), 2) from exc
    if not isinstance(requirements, list) or not isinstance(resolutions, list):
        raise Failure("invalid-probe-input", "Requirements and resolutions must be arrays", 2)
    try:
        return edge_probe.analyze_coverage(requirements, resolutions)
    except ValueError as exc:
        raise Failure("invalid-probe-input", str(exc), 2) from exc


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


def section_status(args):
    """Expose the canonical strict section-presence check for workflow gates."""
    from .spec_section import VALID_KEYS, spec_section_status
    path, key = safe_path(args.need()), args.need(1)
    if key not in VALID_KEYS:
        raise Failure("unknown-spec-section", key, 2)
    return spec_section_status(path, key)


def ui(args):
    """Run the canonical UI consideration probe behind the runtime CLI."""
    from . import ui_consideration_probe
    source = args.arg(0, args.get("input"))
    resolutions_source = args.get("resolutions", args.arg(1))
    try:
        elements = input_json(None if args.has("stdin") else source)
        resolutions = input_json(resolutions_source) if resolutions_source is not None else []
        if not isinstance(elements, list) or not isinstance(resolutions, list):
            raise ValueError("elements and resolutions must be arrays")
        return ui_consideration_probe.analyze_coverage(elements, resolutions)
    except (ValueError, TypeError, OSError) as exc:
        raise Failure("invalid-ui-probe-input", str(exc), 2) from exc
