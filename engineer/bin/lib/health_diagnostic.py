"""Health diagnostic: frozen rule-table enums, rule evaluator and ``--repair`` dispatcher.

Port of ``src/health-diagnostic.cts`` and ``src/health-diagnostic-types.cts`` from gsd-core
at pinned commit d37ff11b47258b560f0cf8f1132b42ecd90e0c79 (MIT, Copyright (c) 2026 Open GSD).
The rule groups (``src/health-diagnostic-rules/*.cts``) live in ``health_diagnostic_rules.py``.

Public surface (snake_case of upstream): ``SEVERITY``, ``REMEDY_ACTION``, ``REMEDY_RISK``,
``advise_remedy``, ``RULES``, ``CONSISTENCY_RULES``, ``evaluate_rule_table``,
``evaluate_rules``, ``evaluate_consistency_rules``, ``apply_repairs``.
A Diagnostic is ``{"code", "severity", "message", "remedy": {"action", "risk", "args"}}``;
``apply_repairs`` returns ``{"applied": [...], "refused": [...], "details": [...]}``.

Deviations:
- ``planning-snapshot.cts`` is not ported: rules receive a plain dict with the upstream
  ``PlanningSnapshot`` field names (see ``health_diagnostic_rules``).
- Repair paths are ``<cwd>/.planning/{config.json,STATE.md,MILESTONES.md,milestones/}`` as upstream;
  ``GSD_PROJECT`` / ``GSD_WORKSTREAM`` scoping (``planning-workspace.cts``) is not ported. The repo's
  own config lives in ``config.yaml``; ``createConfig`` / ``resetConfig`` still write upstream's
  ``config.json`` payload (``CONFIG_DEFAULTS`` values are inlined from ``config-loader.cts``).
- ``regenerateState`` (always refused by the dispatcher for DESTRUCTIVE remedies) writes the
  regenerated content after a timestamped backup but does not run ``rebuildStateTransaction`` /
  ``writeStateMd`` frontmatter rebuilding, and leaves the milestone label empty
  (``getMilestoneInfo`` is not ported).
- ``assertVerificationReportsReadable`` is approximated by scanning
  ``.planning/phases/*/*VERIFICATION.md`` frontmatter ``status`` against the closed set.
- ``/gsd-health`` slash text is hardcoded (``resolveRuntime`` / ``formatGsdSlash`` are not ported).
- Handler exceptions are reported with Python's ``str(exc)`` rather than a JavaScript message.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
from pathlib import Path

from .health_diagnostic_rules import (
    REMEDY_ACTION,
    REMEDY_RISK,
    RULE_GROUPS,
    SCOPE,
    SEVERITY,
    advise_remedy,
    legacy_status_repair_target,
)

__all__ = [
    "SEVERITY", "REMEDY_ACTION", "REMEDY_RISK", "SCOPE", "advise_remedy", "RULES", "CONSISTENCY_RULES",
    "evaluate_rule_table", "evaluate_rules", "evaluate_consistency_rules", "apply_repairs", "repair_paths",
    "default_config_payload", "compute_missing_milestone_versions", "run_repair_action",
]

# --- Rule table -----------------------------------------------------------------------

_RULE_ORDER = (
    "root-existence", "state-consistency", "config-validation", "phase-structure", "agent-install",
    "roadmap-disk-consistency", "worktree-health", "milestone-archive-hygiene", "install-surface-shadowing",
)


def _group(name):
    return RULE_GROUPS.get(name, [])


RULES = [rule for name in _RULE_ORDER for rule in _group(name)]

# ``validate.consistency``'s rule set: W006/W007 and W030 are the SAME rule objects ``RULES`` carries.
CONSISTENCY_RULES = [
    *[r for r in _group("roadmap-disk-consistency") if r["code"] in ("W006", "W007")],
    *[r for r in _group("phase-structure") if r["code"] == "W030"],
    *_group("consistency"),
]

# --- Evaluator ------------------------------------------------------------------------


def evaluate_rule_table(rules, snapshot):
    """Evaluate ``rules`` against ``snapshot``; raises ``ValueError`` on a duplicate rule code."""
    seen = set()
    for rule in rules:
        if rule["code"] in seen:
            raise ValueError(f'health-diagnostic: duplicate rule code "{rule["code"]}" in rule table')
        seen.add(rule["code"])
    return [diagnostic for rule in rules for diagnostic in rule["check"](snapshot)]


def evaluate_rules(snapshot):
    return evaluate_rule_table(RULES, snapshot)


def evaluate_consistency_rules(snapshot):
    return evaluate_rule_table(CONSISTENCY_RULES, snapshot)


# --- Repair handlers ------------------------------------------------------------------


def repair_paths(cwd):
    root_base = Path(cwd) / ".planning"
    return {
        "rootBase": root_base,
        "configPath": root_base / "config.json",
        "statePath": root_base / "STATE.md",
        "milestonesPath": root_base / "MILESTONES.md",
        "milestonesArchiveDir": root_base / "milestones",
    }


def default_config_payload():
    """``verify.cts``'s default ``config.json`` payload (``CONFIG_DEFAULTS`` values inlined)."""
    return {
        "model_profile": "balanced",
        "commit_docs": True,
        "search_gitignored": False,
        "branching_strategy": "none",
        "phase_branch_template": "gsd/phase-{phase}-{slug}",
        "milestone_branch_template": "gsd/{milestone}-{slug}",
        "quick_branch_template": None,
        "workflow": {"research": True, "plan_check": True, "verifier": True, "nyquist_validation": True},
        "parallelization": True,
        "brave_search": False,
    }


def _read_text(path):
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def _write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def _json_text(value):
    return json.dumps(value, indent=2, ensure_ascii=False)


def _local_today():
    return _dt.date.today().isoformat()


def compute_missing_milestone_versions(milestones_archive_dir, milestones_path):
    """Archived ``vX.Y-ROADMAP.md`` versions with no ``## vX.Y`` heading in MILESTONES.md."""
    archived = []
    try:
        if os.path.exists(milestones_archive_dir):
            for name in os.listdir(milestones_archive_dir):
                match = re.match(r"^(v\d+\.\d+(?:\.\d+)?)-ROADMAP\.md\Z", name)
                if match:
                    archived.append(match.group(1))
    except OSError:
        pass
    documented = []
    try:
        if os.path.exists(milestones_path):
            documented = re.findall(r"^##\s+(v\d+\.\d+(?:\.\d+)?)", _read_text(milestones_path), re.M)
    except OSError:
        pass
    known = set(documented)
    return [version for version in archived if version not in known]


def _describe_raw_status(raw):
    return json.dumps(raw if isinstance(raw, str) else raw, ensure_ascii=False)


def _frontmatter_fence(content):
    """``(open_end, body_end, eol)`` of a closed frontmatter block, or None."""
    opened = re.match(r"\A﻿?---[ \t]*(\r?\n)", content)
    if not opened:
        return None
    closed = re.compile(r"^---[ \t]*(?:\r?\n|\Z)", re.M).search(content, opened.end())
    if not closed:
        return None
    return opened.end(), closed.start(), opened.group(1)


def _report_contained(phase_dir, file_path):
    try:
        real_dir = os.path.realpath(phase_dir)
        real_file = os.path.realpath(file_path)
        planning_root = None
        probe = real_dir
        while True:
            if os.path.basename(probe) == ".planning":
                planning_root = probe
                break
            parent = os.path.dirname(probe)
            if parent == probe:
                break
            probe = parent
        if planning_root is None:
            return False
        return (os.path.commonpath([real_dir, planning_root]) == planning_root
                and os.path.commonpath([real_file, real_dir]) == real_dir and os.path.isfile(real_file))
    except (OSError, ValueError):
        return False


def _repair_legacy_verification_status(file_path):
    """Rewrite a known legacy report ``status`` to its closed-set equivalent, keeping ``legacy_status``."""
    if not _report_contained(os.path.dirname(file_path), file_path):
        return {"ok": False, "reason": "the report is not contained in its phase directory"}
    try:
        content = _read_text(file_path)
    except OSError as exc:
        return {"ok": False, "reason": str(exc)}
    fence = _frontmatter_fence(content)
    if fence is None:
        return {"ok": False, "reason": "the report has no closed frontmatter"}
    open_end, body_end, _eol = fence
    lines = content[open_end:body_end].splitlines(keepends=True)
    status_at = -1
    for index, line in enumerate(lines):
        if re.match(r"status:", line):
            status_at = index
    if status_at == -1:
        return {"ok": False, "reason": "the report frontmatter has no status"}
    ending = re.search(r"(\r?\n)\Z", lines[status_at])
    ending = ending.group(1) if ending else ""
    raw = lines[status_at].rstrip("\r\n")
    raw = re.sub(r"^status:\s*", "", raw)
    raw = re.sub(r"\s+#.*$", "", raw)
    raw = re.sub(r"\s+$", "", raw)
    quoted = re.match(r"^([\"'])(.*)\1\Z", raw)
    if quoted:
        raw = quoted.group(2)
    target = legacy_status_repair_target(raw)
    if target is None:
        return {"ok": False, "reason": f"{_describe_raw_status(raw)} has no known repair"}
    kept = any(re.match(r"legacy_status:", line) for line in lines)
    lines[status_at] = f"status: {target}{ending}"
    if not kept:
        lines.insert(status_at + 1, f"legacy_status: {raw}{ending}")
    _write_text(file_path, content[:open_end] + "".join(lines) + content[body_end:])
    return {"ok": True, "from": raw, "to": target, "legacyStatusKept": kept}


class _VerificationStatusError(Exception):
    pass


def _assert_verification_reports_readable(cwd):
    """Raise when any phase report's frontmatter ``status`` is outside ``passed | gaps_found | human_needed``."""
    accepted = ("passed", "gaps_found", "human_needed")
    phases = Path(cwd) / ".planning" / "phases"
    if not phases.is_dir():
        return
    for phase_dir in sorted(p for p in phases.iterdir() if p.is_dir()):
        for report in sorted(phase_dir.glob("*VERIFICATION.md")):
            try:
                content = _read_text(report)
            except OSError:
                continue
            fence = _frontmatter_fence(content)
            if fence is None:
                continue
            value = None
            for line in content[fence[0]:fence[1]].splitlines():
                if line.startswith("status:"):
                    value = re.sub(r"^status:\s*", "", line)
                    value = re.sub(r"\s+#.*$", "", value).strip().strip("\"'")
            if value and value not in accepted:
                raise _VerificationStatusError(
                    f"Verification report {report} has status {_describe_raw_status(value)}, which is outside the closed set"
                    f" — accepted values: {' | '.join(accepted)}. "
                    f"Recovery: set the report's frontmatter `status:` to one of {' | '.join(accepted)}, "
                    "or delete the report and re-run the phase's verification.")


def run_repair_action(cwd, action, paths, args=None):
    """Execute exactly one repair action. Exceptions are the caller's responsibility."""
    args = args or {}
    config_path, state_path = paths["configPath"], paths["statePath"]
    milestones_path, archive_dir = paths["milestonesPath"], paths["milestonesArchiveDir"]

    if action == REMEDY_ACTION["REPAIR_VERIFICATION_STATUS"]:
        file = args.get("file") if isinstance(args.get("file"), str) else ""
        if file == "":
            return {"success": False, "error": "no report path on the finding"}
        repaired = _repair_legacy_verification_status(file)
        if not repaired["ok"]:
            return {"success": False, "error": repaired["reason"]}
        relative = os.path.relpath(file, cwd).replace(os.sep, "/")
        detail = (f"status {repaired['from']} -> {repaired['to']}; the report's existing legacy_status was left as it was"
                  if repaired["legacyStatusKept"]
                  else f"status {repaired['from']} -> {repaired['to']}; original kept as legacy_status")
        return {"success": True, "path": relative, "detail": detail}

    if action in (REMEDY_ACTION["CREATE_CONFIG"], REMEDY_ACTION["RESET_CONFIG"]):
        _write_text(config_path, _json_text(default_config_payload()))
        return {"success": True, "path": "config.json"}

    if action == REMEDY_ACTION["REGENERATE_STATE"]:
        extra = []
        project_ref = os.path.relpath(paths["rootBase"] / "PROJECT.md", cwd).replace(os.sep, "/")
        content = "# Session State\n\n## Project Reference\n\n"
        content += f"See: {project_ref}\n\n"
        content += "## Position\n\n"
        content += "**Milestone:**  \n"
        content += "**Current phase:** (determining...)\n"
        content += "**Status:** Resuming\n\n"
        content += "## Session Log\n\n"
        content += f"- {_local_today()}: STATE.md regenerated by /gsd-health --repair\n"
        if os.path.exists(state_path):
            timestamp = re.sub(r"[:.]", "-", _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="milliseconds"))[:19]
            backup = f"{state_path}.bak-{timestamp}"
            with open(state_path, "rb") as source, open(backup, "wb") as target:
                target.write(source.read())
            extra.append({"action": "backupState", "success": True, "path": backup})
        _write_text(state_path, content)
        return {"success": True, "path": "STATE.md", "extraDetails": extra}

    if action in (REMEDY_ACTION["ADD_NYQUIST_KEY"], REMEDY_ACTION["ADD_AI_INTEGRATION_PHASE_KEY"]):
        key = "nyquist_validation" if action == REMEDY_ACTION["ADD_NYQUIST_KEY"] else "ai_integration_phase"
        parsed = json.loads(_read_text(config_path))
        if not parsed.get("workflow"):
            parsed["workflow"] = {}
        workflow = parsed["workflow"]
        if key not in workflow:
            workflow[key] = True
            _write_text(config_path, _json_text(parsed))
        return {"success": True, "path": "config.json"}

    if action == REMEDY_ACTION["BACKFILL_MILESTONES"]:
        missing = compute_missing_milestone_versions(archive_dir, milestones_path)
        today = _local_today()
        backfilled = 0
        for version in missing:
            try:
                try:
                    snapshot = _read_text(Path(archive_dir) / f"{version}-ROADMAP.md")
                except OSError:
                    snapshot = None
                title = re.search(r"^#\s+(.+)$", snapshot, re.M) if snapshot else None
                if title:
                    name = re.sub(r"^v[\d.]+\s*", "", re.sub(r"^Milestone\s+", "", title.group(1), flags=re.I)).strip()
                else:
                    name = version
                label = f" {name}" if name and name != version else ""
                entry = (f"## {version}{label} (Backfilled: {today})\n\n**Note:** Synthesized from archive snapshot by "
                         f"`/gsd-health --backfill`. Original completion date unknown.\n\n---\n\n")
                existing = _read_text(milestones_path) if os.path.exists(milestones_path) else ""
                if not existing.strip():
                    _write_text(milestones_path, f"# Milestones\n\n{entry}")
                else:
                    header = re.match(r"^(#{1,3}\s+[^\n]*\n\n?)", existing)
                    if header:
                        _write_text(milestones_path, header.group(1) + entry + existing[len(header.group(1)):])
                    else:
                        _write_text(milestones_path, entry + existing)
                backfilled += 1
            except (OSError, ValueError):
                pass
        return {"success": True, "detail": f"Backfilled {backfilled} milestone(s) into MILESTONES.md"}

    return {"success": False, "error": f'no repair handler registered for action "{action}"'}


def _detail(code, action, outcome):
    row = {"code": code, "action": action, "success": outcome["success"]}
    for key in ("path", "detail", "error"):
        if outcome.get(key):
            row[key] = outcome[key]
    return row


def apply_repairs(cwd, diagnostics, repair, backfill):
    """``--repair`` / ``--backfill`` dispatcher: ADVISE is never applied, DESTRUCTIVE is refused."""
    applied, refused, details = [], [], []
    paths = repair_paths(cwd)

    status_repairs = []
    if repair:
        for diagnostic in diagnostics:
            remedy, code = diagnostic["remedy"], diagnostic["code"]
            if remedy["action"] != REMEDY_ACTION["REPAIR_VERIFICATION_STATUS"] or remedy["risk"] == REMEDY_RISK["DESTRUCTIVE"]:
                continue
            status_repairs.append(diagnostic)
            try:
                outcome = run_repair_action(cwd, remedy["action"], paths, remedy.get("args"))
                details.append(_detail(code, remedy["action"], outcome))
                if outcome["success"]:
                    applied.append(code)
            except Exception as exc:  # noqa: BLE001 - mirrors the per-action catch-all upstream
                details.append({"code": code, "action": remedy["action"], "success": False, "error": str(exc)})

    regenerate_requested = repair and any(
        d["remedy"]["action"] == REMEDY_ACTION["REGENERATE_STATE"] and d["remedy"]["risk"] != REMEDY_RISK["DESTRUCTIVE"]
        for d in diagnostics)
    abort_message = None
    if regenerate_requested:
        try:
            _assert_verification_reports_readable(cwd)
        except _VerificationStatusError as exc:
            abort_message = str(exc)

    for diagnostic in diagnostics:
        remedy, code = diagnostic["remedy"], diagnostic["code"]
        if remedy["action"] == REMEDY_ACTION["ADVISE"]:
            continue
        if any(diagnostic is repaired for repaired in status_repairs):
            continue
        requested = (repair or backfill) if remedy["action"] == REMEDY_ACTION["BACKFILL_MILESTONES"] else repair
        if not requested:
            continue
        if remedy["risk"] == REMEDY_RISK["DESTRUCTIVE"]:
            refused.append(code)
            details.append({"code": code, "action": remedy["action"], "success": False,
                            "error": f"refused: '{remedy['action']}' is a destructive remedy and is not auto-applied by --repair"})
            continue
        if abort_message is not None:
            error = (abort_message if remedy["action"] == REMEDY_ACTION["REGENERATE_STATE"]
                     else f"not applied: the run stopped before its first write — {abort_message}")
            details.append({"code": code, "action": remedy["action"], "success": False, "error": error})
            continue
        try:
            outcome = run_repair_action(cwd, remedy["action"], paths)
            for extra in outcome.get("extraDetails") or []:
                row = {"code": code, "action": extra["action"], "success": extra["success"]}
                if extra.get("path"):
                    row["path"] = extra["path"]
                details.append(row)
            details.append(_detail(code, remedy["action"], outcome))
            if outcome["success"]:
                applied.append(code)
        except Exception as exc:  # noqa: BLE001
            details.append({"code": code, "action": remedy["action"], "success": False, "error": str(exc)})
    return {"applied": applied, "refused": refused, "details": details}
