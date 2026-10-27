"""Status-only requirement traceability updates preserve requirement wording."""
import re
from . import records
from .core import Failure, planning_lock, read, write

STATUSES = {"Pending", "In Progress", "Complete", "Deferred", "Blocked"}
ROW = re.compile(r"(?m)^(\|\s*([A-Z][A-Z0-9_-]*-\d+)\s*\|\s*([^|]+?)\s*\|)\s*([^|]+?)\s*\|(.*)$")


def command(args, action):
    path = records.planning()/"REQUIREMENTS.md"
    text = read(path)
    rows = [{"Requirement": m[2], "Phase": m[3].strip(), "Status": m[4].strip()} for m in ROW.finditer(text)]
    if action == "outstanding":
        pending = [row for row in rows if row["Status"] not in ("Complete", "Deferred")]
        return {"outstanding": pending, "count": len(pending)}
    if action == "set-status":
        identifier, status = args.need(), args.need(1)
        if status not in STATUSES:
            raise Failure("bad-status", status)
        matched = [row for row in rows if row["Requirement"] == identifier]
        if len(matched) != 1:
            raise Failure("unknown-requirement", identifier)
        ids = [identifier]
    else:
        status = "Complete"
        target = records.number(args.need())
        ids = args.all("requirements") or [row["Requirement"] for row in rows if re.search(r"\bPhase\s+(\d+(?:\.\d+)?)", row["Phase"]) and records.number(re.search(r"\bPhase\s+(\d+(?:\.\d+)?)", row["Phase"])[1]) == target]
        if not ids:
            raise Failure("no-requirements", "Phase has no requirement traceability rows")
    known = {row["Requirement"] for row in rows}
    unknown = [identifier for identifier in ids if identifier not in known]
    changed = [row["Requirement"] for row in rows if row["Requirement"] in ids and row["Status"] != status]
    with planning_lock():
        if read(path) != text:
            raise Failure("requirements-drift", "Traceability changed before status update")
        updated = ROW.sub(lambda m: m[1]+" "+status+" |"+m[5] if m[2] in ids else m[0], text)
        write(path, updated)
    if action == "set-status":
        return {"changed": bool(changed), "previous": matched[0]["Status"], "status": status, "id": identifier}
    return {"changed": changed, "unknown": unknown}
