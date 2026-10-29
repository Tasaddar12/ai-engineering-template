"""Read-only native planning evidence for the shared health rule evaluator.

Each evidence field records completeness. Files outside the repository (including
linked planning directories) are never read. No defaults are written to disk.
"""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import time

from . import config, phase_id
from .core import Failure
from .text import split_frontmatter, yaml_load
from .health_diagnostic_rules import extract_phase_token, phase_directory_context


def field(value, scope="complete", **extra):
    return {"value": value, "scope": scope, **extra}


class Reader:
    def __init__(self, cwd):
        self.root = Path(cwd).resolve()
        self.gaps = []

    def safe(self, path):
        if not path.resolve().is_relative_to(self.root):
            raise OSError("Linked path leaves repository")
        return path

    def text(self, path):
        try:
            return self.safe(path).read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            self.gaps.append({"path": str(path), "reason": f"Planning record is unreadable ({type(exc).__name__})"})
            return None

    def entries(self, path):
        try:
            if not self.safe(path).exists():
                return []
            return sorted(self.safe(p) for p in path.iterdir())
        except OSError as exc:
            self.gaps.append({"path": str(path), "reason": str(exc)})
            return []


def _label(text, name):
    match = re.search(r"(?mi)^(?:\*\*)?" + name + r"(?::\*\*|\*\*:|:)\s*(.*)$", text or "")
    return match.group(1).strip() if match else None


def _phase_token(value, reader, path):
    try:
        return phase_id.normalize(value.lower())
    except Failure:
        reader.gaps.append({"path": str(path), "reason": "Invalid native phase identifier"})
        return value.lower()


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=10)


def _git_evidence(cwd):
    try:
        result = _git(cwd, "worktree", "list", "--porcelain", "-z")
        if result.returncode:
            return field([], "unreadable", reason="git_list_failed"), field({}, "unreadable")
        findings = []
        for part in result.stdout.split("\0"):
            if not part.startswith("worktree "):
                continue
            path = Path(part[9:])
            try:
                age = (time.time() - path.stat().st_mtime) / 60
                if age > 60 * 24 * 14:
                    findings.append({"kind": "stale", "path": str(path), "ageMinutes": int(age)})
            except FileNotFoundError:
                findings.append({"kind": "orphan", "path": str(path)})
            except OSError:
                findings.append({"kind": "unverified", "path": str(path)})
        tracked = _git(cwd, "ls-files", "--", ".planning/")
        ignored = _git(cwd, "check-ignore", "--no-index", ".planning/")
        scope = "complete" if tracked.returncode == 0 and ignored.returncode in (0, 1) else "unreadable"
        return field(findings), field({"tracked": bool(tracked.stdout), "ignored": ignored.returncode == 0}, scope)
    except subprocess.TimeoutExpired:
        return field([], "unreadable", reason="git_timed_out"), field({}, "unreadable")
    except OSError:
        return field([], "unreadable", reason="git_list_failed"), field({}, "unreadable")


def build_snapshot(cwd):
    """Return upstream-shaped evidence plus native validation and evidence gaps."""
    reader = Reader(cwd)
    base = reader.root / ".planning"
    project, roadmap, state, requirements = [reader.text(base / name) for name in
                                            ("PROJECT.md", "ROADMAP.md", "STATE.md", "REQUIREMENTS.md")]
    raw_config = reader.text(base / "config.yaml")
    config_error = None
    parsed = None
    if raw_config is not None:
        try:
            parsed = yaml_load(raw_config)
            config.validate(parsed)
        except (Failure, ValueError, TypeError) as exc:
            code = getattr(exc, "code", "invalid-config")
            config_error = {"code": code, "message": f"config.yaml failed native validation ({code}); inspect the local file"}
            # Keep a readable mapping available to field-specific advisory rules.
            if not isinstance(parsed, dict):
                parsed = None
    declared, checkboxes = [], {}
    milestone = None
    for line in (roadmap or "").splitlines():
        version = re.match(r"^##\s+(v\d+(?:\.\d+)+)\b", line)
        if version:
            milestone = version.group(1)
        phase = re.match(r"^#{2,4}\s+Phase\s+(" + phase_id.PATTERN + r")\s*:", line, re.I)
        if phase:
            declared.append({"phaseId": _phase_token(phase.group(1), reader, base / "ROADMAP.md"), "milestone": milestone})
        check = re.match(r"^- \[([ xX])\]\s+(?:\*\*)?Phase\s+(" + phase_id.PATTERN + r")\s*:", line, re.I)
        if check:
            checkboxes[_phase_token(check.group(2), reader, base / "ROADMAP.md")] = check.group(1).lower() == "x"
            if check.group(2).isdigit():
                checkboxes[str(int(check.group(2)))] = check.group(1).lower() == "x"
    active_version = re.search(r"v\d+(?:\.\d+)+", _label(state, "Milestone") or "")
    active_milestone = active_version.group(0) if active_version else milestone
    phases, research, numbering, orphans, missing_wave = [], [], [], [], []
    dirs = [p for p in reader.entries(base / "phases") if p.is_dir()]
    for directory in dirs:
        files = [p for p in reader.entries(directory) if p.is_file()]
        plans = [p for p in files if p.name.endswith("-PLAN.md")]
        summaries = [p for p in files if p.name.endswith("-SUMMARY.md")]
        plan_contents = {p: reader.text(p) for p in plans}
        readable_summaries = [p for p in summaries if reader.text(p) is not None]
        matching_names = [p for p in summaries if p.with_name(p.name.replace("-SUMMARY.md", "-PLAN.md")) in plans]
        matched = [p for p in readable_summaries
                   if plan_contents.get(p.with_name(p.name.replace("-SUMMARY.md", "-PLAN.md"))) is not None]
        phase = {"dir": directory.name, "planCount": len(plans), "summaryCount": len(matched),
                 "complete": bool(plans) and len(matched) == len(plans), "verificationStatus": None}
        for report in (p for p in files if p.name.endswith("-VERIFICATION.md")):
            content = reader.text(report)
            if content is None:
                continue
            try:
                metadata, _ = split_frontmatter(content)
                status = metadata.get("status")
            except Failure as exc:
                status = None
                reader.gaps.append({"path": str(report), "reason": str(exc)})
            phase["verificationStatus"] = status
            if status not in ("passed", "gaps_found", "human_needed"):
                phase["verificationStatusError"] = {"rawStatus": status, "file": str(report),
                                                     "message": f"Verification status {status!r} is outside passed | gaps_found | human_needed"}
        phases.append(phase)
        nums = []
        for plan in plans:
            content = plan_contents[plan]
            if content is None:
                continue
            try:
                metadata, _ = split_frontmatter(content)
            except Failure as exc:
                reader.gaps.append({"path": str(plan), "reason": str(exc)})
                metadata = {}
            if "wave" not in metadata:
                missing_wave.append({"phaseDir": directory.name, "plan": plan.name})
            num = re.search(r"-(\d+)-PLAN\.md$", plan.name)
            if num:
                nums.append(int(num.group(1)))
        numbering.append({"phaseDir": directory.name, "planNums": sorted(nums)})
        orphans.extend({"phaseDir": directory.name, "orphanSummary": p.name} for p in summaries if p not in matching_names)
        research_text = "\n".join(reader.text(p) or "" for p in files if p.name.endswith("-RESEARCH.md"))
        research.append({"dir": directory.name, "hasValidationArchitecture": "Validation Architecture" in research_text,
                         "hasValidationMd": any(p.name.endswith("-VALIDATION.md") for p in files)})
    archives = reader.entries(base / "milestones")
    archived_versions = [p.name[:-11] for p in archives if re.fullmatch(r"v\d+(?:\.\d+)+-ROADMAP\.md", p.name)]
    milestones = reader.text(base / "MILESTONES.md") if (base / "MILESTONES.md").exists() else ""
    archived_tokens = []
    for archive in archives:
        if archive.is_dir():
            archived_tokens.extend(extract_phase_token(p.name, "native") for p in reader.entries(archive) if p.is_dir())
    worktrees, tracked = _git_evidence(reader.root)
    if worktrees["scope"] != "complete" or tracked["scope"] != "complete":
        reader.gaps.append({"path": str(reader.root), "kind": "git",
                            "reason": worktrees.get("reason") or "Git tracking/ignore evidence unavailable"})
    label = _label(state, r"(?:Current phase|Phase)")
    state_token = re.match(r"(" + phase_id.PATTERN + r")(?=\s|$|\))", label or "", re.I)
    state_tokens = [_phase_token(state_token.group(1), reader, base / "STATE.md")] if state_token else []
    config_field = field(parsed, exists=raw_config is not None, path=str(base / "config.yaml"))
    snapshot = {
        "cwd": str(reader.root), "workstream": None, "phaseIdConvention": (parsed or {}).get("phase_id_convention") or "native",
        "projectSections": field(re.findall(r"(?m)^##\s+(.+?)\s*$", project) if project is not None else None,
                                 exists=project is not None),
        "milestone": field({"version": active_milestone}, "complete" if roadmap is not None else "unreadable"),
        "currentPhaseLabel": field(label, "complete" if state is not None else "unreadable"),
        "stateStatus": field(_label(state, "Status")),
        "statePhaseTokens": field(state_tokens),
        "config": config_field, "phaseDirs": field([p.name for p in dirs]),
        "allPhaseDirNames": field([p.name for p in dirs]), "phases": field(phases),
        "archivedPhaseTokens": field(archived_tokens),
        "roadmapDeclaredPhases": field(declared, "complete" if roadmap is not None else "unreadable"),
        "roadmapSentinelPhaseTokens": field([]), "roadmapPhaseCheckboxes": field(checkboxes),
        "roadmapBracketIncoherences": field([], "unscoped"),
        "currentMilestoneRoadmapPhaseIds": field([p["phaseId"] for p in declared if p["milestone"] == active_milestone]),
        "researchValidationStatus": field(research), "agentInstall": field({}, "unreadable"),
        "milestoneArchiveStatus": field({"archivedVersions": archived_versions,
                                        "documentedVersions": re.findall(r"(?m)^##\s+(v\d+(?:\.\d+)+)\b", milestones or "")}),
        "planningRootFiles": field([p.name for p in reader.entries(base) if p.is_file()]),
        "worktreeHealth": worktrees, "planningTracked": tracked,
        "perPhasePlanNumbering": field(numbering), "perPhaseOrphanSummaries": field(orphans),
        "perPhaseWaveMissingPlans": field(missing_wave),
        "directoryContext": phase_directory_context(parsed or {}, roadmap or "", [p["phaseId"] for p in declared]),
    }
    snapshot["directoryContext"]["nativePhaseIds"] = True
    return {"snapshot": snapshot, "gaps": reader.gaps, "configError": config_error,
            "requirementsReadable": requirements is not None,
            "unonboarded": bool(project and "Unfilled adoption skeleton" in project),
            "planningExists": base.is_dir()}
