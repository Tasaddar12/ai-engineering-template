"""Cross-record diagnostics; findings never manufacture approval or intent."""
import re
from . import records
from .core import Failure, read
from .text import split_frontmatter


def findings():
    base = records.planning()
    result = []
    def report(path, message):
        result.append({"path": str(path), "error": message})
    if any((base/name).is_file() for name in ("PROJECT.md", "STATE.md", "ROADMAP.md", "REQUIREMENTS.md")):
        for name in ("PROJECT.md", "STATE.md", "ROADMAP.md", "REQUIREMENTS.md"):
            if not (base/name).is_file():
                report(base/name, "Core planning record is absent")
    roadmap = records.roadmap_phases()
    ids = [phase["number"] for phase in roadmap]
    if len(ids) != len(set(ids)):
        report(base/"ROADMAP.md", "Duplicate roadmap phase identifiers")
    directories = {records.number(path.name): path for path in records.phases()}
    if len(directories) != len(records.phases()):
        report(base/"phases", "Duplicate phase directory identifiers")
    for identifier, directory in directories.items():
        if identifier not in ids:
            report(directory, "Phase directory has no roadmap entry")
    requirements = read(base/"REQUIREMENTS.md")
    declared = set(re.findall(r"(?m)^- \[[ x]\]\s*\*\*([A-Z][A-Z0-9]*-\d+)\*\*", requirements))
    trace = {}
    for identifier, phase, status in re.findall(r"(?m)^\|\s*([A-Z][A-Z0-9]*-\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|", requirements):
        trace.setdefault(identifier, []).append((phase, status))
        if declared and identifier not in declared:
            report(base/"REQUIREMENTS.md", "Traceability references undeclared requirement "+identifier)
        match = re.fullmatch(r"(?:Phase\s+)?(\d+(?:\.\d+)?)", phase, re.I)
        if match and records.number(match[1]) not in ids:
            report(base/"REQUIREMENTS.md", "Traceability references absent phase "+phase)
        if match and records.number(match[1]) in ids:
            owner = next(item for item in roadmap if item["number"] == records.number(match[1]))
            if identifier not in owner["requirements"]:
                report(base/"REQUIREMENTS.md", "Traceability ownership disagrees with roadmap for "+identifier)
        checkbox = re.search(r"(?m)^- \[([ x])\]\s*\*\*"+re.escape(identifier)+r"\*\*", requirements)
        if checkbox and (checkbox[1] == "x") != (status.strip().casefold() == "complete"):
            report(base/"REQUIREMENTS.md", "Requirement checkbox/status disagree for "+identifier)
    for identifier, entries in trace.items():
        if len(entries) != 1:
            report(base/"REQUIREMENTS.md", "Duplicate traceability row "+identifier)
    for phase in roadmap:
        directory = directories.get(phase["number"])
        if directory is None:
            report(base/"ROADMAP.md", "Roadmap phase lacks directory: "+phase["number"])
            continue
        for identifier in phase["requirements"]:
            if identifier not in declared:
                report(base/"ROADMAP.md", "Phase references undeclared requirement "+identifier)
        for dependency in re.findall(r"(?i)\bPhase\s+(\d+(?:\.\d+)?)", phase["depends_on"]):
            if records.number(dependency) not in ids or records.number(dependency) == phase["number"]:
                report(base/"ROADMAP.md", "Invalid phase dependency "+dependency)
        for path in directory.glob("*.md"):
            try:
                metadata, body = split_frontmatter(read(path))
            except Failure:
                continue  # Schema diagnostics own parse errors.
            if "phase" in metadata:
                try:
                    if records.number(metadata["phase"]) != phase["number"]:
                        report(path, "Frontmatter phase disagrees with containing directory")
                except ValueError:
                    report(path, "Frontmatter phase is not a phase identifier")
            if path.name.endswith("-SUMMARY.md") and not path.with_name(path.name.replace("-SUMMARY.md", "-PLAN.md")).is_file():
                report(path, "Summary has no corresponding plan")
            if path.name.endswith("-PLAN.md"):
                dependencies = metadata.get("depends_on", [])
                if not isinstance(dependencies, list):
                    dependencies = []  # Schema diagnostics own the type error.
                for dependency in dependencies:
                    if not isinstance(dependency, str) or not (directory/(dependency+"-PLAN.md")).is_file():
                        report(path, "Plan dependency is absent from this phase: "+str(dependency))
                if records.phase_completed(phase) and not path.with_name(path.name.replace("-PLAN.md", "-SUMMARY.md")).is_file():
                    report(path, "Completed roadmap phase has an incomplete plan")
    try:
        state = records.state_view()
    except Failure as exc:
        report(base/"STATE.md", exc.message)
        state = {}
    current = re.match(r"^(\d+(?:\.\d+)?)\b", str(state.get("phase", "")))
    if current and records.number(current[1]) not in ids:
        report(base/"STATE.md", "Current position references absent phase")
    try:
        progress = split_frontmatter(read(base/"STATE.md"))[0].get("progress")
    except Failure:
        progress = None
    if isinstance(progress, dict):
        derived = records.derived_progress()
        for key, value in derived.items():
            if key in progress and progress[key] != value:
                report(base/"STATE.md", "Derived progress differs from artifacts: "+key)
    for path in base.rglob("*.md"):
        if any(part in ("archive", "milestones", "completed") for part in path.relative_to(base).parts):
            continue
        content = read(path)
        if re.search(r"(?mi)^\s*(?:-\s*)?~~.+~~|^\s*\*\*(?:Closed|Retired|Superseded)(?::\*\*|\*\*:)", content):
            report(path, "Retired entry remains in an active record; use explicit archive selection")
    return result
