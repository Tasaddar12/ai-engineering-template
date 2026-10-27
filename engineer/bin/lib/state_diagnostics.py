"""Read-only diagnostics for the bounded, closed STATE digest contract."""
import re
from . import records
from .core import read


def findings():
    path = records.planning()/"STATE.md"
    content = read(path)
    result = []
    def report(check, message):
        result.append({"path": str(path), "check": check, "message": message, "error": message})
    required = ("Current Position", "Accumulated Context", "Session Continuity")
    allowed = {*required, "Project Reference", "Deferred Items"}
    headings = re.findall(r"(?m)^## (.+?)\s*$", content)
    for heading in required:
        if heading not in headings:
            report("state-contract", "Missing required STATE section: "+heading)
    for heading in headings:
        if heading not in allowed:
            report("state-contract", heading+" is not part of the STATE contract")
    for heading, cap in (("Decisions", 5), ("Roadmap Evolution", 5), ("Blockers/Concerns", 10)):
        section = re.search(r"(?ms)^### "+re.escape(heading)+r"\s*\n(.*?)(?=^##|\Z)", content)
        count = len(re.findall(r"(?m)^- ", section[1])) if section else 0
        if count > cap:
            report("state-caps", heading+" exceeds its digest section cap; preserve unresolved entries and reconcile their owner")
    if len(content.splitlines()) > 150:
        report("state-budget", "STATE exceeds its 150-line digest budget")
    for record in (records.planning()/"STATE.md", records.planning()/"PROJECT.md", records.planning()/"ROADMAP.md"):
        text = read(record)
        if re.search(r"~~[^\n]+~~|(?i:\(closed\))", text):
            message = "Entry closed in place; move retired content through its explicit archive route"
            result.append({"path": str(record), "check": "retirement-markers", "message": message, "error": message})
    requirements = records.planning()/"REQUIREMENTS.md"
    for identifier, phase, status in re.findall(r"(?m)^\|\s*([A-Z][A-Z0-9]*-\d+)\s*\|\s*(?:Phase\s+)?(\d+(?:\.\d+)?)\s*\|\s*([^|]+)\|", read(requirements)):
        owner = next((item for item in records.roadmap_phases() if item["number"] == records.number(phase)), None)
        if owner and records.phase_completed(owner) and status.strip() == "Pending":
            message = identifier+" is still Pending under a complete phase"
            result.append({"path": str(requirements), "check": "requirement-completion", "message": message, "error": message})
    return result
