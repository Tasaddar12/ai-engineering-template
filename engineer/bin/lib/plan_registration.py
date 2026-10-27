"""Guarded replacement of only a phase's explicitly labelled plan checklist."""
import re
from .core import Failure


def rewrite(block, prefix, values, summary=None):
    if not values:
        raise Failure("bad-plan", "Provide at least one explicit plan ID and title")
    requested = []
    for value in values:
        if "\n" in value or "\r" in value:
            raise Failure("bad-plan", "Plan entries must be a single line")
        match = re.fullmatch(re.escape(prefix)+r"-([0-9]{2})\s*:\s*([^\r\n]+)", value.strip())
        if not match or not match[2].strip():
            raise Failure("bad-plan", "Plan entries require the exact padded phase, two ASCII ordinal digits and a nonempty single-line title")
        requested.append((prefix+"-"+match[1], match[2].strip()))
    if len({identifier for identifier, _ in requested}) != len(requested):
        raise Failure("bad-plan", "Duplicate requested plan identifier")
    if summary is not None and (not isinstance(summary, str) or not summary.strip() or "\n" in summary or "\r" in summary):
        raise Failure("bad-plan", "Plan summary must be a nonempty single line")

    lines = block.splitlines(keepends=True)
    markers = [index for index, line in enumerate(lines) if line.strip() == "Plans:"]
    candidates = {index for index, line in enumerate(lines)
                  if re.match(r"^\s*[-*+]\s+(?:\[[^\]]*\]\s*)?[0-9]+(?:\.[0-9]+)?-[^:\s]*\s*:", line)}
    if len(markers) > 1 or (not markers and candidates):
        raise Failure("bad-existing-plan", "Existing plan rows require one unambiguous Plans: owner")
    checked, existing_ids, owned = set(), set(), set()
    start = stop = None
    if markers:
        start = markers[0]+1
        while start < len(lines) and not lines[start].strip():
            start += 1
        stop = start
        while stop < len(lines) and re.match(r"^\s*[-*+]\s", lines[stop]):
            match = re.fullmatch(r"- \[([ x])\]\s+("+re.escape(prefix)+r"-[0-9]{2})\s*:\s*([^\r\n]+)\r?\n?", lines[stop])
            if not match or not match[3].strip() or match[2] in existing_ids:
                raise Failure("bad-existing-plan", "Existing plan checklist is malformed, duplicated or belongs to another phase")
            existing_ids.add(match[2])
            if match[1] == "x":
                checked.add(match[2])
            owned.add(stop)
            stop += 1
        following = stop
        while following < len(lines) and not lines[following].strip():
            following += 1
        if following != stop and following < len(lines) and re.match(r"^\s*[-*+]\s", lines[following]):
            raise Failure("bad-existing-plan", "Unlabelled checklist rows after Plans: are ambiguous")
    if candidates-owned:
        raise Failure("bad-existing-plan", "Plan rows outside their labelled checklist must be reconciled first")
    if checked-{identifier for identifier, _ in requested}:
        raise Failure("completed-plan", "Completed plan identifiers cannot be removed by registration")

    rows = "".join(f"- [{'x' if identifier in checked else ' '}] {identifier}: {title}\n" for identifier, title in requested)
    if markers:
        # Keep every authored byte before and after the actual checklist rows.
        lines[start:stop] = [rows]
        updated = "".join(lines)
    else:
        updated = block.rstrip()+"\n\nPlans:\n"+rows+"\n"
    count = summary.strip() if summary is not None else str(len(requested))+" plans"
    field = re.compile(r"(?m)^(\*\*Plans(?::\*\*|\*\*:))[^\n]*$")
    if field.search(updated):
        updated = field.sub(lambda match: match[1]+" "+count, updated, count=1)
    else:
        insertion = updated.index("Plans:")
        updated = updated[:insertion]+"**Plans**: "+count+"\n\n"+updated[insertion:]
    return updated, [identifier+": "+title for identifier, title in requested]
