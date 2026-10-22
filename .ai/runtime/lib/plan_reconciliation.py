"""Mechanical PLAN registration; objective meaning remains the caller's judgment."""
import hashlib
import json
import re

from . import phases, state
from .paths import read_text
from .results import require
from .roadmap import Roadmap
from .text import join_frontmatter, split_frontmatter


def reconcile(workspace, number, entries=None, apply=False, expected=None):
    """Propose, or apply and read back, the complete ordered on-disk plan set.

    The CLI holds planning_lock for this operation. Each PLAN is parsed once;
    the result includes its full objective for the caller's semantic review.
    """
    roadmap = Roadmap(workspace)
    phase = roadmap.require_phase(number)
    require(not phase.archived, "archived phase requires recovery", "phase-archived")
    directory = phases.find_directory(workspace, number, include_archived=False)
    require(directory is not None, "no phase directory for " + str(number), "no-phase-dir")
    expected_directory = workspace.phases_dir / (phase.padded + "-" + phase.slug)
    require(directory.resolve() == expected_directory.resolve()
            and directory.resolve().is_relative_to(workspace.root)
            and directory.resolve().is_relative_to(workspace.phases_dir.resolve()),
            "phase directory does not match roadmap: " + str(directory), "plan-directory")
    canonical = re.compile(re.escape(phase.padded) + r"-([0-9]{2})-PLAN\.md")
    plans = []
    sources = [(workspace.relative(workspace.roadmap), roadmap.content)]
    for source in (workspace.state, workspace.requirements,
                   directory / (phase.padded + "-CONTEXT.md"),
                   directory / (phase.padded + "-SPEC.md")):
        sources.append((workspace.relative(source), read_text(source, "")))
    # Include recognizable malformed names so they cannot silently disappear
    # from a valid-looking registration (case, phase and plan padding included).
    for path in sorted(directory.iterdir()):
        if not (path.name.lower().endswith("-plan.md")
                or path.name.lower().startswith("plan-")
                or "-plan-" in path.name.lower()):
            continue
        match = canonical.fullmatch(path.name)
        require(match is not None, "invalid PLAN filename: " + path.name, "plan-filename")
        require(path.is_file() and path.resolve().parent == directory.resolve(),
                "PLAN must be a file inside phase directory: " + path.name, "plan-path")
        content = read_text(path)
        sources.append((workspace.relative(path), content))
        metadata, body = split_frontmatter(content)
        require(metadata.get("phase") == directory.name,
                path.name + ": frontmatter phase must equal " + directory.name, "plan-frontmatter")
        plan_number = metadata.get("plan")
        # YAML's unquoted 01 is an integer; accept its canonical numeric value.
        require((isinstance(plan_number, str) and plan_number == match.group(1))
                or (type(plan_number) is int and plan_number == int(match.group(1))),
                path.name + ": frontmatter plan must equal " + match.group(1), "plan-frontmatter")
        objectives = re.findall(r"<objective>\s*(.*?)\s*</objective>", body, re.DOTALL)
        require(len(objectives) == 1 and objectives[0].strip(),
                path.name + ": expected one nonempty <objective>", "plan-objective")
        plans.append({"id": path.name[:-len("-PLAN.md")],
                      "file": workspace.relative(path), "objective": objectives[0].strip()})
    require(plans, "no PLAN files found for phase " + phase.padded, "missing-plans")
    identifiers = [plan["id"] for plan in plans]
    require(len(set(identifiers)) == len(identifiers), "duplicate PLAN IDs", "duplicate-plan")
    existing = phase.plans
    missing = [plan["id"] for plan in existing if plan["id"] not in identifiers]
    require(not missing, "roadmap IDs have no PLAN file: " + ", ".join(missing), "missing-plan-file")
    if entries is None:
        require(not apply, "--apply requires semantically reviewed --plans descriptions", "missing-plans")
        entries = [plan["id"] + ": " + " ".join(plan["objective"].split()) for plan in plans]
    # Reuse the canonical checklist validator before any mutation.
    candidate = Roadmap(workspace)
    candidate.content = candidate.set_plan_list(number, entries)
    proposed = candidate.require_phase(number).plans
    require([plan["id"] for plan in proposed] == identifiers,
            "--plans IDs, order and count must match the complete on-disk PLAN set",
            "plan-set-mismatch")
    fingerprint = hashlib.sha256(json.dumps(sources, ensure_ascii=False).encode("utf-8")).hexdigest()
    if apply:
        require(isinstance(expected, str) and expected,
                "--apply requires --expected from the inspected proposal", "missing-review")
    if expected:
        require(expected == fingerprint, "plan reconciliation inputs changed; review a fresh proposal",
                "stale-review")
    result = {"phase": phase.summary()["number"], "directory": workspace.relative(directory),
              "fingerprint": fingerprint,
              "count": len(plans), "plans": plans, "entries": entries,
              "delta": {"before": existing, "after": proposed,
                        "added": [identifier for identifier in identifiers
                                  if identifier not in {plan["id"] for plan in existing}],
                        "changed": proposed != existing},
              "applied": False, "verified": False}
    if not apply:
        return result
    candidate.content = candidate.set_checklist(number, candidate.require_phase(number).status == "Complete")
    candidate.content = candidate.update_progress_table()
    expected_state, progress = state.prepare_progress(workspace, candidate, registration_phase=number)
    expected_state.check_integrity()
    expected_state_content = join_frontmatter(expected_state.frontmatter, expected_state.body)
    state.register_plans(workspace, number, entries)
    saved = Roadmap(workspace)
    saved_phase = saved.require_phase(number)
    require(saved.content == candidate.content and saved_phase.plans == proposed
            and saved_phase.fields.get("plans") == str(len(plans)) + " plans",
            "saved ROADMAP plan IDs/descriptions/order/count/ticks differ from proposal; inspect both records",
            "plan-readback")
    require(read_text(workspace.state) == expected_state_content,
            "saved STATE progress or position differs from roadmap; inspect both records", "plan-readback")
    result.update(applied=True, verified=True, progress=progress)
    return result
