"""Evidence inventory and conservative repair proposals for planning records.

Reuses the runtime's readers and conformance checks. The only automatic writes
restore an unambiguous STATE heading or its roadmap-derived progress metadata.
No requirement, checklist, authorization, prose or historical decision changes.
"""
import difflib
import hashlib
import os
import re
import stat
from pathlib import Path
from urllib.parse import unquote

from . import gitops, phases, quick, requirements, state, validate, verification
from .paths import read_text, write_text
from .results import VerbError, require
from .roadmap import Roadmap, as_number, pad
from .text import (find_section, join_frontmatter, section_body,
                   split_frontmatter, table_records)

# Keep the lexical source namespace so resolving a linked `.ai`/host directory
# cannot hide the link before the fingerprint reads its canonical templates.
TEMPLATE_NAMESPACE = Path(__file__).absolute().parents[2]
TEMPLATES = TEMPLATE_NAMESPACE / "templates"
HEADING = re.compile(r"^(#{2,3})[ \t]+(.+?)[ \t]*$", re.M)
REQUIREMENT = re.compile(r"^\s*-\s*\[[ xX]\]\s*\*\*([\w.-]+)\*\*:", re.M)
LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)")
ADR_STATUSES = ("proposed", "accepted", "rejected", "superseded", "deprecated")


def _guard_path(path, boundary):
    """Reject links/reparse points before resolving or traversing their target.

    Python 3.11 has no Path.is_junction. lstat's Windows attribute flag covers
    junctions and other reparse points as well as ordinary symlinks.
    """
    path, boundary = Path(path).absolute(), Path(boundary).absolute()
    require(".." not in path.parts and path.is_relative_to(boundary),
            "path escapes planning boundary: " + str(path), "path-escape")
    chain = [*reversed(boundary.parents), boundary]
    cursor = boundary
    for component in path.relative_to(boundary).parts:
        cursor = cursor / component
        chain.append(cursor)
    for cursor in chain:
        try:
            info = cursor.lstat()
        except FileNotFoundError:
            continue  # A missing record is diagnosed by the normal reader.
        linked = stat.S_ISLNK(info.st_mode) or bool(
            getattr(info, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
        require(not linked, "linked planning/template path is not supported: " + str(cursor), "linked-path")
    require(path.resolve().is_relative_to(boundary.resolve()),
            "resolved path escapes planning boundary: " + str(path), "path-escape")
    return path


def _record(workspace, path):
    """Repository-relative lexical identity; never follow a record's target."""
    path = Path(path).absolute()
    require(path.is_relative_to(workspace.root), "record escapes repository", "path-escape")
    return path.relative_to(workspace.root).as_posix()


def _checked_files(directory, boundary, recursive=True):
    """Preflight the tree before any record content is read, without following links."""
    directory = _guard_path(directory, boundary)
    files, pending = [], [directory]
    while pending:
        current = pending.pop()
        if not current.is_dir():
            continue
        with os.scandir(current) as entries:
            children = sorted(entries, key=lambda entry: entry.name)
        for entry in children:
            path = _guard_path(Path(entry.path), boundary)
            if entry.is_dir(follow_symlinks=False):
                if recursive:
                    pending.append(path)
            elif path.suffix == ".md" and entry.is_file(follow_symlinks=False):
                files.append(path)
    return sorted(files)


def _preflight(workspace):
    # The planning root itself is checked before require_planning or lock creation.
    # Canonical templates use the installed runtime namespace as their boundary;
    # a global host installation may legitimately be outside the project root.
    files = _checked_files(workspace.planning, workspace.root)
    templates = _checked_files(TEMPLATES, TEMPLATE_NAMESPACE, recursive=False)
    workspace.require_planning()
    return files, templates


def _hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _visible(content):
    """Ignore instructional links and headings inside fenced examples."""
    return re.sub(r"(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1[^\n]*$", "", content)


def _skeleton(name):
    content = read_text(TEMPLATES / name)
    match = re.search(r"(?ms)^```markdown\s*\n(.*?)^```\s*$", content)
    require(match is not None, "template has no File Template: " + name,
            "bad-template")
    return match.group(1)


def _headings(name):
    return [(len(level), title) for level, title in HEADING.findall(_skeleton(name))
            if "[" not in title and not title.startswith("Phase ")]


def _finding(items, check, record, message, kind="semantic", fix=""):
    items.append({"check": check, "record": record, "message": message,
                  "kind": kind, "fix": fix})


def _metadata(path, workspace, findings):
    try:
        return split_frontmatter(read_text(path))
    except VerbError as exc:
        _finding(findings, "frontmatter", _record(workspace, path), str(exc))
        return {}, read_text(path)


def _summary_commits(data, body):
    """Canonical SUMMARY records hash evidence in Task Commits, not a count."""
    declared = data.get("commits", [])
    hashes = [item for item in declared if isinstance(item, str)
              and re.fullmatch(r"[0-9a-fA-F]{7,64}", item)] if isinstance(declared, list) else []
    hashes += re.findall(r"\b[0-9a-fA-F]{7,64}\b", section_body(body, "Task Commits", 2))
    return sorted(set(hashes))


def _check_headings(path, body, template, workspace, findings, optional=()):
    present = HEADING.findall(_visible(body))
    for level, title in _headings(template):
        if title in optional:
            continue
        if ("#" * level, title) not in present:
            _finding(findings, "template-section", _record(workspace, path),
                     "missing section: " + title, "structure",
                     "compare the complete templates/" + template + "; retain authored prose")


def _state_headings(body):
    """Propose a heading only when all its unique field anchors remain intact."""
    changes = []
    for title, pattern, keys in (
            ("Current Position", state.POSITION, ("Phase", "Plan", "Status", "Last activity")),
            ("Session Continuity", state.CONTINUITY, ("Last session", "Stopped at", "Resume file"))):
        if find_section(body, title, 2):
            continue
        if any(name == title for _, name in HEADING.findall(_visible(body))):
            continue  # Wrong heading level needs an explicit, separate proposal.
        matches = list(pattern.finditer(body))
        if [item.group("key") for item in matches] != list(keys):
            continue
        # Anchors must be a single contiguous field block, outside fenced text.
        gap = body[matches[0].start():matches[-1].end()]
        if "#" in gap or len(gap.splitlines()) != len(keys):
            continue
        if _visible(body).count(matches[0].group(0)) != 1:
            continue
        changes.append((matches[0].start(), "## " + title + "\n\n", title))
    digest = list(re.finditer(r"^### (Decisions|Pending Todos|Blockers/Concerns|Roadmap Evolution)\s*$",
                             _visible(body), re.M))
    if not find_section(body, "Accumulated Context", 2) and digest:
        # Offset lookup uses original text because example removal shifts offsets.
        first = re.search(r"^### " + re.escape(digest[0].group(1)) + r"[ \t]*$", body, re.M)
        boundary = re.search(r"^## ", body[first.end():], re.M)
        end = first.end() + boundary.start() if boundary else len(body)
        known = {name for name, level in validate.STATE_SECTIONS if level == 3}
        subheads = [name for level, name in HEADING.findall(body[first.start():end])]
        if set(subheads) == known and len(subheads) == len(known):
            changes.append((first.start(), "## Accumulated Context\n\n", "Accumulated Context"))
    updated = body
    for offset, prefix, _ in sorted(changes, reverse=True):
        updated = updated[:offset] + prefix + updated[offset:]
    return updated, [title for _, _, title in changes]


def _repair_candidate(workspace, findings, roadmap):
    if not workspace.state.is_file():
        return None
    try:
        parsed = state.State(workspace)
    except VerbError:
        return None
    original = read_text(workspace.state)
    parsed.body, headings = _state_headings(parsed.body)
    operations = [{"operation": "restore-state-heading", "section": title} for title in headings]
    # Counters copy authoritative checkboxes; contradictory evidence requires
    # reconciliation first, even though the counters themselves are derived.
    blocked = any(item["check"] in {"completion-evidence", "phase-id", "plan-id", "roadmap-missing"}
                  for item in findings)
    before = dict(parsed.frontmatter)
    if roadmap.exists and not blocked:
        parsed.derive_frontmatter(roadmap)
        if "status" not in before:
            parsed.frontmatter.pop("status", None)  # Never infer authored status.
        if parsed.frontmatter != before:
            operations.append({"operation": "derive-state-progress", "source": ".planning/ROADMAP.md"})
    if not operations:
        return None
    after = join_frontmatter(parsed.frontmatter, parsed.body)
    return {"id": "state-structure", "record": _record(workspace, workspace.state),
            "operations": operations, "before_sha256": _hash(original),
            "after_sha256": _hash(after), "diff": "".join(difflib.unified_diff(
                original.splitlines(True), after.splitlines(True),
                fromfile=_record(workspace, workspace.state),
                tofile=_record(workspace, workspace.state))), "content": after}


def _audit(workspace):
    files, templates = _preflight(workspace)
    # Fingerprint includes archived records and templates: the review remains
    # valid only while every possible cited planning source is unchanged.
    snapshot = [(_record(workspace, path), _hash(read_text(path))) for path in files]
    snapshot += [("templates/" + path.name, _hash(read_text(path)))
                 for path in templates]
    fingerprint = _hash(repr(snapshot))
    if validate.unfilled(workspace):
        return {"status": "unfilled", "fingerprint": fingerprint,
                "inventory": [{"record": name, "sha256": digest} for name, digest in snapshot
                              if not name.startswith("templates/")],
                "findings": [], "finding_count": 0, "checks": [], "repairs": [],
                "note": "adoption skeleton is instructional; run onboarding"}, []
    base = validate.run(workspace)
    findings = [dict(item, kind="conformance") for item in base["warnings"]]
    roadmap = Roadmap(workspace)
    if not roadmap.exists:
        _finding(findings, "roadmap-missing", ".planning/ROADMAP.md", "roadmap is missing")
    for name, template, optional in (("PROJECT.md", "project.md", ("Business Context",)),
                                     ("REQUIREMENTS.md", "requirements.md", ()),
                                     ("STATE.md", "state.md", ())):
        path = workspace.planning / name
        if path.is_file():
            _, body = _metadata(path, workspace, findings)
            _check_headings(path, body, template, workspace, findings, optional)
        else:
            _finding(findings, "missing-record", _record(workspace, path), "required record is missing")
    # Both flat and milestone-grouped roadmaps are canonical template variants.
    if roadmap.exists:
        for title in ("Phases", "Progress"):
            if not find_section(roadmap.content, title, 2):
                _finding(findings, "template-section", ".planning/ROADMAP.md", "missing section: " + title, "structure")

    rows = table_records(section_body(read_text(workspace.requirements, ""), "Traceability", 2))
    requirement_ids = [row.get("Requirement", "") for row in rows]
    authored = REQUIREMENT.findall(read_text(workspace.requirements, ""))
    for identifier in sorted(set(requirement_ids + authored)):
        if not identifier or requirement_ids.count(identifier) > 1 or authored.count(identifier) > 1:
            _finding(findings, "requirement-id", ".planning/REQUIREMENTS.md", "missing or duplicate requirement id: " + identifier)
    for identifier in authored:
        if identifier not in requirement_ids:
            _finding(findings, "requirement-id", ".planning/REQUIREMENTS.md", "no traceability row: " + identifier)
    for identifier in requirement_ids:
        if identifier not in authored:
            _finding(findings, "requirement-id", ".planning/REQUIREMENTS.md", "traceability id has no authored requirement: " + identifier)
    phase_list = roadmap.phases()
    numbers = [as_number(item.number) for item in phase_list]
    parsed_state = None
    try:
        parsed_state = state.State(workspace) if workspace.state.is_file() else None
    except VerbError:
        pass  # Already reported by _metadata above; no repair is proposed.
    if parsed_state and parsed_state.phase_number and roadmap.find(parsed_state.phase_number) is None:
        _finding(findings, "state-position", ".planning/STATE.md", "current phase has no roadmap entry")
    for row in rows:
        status = row.get("Status", "")
        if status not in requirements.STATUSES:
            _finding(findings, "requirement-status", ".planning/REQUIREMENTS.md", "unknown requirement status: " + status)
        raw = row.get("Phase", "").strip()
        match = re.fullmatch(r"(?:Phase\s+)?(\d+(?:\.\d+)?)", raw, re.I)
        target = roadmap.find(match.group(1)) if match else None
        if match and target is None:
            _finding(findings, "requirement-phase", ".planning/REQUIREMENTS.md", "unknown phase: " + raw)
        if target and status == "Complete" and target.status != "Complete":
            _finding(findings, "completion-evidence", ".planning/REQUIREMENTS.md", "complete requirement maps to unfinished phase: " + row.get("Requirement", "?"))

    plan_paths = {}
    for directory in sorted(workspace.phases_dir.glob("*")):
        if not directory.is_dir():
            continue
        match = phases.DIRECTORY.fullmatch(directory.name)
        if not match or as_number(match.group(1)) not in numbers:
            _finding(findings, "phase-id", _record(workspace, directory), "phase directory has no unique roadmap identity")
    for phase in phase_list:
        if numbers.count(as_number(phase.number)) > 1:
            _finding(findings, "phase-id", ".planning/ROADMAP.md", "duplicate phase: " + phase.number)
        for dependency in re.findall(r"\bPhase\s+(\d+(?:\.\d+)?)", phase.depends_on, re.I):
            if roadmap.find(dependency) is None or as_number(dependency) >= as_number(phase.number):
                _finding(findings, "phase-dependency", ".planning/ROADMAP.md", "invalid dependency for phase " + phase.number + ": " + dependency)
        for identifier in phase.requirements:
            if identifier not in requirement_ids:
                _finding(findings, "requirement-id", ".planning/ROADMAP.md", "unknown requirement: " + identifier)
        directories = [entry for entry in workspace.phases_dir.glob("*") if entry.is_dir()
                       and phases.DIRECTORY.fullmatch(entry.name)
                       and as_number(phases.DIRECTORY.fullmatch(entry.name).group(1)) == as_number(phase.number)]
        if len(directories) > 1:
            _finding(findings, "phase-id", ".planning/phases", "duplicate directories for phase " + phase.number)
        directory = directories[0] if directories else None
        checklist = [item["id"] for item in phase.plans]
        for item in phase.plans:
            if checklist.count(item["id"]) > 1 or not item["id"].startswith(pad(phase.number) + "-"):
                _finding(findings, "plan-id", ".planning/ROADMAP.md", "invalid or duplicate plan id: " + item["id"])
            plan_path = directory / (item["id"] + "-PLAN.md") if directory else None
            if plan_path is None or not plan_path.is_file():
                if item["description"].strip().upper() != "TBD":
                    _finding(findings, "plan-id", ".planning/ROADMAP.md", "registered plan file missing: " + item["id"])
            summary_path = directory / (item["id"] + "-SUMMARY.md") if directory else None
            if item["done"]:
                if summary_path is None or not summary_path.is_file():
                    _finding(findings, "completion-evidence", ".planning/ROADMAP.md", "checked plan lacks summary: " + item["id"])
                else:
                    data, summary_body = _metadata(summary_path, workspace, findings)
                    hashes = _summary_commits(data, summary_body)
                    if data.get("status") != "complete" or not hashes:
                        _finding(findings, "completion-evidence", _record(workspace, summary_path), "checked plan lacks complete status and commits")
                    else:
                        for revision in hashes:
                            if not gitops.rev_parse(workspace, revision + "^{commit}"):
                                _finding(findings, "completion-evidence", _record(workspace, summary_path), "summary commit cannot be resolved: " + revision)
        if not directory:
            continue
        context = directory / (pad(phase.number) + "-CONTEXT.md")
        if list(directory.glob("*-PLAN.md")) and not context.is_file():
            _finding(findings, "missing-context", _record(workspace, directory), "executable plans lack phase CONTEXT")
        elif context.is_file():
            _, body = _metadata(context, workspace, findings)
            _check_headings(context, body, "context.md", workspace, findings,
                            ("Claude's Discretion", "Reusable Assets", "Established Patterns", "Integration Points"))
            if "<canonical_refs>" not in body:
                _finding(findings, "canonical-refs", _record(workspace, context), "mandatory canonical_refs is missing")
        for path in sorted(directory.glob("*-PLAN.md")):
            match = phases.PLAN_FILE.fullmatch(path.name)
            if not match:
                _finding(findings, "plan-id", _record(workspace, path), "noncanonical plan filename")
                continue
            identifier = path.name[:-len("-PLAN.md")]
            if identifier in plan_paths or identifier not in checklist:
                _finding(findings, "plan-id", _record(workspace, path), "duplicate or unregistered plan: " + identifier)
            data, body = _metadata(path, workspace, findings)
            plan_paths[identifier] = (path, data)
            expected_phase = directory.name
            if str(data.get("phase")) != expected_phase or str(data.get("plan")).zfill(2) != match.group(2):
                _finding(findings, "plan-id", _record(workspace, path), "frontmatter identity differs from filename/directory")
            for key in ("wave", "depends_on", "files_modified", "requirements", "acceptance", "must_haves"):
                if key not in data:
                    _finding(findings, "plan-contract", _record(workspace, path), "missing metadata: " + key, "structure")
            for key in ("depends_on", "files_modified", "requirements", "acceptance"):
                if key in data and not isinstance(data[key], list):
                    _finding(findings, "plan-contract", _record(workspace, path), key + " must be a list")
            if not isinstance(data.get("wave"), int) or isinstance(data.get("wave"), bool) or data.get("wave", 0) < 1:
                _finding(findings, "plan-contract", _record(workspace, path), "wave must be a positive integer")
            for key in ("requirements", "acceptance"):
                if not data.get(key):
                    _finding(findings, "plan-contract", _record(workspace, path), "empty " + key)
            ids = data.get("requirements", [])
            for req in ids if isinstance(ids, list) else []:
                if req not in requirement_ids:
                    _finding(findings, "requirement-id", _record(workspace, path), "unknown requirement: " + str(req))
            for tag in ("objective", "context", "tasks", "verification", "success_criteria", "output"):
                if not re.search(r"<" + tag + r">.*?</" + tag + r">", body, re.S):
                    _finding(findings, "plan-contract", _record(workspace, path), "missing block: " + tag, "structure")
            tasks = re.findall(r"<task\b([^>]*)>(.*?)</task>", body, re.S)
            if not tasks:
                _finding(findings, "plan-contract", _record(workspace, path), "no tasks")
            for index, (attributes, task) in enumerate(tasks, 1):
                if re.search(r"\btype=[\"']checkpoint:", attributes):
                    if "<resume-signal>" not in task:
                        _finding(findings, "plan-contract", _record(workspace, path), "checkpoint " + str(index) + " lacks resume-signal")
                    continue  # Canonical human checkpoints have their own fields.
                for tag in ("read_first", "action", "acceptance_criteria", "verify"):
                    if not re.search(r"<" + tag + r">\s*\S.*?</" + tag + r">", task, re.S):
                        _finding(findings, "plan-contract", _record(workspace, path), "task " + str(index) + " lacks " + tag, "structure")
                for automated in re.finditer(r"<automated>.*?</automated>", task, re.S):
                    if not re.match(r"\s*<fails_when>\s*\S.*?</fails_when>", task[automated.end():], re.S):
                        _finding(findings, "plan-contract", _record(workspace, path), "task " + str(index) + " check lacks fails_when")
        for path in sorted(directory.glob("*-SUMMARY.md")):
            data, body = _metadata(path, workspace, findings)
            _check_headings(path, body, "summary.md", workspace, findings, ("User Setup Required",))
            if data.get("status") not in ("complete", "blocked"):
                _finding(findings, "summary-status", _record(workspace, path), "status must be complete or blocked")
        if phase.status == "Complete":
            try:
                report = verification.status(workspace, phase.number)
            except VerbError as exc:
                _finding(findings, "frontmatter", _record(workspace, directory), str(exc))
                report = {}
            if report.get("status") != "passed" or not report.get("revision") or not report.get("verified_at"):
                _finding(findings, "completion-evidence", _record(workspace, directory), "complete phase lacks dated passed verification with revision")
    for identifier, (path, data) in plan_paths.items():
        dependencies = data.get("depends_on", [])
        for dependency in dependencies if isinstance(dependencies, list) else []:
            target = plan_paths.get(str(dependency))
            if not target or str(dependency) == identifier:
                _finding(findings, "plan-dependency", _record(workspace, path), "unknown or self dependency: " + str(dependency))
            elif isinstance(data.get("wave"), int) and isinstance(target[1].get("wave"), int) and target[1]["wave"] >= data["wave"]:
                _finding(findings, "plan-dependency", _record(workspace, path), "dependency is not in an earlier wave: " + str(dependency))

    graph = {identifier: [str(item) for item in data.get("depends_on", [])]
             if isinstance(data.get("depends_on"), list) else []
             for identifier, (_, data) in plan_paths.items()}
    visited, visiting, cycles = set(), set(), set()

    def visit(identifier):
        if identifier in visiting:
            cycles.add(identifier)
            return
        if identifier in visited or identifier not in graph:
            return
        visiting.add(identifier)
        for dependency in graph[identifier]:
            visit(dependency)
        visiting.remove(identifier)
        visited.add(identifier)

    for identifier in sorted(graph):
        visit(identifier)
    for identifier in sorted(cycles):
        _finding(findings, "plan-dependency", _record(workspace, plan_paths[identifier][0]),
                 "dependency cycle includes: " + identifier)

    active_files = [path for path in files if not any(part in {"archive", "archives", "milestones"}
                                                    for part in path.relative_to(workspace.planning).parts)]
    adr_ids = {}
    for path in active_files:
        data, body = _metadata(path, workspace, findings)
        if path.name.startswith("ADR-") and path.parent.name == "decisions":
            identifier = re.match(r"^ADR-(\d+)-.+\.md$", path.name)
            declared = re.search(r"^# ADR-(\d+)\b", body, re.M)
            if not identifier or not declared or int(identifier.group(1)) != int(declared.group(1)):
                _finding(findings, "adr-id", _record(workspace, path), "ADR heading identity differs from filename")
            elif int(identifier.group(1)) in adr_ids:
                _finding(findings, "adr-id", _record(workspace, path), "duplicate ADR id: " + identifier.group(1))
            else:
                adr_ids[int(identifier.group(1))] = path
            _check_headings(path, body, "ADR.md", workspace, findings)
            if data.get("status") not in ADR_STATUSES:
                _finding(findings, "adr-status", _record(workspace, path), "unknown ADR status")
            if data.get("status") == "superseded" and not data.get("superseded_by"):
                _finding(findings, "adr-replacement", _record(workspace, path), "superseded ADR lacks replacement reference")
        if path.name == "QUICK.md":
            if not quick.DIRECTORY.fullmatch(path.parent.name):
                _finding(findings, "quick-id", _record(workspace, path), "noncanonical quick directory identity")
            if data.get("status") not in quick.STATUSES:
                _finding(findings, "quick-status", _record(workspace, path), "unknown quick status")
            for title in ("Task", "Verification", "Changes"):
                if not find_section(body, title, 2):
                    _finding(findings, "template-section", _record(workspace, path), "missing quick section: " + title, "structure")
            if data.get("status") == "complete" and not data.get("completed"):
                _finding(findings, "completion-evidence", _record(workspace, path), "complete quick item lacks completion date")
        for target in LINK.findall(_visible(body)):
            raw = unquote(target.strip().strip("<>").split("#", 1)[0])
            if not raw or re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", raw):
                continue
            destination = (workspace.root / raw if raw.startswith(".planning/") else path.parent / raw).resolve()
            if not destination.is_relative_to(workspace.root) or not destination.exists():
                _finding(findings, "local-reference", _record(workspace, path), "missing or outside repository reference: " + raw)
    candidates = []
    candidate = _repair_candidate(workspace, findings, roadmap)
    if candidate:
        candidates.append(candidate)
        for operation in candidate["operations"]:
            if operation["operation"] == "derive-state-progress":
                _finding(findings, "state-progress", ".planning/STATE.md",
                         "derived progress metadata differs from roadmap checkboxes",
                         "structure", "planning.repair --only state-structure")
    result = {"status": "findings" if findings else "clean", "fingerprint": fingerprint,
              "inventory": [{"record": name, "sha256": digest} for name, digest in snapshot
                            if not name.startswith("templates/")],
              "checks": base["checks"], "findings": findings, "finding_count": len(findings),
              "repairs": [{key: value for key, value in item.items() if key != "content"}
                          for item in candidates]}
    return result, candidates


def review(workspace):
    """Read-only report; findings never claim to prove implementation behavior."""
    return _audit(workspace)[0]


def repair(workspace, apply=False, expected=None, only=()):
    """Preview by default; apply requires the exact reviewed evidence snapshot."""
    _preflight(workspace)
    if apply:
        require(expected, "--apply requires --expect <review fingerprint>", "review-required")
        _guard_path(workspace.planning / ".lock", workspace.root)
        with state.planning_lock(workspace):
            return _repair(workspace, True, expected, only)
    return _repair(workspace, False, expected, only)


def _repair(workspace, apply, expected, only):
    report, candidates = _audit(workspace)
    if expected:
        require(expected == report["fingerprint"], "planning evidence changed; review again", "stale-review")
    requested = set(only)
    require(requested.issubset({item["id"] for item in candidates}),
            "unknown repair selection", "unknown-repair")
    selected = [item for item in candidates if not requested or item["id"] in requested]
    changed = []
    for item in selected:
        path = workspace.root / item["record"]
        _guard_path(path, workspace.root)
        require(path.is_relative_to(workspace.planning),
                "repair target escapes planning", "path-escape")
        if apply:
            write_text(path, item["content"])
            changed.append(item["record"])
    return {"dry_run": not apply, "fingerprint": report["fingerprint"],
            "repairs": [{key: value for key, value in item.items() if key != "content"}
                        for item in selected], "changed": changed,
            "findings": report["findings"], "status": report["status"]}
