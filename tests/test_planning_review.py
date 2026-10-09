"""Offline evidence/repair fixtures; never mutate the adoption skeleton."""
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".ai/runtime"))

from lib import planning_review  # noqa: E402
from lib.paths import Workspace, write_text  # noqa: E402
from lib.results import VerbError  # noqa: E402
from lib.text import join_frontmatter, split_frontmatter  # noqa: E402


STATE = """# Project State

## Current Position

Phase: 1 of 1 (Foundation)
Plan: 1 of 1 in current phase
Status: Planning
Last activity: 2026-10-09 - Preserve this original wording.

## Accumulated Context

### Decisions

- Our deliberately unusual architecture stays intact.

### Pending Todos

None yet.

### Blockers/Concerns

- A human decision is still needed.

### Roadmap Evolution

None yet.

## Deferred Items

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: 2026-10-09 11:00
Stopped at: Waiting for the decision; do not mark complete.
Resume file: None
"""
ROADMAP = """# Roadmap

## Phases

- [ ] **Phase 1: Foundation** - Keep intent

## Phase Details

### Phase 1: Foundation
**Goal**: Preserve the exact approved outcome.
**Depends on**: Nothing (first phase)
**Requirements**: REQ-01
**Plans**: TBD

Plans:
- [ ] 01-01: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 0/1 | Not started | - |
"""
REQUIREMENTS = """# Requirements

## v1 Requirements

- [ ] **REQ-01**: The wording approved by our project owner.

## v2 Requirements

None yet.

## Out of Scope

No unapproved product changes.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REQ-01 | Phase 1 | Pending |
"""
PROJECT = """# Specific project identity

## What This Is

Our existing project identity.

## Core Value

Keep the established outcomes.

## Requirements

### Validated

None yet.

### Active

See REQUIREMENTS.md.

### Out of Scope

No unrelated features.

## Context

Preserve this narrative.

## Constraints

Offline fixtures.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Preserve the historic choice | The original argument | Accepted |
"""


class PlanningReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.workspace = Workspace(self.root)
        # Workspace uses Git root only when one exists; this isolated fixture
        # has none and therefore cannot resolve to the template checkout.
        self.assertEqual(self.root.resolve(), self.workspace.root)
        self.planning = self.workspace.planning
        write_text(self.planning / "PROJECT.md", PROJECT)
        write_text(self.planning / "REQUIREMENTS.md", REQUIREMENTS)
        write_text(self.planning / "ROADMAP.md", ROADMAP)
        self.metadata = {"workflow_state_version": "1.0", "status": "planning",
                         "progress": {"total_phases": 99, "completed_phases": 99,
                                      "total_plans": 99, "completed_plans": 99,
                                      "percent": 100}, "custom_project_field": "keep me"}
        write_text(self.planning / "STATE.md", join_frontmatter(self.metadata, STATE))

    def tearDown(self):
        self.temp.cleanup()

    def checks(self, report):
        return {item["check"] for item in report["findings"]}

    def test_dry_run_and_apply_are_idempotent_and_preserve_unfinished_prose(self):
        before = self.workspace.state.read_bytes()
        preview = planning_review.repair(self.workspace)
        self.assertTrue(preview["dry_run"])
        self.assertEqual([], preview["changed"])
        self.assertEqual(before, self.workspace.state.read_bytes())
        self.assertIn("derive-state-progress", str(preview["repairs"]))
        result = planning_review.repair(self.workspace, apply=True, expected=preview["fingerprint"])
        self.assertEqual([".planning/STATE.md"], result["changed"])
        metadata, body = split_frontmatter(self.workspace.state.read_text(encoding="utf-8"))
        self.assertEqual(STATE, body)
        self.assertEqual("planning", metadata["status"])
        self.assertEqual("keep me", metadata["custom_project_field"])
        self.assertEqual(0, metadata["progress"]["completed_plans"])
        self.assertEqual([], planning_review.repair(self.workspace)["repairs"])
        self.assertEqual(REQUIREMENTS, self.workspace.requirements.read_text(encoding="utf-8"))

    def test_restore_unique_state_heading_keeps_all_original_lines(self):
        missing = STATE.replace("## Current Position\n\n", "").replace("## Session Continuity\n\n", "")
        write_text(self.workspace.state, join_frontmatter(self.metadata, missing))
        preview = planning_review.repair(self.workspace)
        self.assertIn("restore-state-heading", str(preview["repairs"]))
        planning_review.repair(self.workspace, apply=True, expected=preview["fingerprint"])
        _, body = split_frontmatter(self.workspace.state.read_text(encoding="utf-8"))
        self.assertEqual(STATE, body)

    def test_restore_missing_digest_container_uses_existing_sections(self):
        missing = STATE.replace("## Accumulated Context\n\n", "")
        write_text(self.workspace.state, join_frontmatter(self.metadata, missing))
        preview = planning_review.repair(self.workspace)
        planning_review.repair(self.workspace, apply=True, expected=preview["fingerprint"])
        _, body = split_frontmatter(self.workspace.state.read_text(encoding="utf-8"))
        self.assertEqual(STATE, body)

    def test_ambiguous_missing_heading_is_reported_without_invented_content(self):
        missing = STATE.replace("## Current Position\n\n", "").replace("Plan: 1 of 1 in current phase\n", "")
        write_text(self.workspace.state, join_frontmatter(self.metadata, missing))
        report = planning_review.review(self.workspace)
        self.assertIn("template-section", self.checks(report))
        self.assertNotIn("restore-state-heading", str(report["repairs"]))

    def test_apply_requires_review_and_rejects_changed_evidence(self):
        with self.assertRaises(VerbError) as caught:
            planning_review.repair(self.workspace, apply=True)
        self.assertEqual("review-required", caught.exception.code)
        report = planning_review.review(self.workspace)
        write_text(self.workspace.project, PROJECT + "\nA later recorded instruction.\n")
        before = self.workspace.state.read_bytes()
        with self.assertRaises(VerbError) as caught:
            planning_review.repair(self.workspace, apply=True, expected=report["fingerprint"])
        self.assertEqual("stale-review", caught.exception.code)
        self.assertEqual(before, self.workspace.state.read_bytes())

    def test_checked_summary_conflict_blocks_counter_refresh(self):
        write_text(self.workspace.roadmap, ROADMAP.replace("- [ ] 01-01", "- [x] 01-01"))
        directory = self.planning / "phases/01-foundation"
        write_text(directory / "01-01-SUMMARY.md", "---\nstatus: blocked\ncommits: [deadbeef]\n---\nStill missing required work.\n")
        report = planning_review.review(self.workspace)
        self.assertIn("completion-evidence", self.checks(report))
        self.assertEqual([], report["repairs"])
        self.assertIn("blocked", (directory / "01-01-SUMMARY.md").read_text(encoding="utf-8"))

    def test_summary_presence_alone_does_not_mark_anything_complete(self):
        directory = self.planning / "phases/01-foundation"
        write_text(directory / "01-01-SUMMARY.md", "---\nstatus: complete\ncommits: [deadbeef]\n---\nAn unsupported claim.\n")
        preview = planning_review.repair(self.workspace)
        planning_review.repair(self.workspace, apply=True, expected=preview["fingerprint"])
        metadata, _ = split_frontmatter(self.workspace.state.read_text(encoding="utf-8"))
        self.assertEqual(0, metadata["progress"]["completed_phases"])
        self.assertIn("- [ ] 01-01", self.workspace.roadmap.read_text(encoding="utf-8"))

    def test_missing_ids_statuses_dependencies_and_local_refs_are_evidence(self):
        bad = REQUIREMENTS.replace("REQ-01 | Phase 1 | Pending", "REQ-01 | Phase 19 | Complete")
        bad += "\n[broken](missing.md)\n[remote](https://example.com)\n```markdown\n[example](also-missing.md)\n```\n"
        write_text(self.workspace.requirements, bad)
        write_text(self.workspace.roadmap, ROADMAP.replace("Nothing (first phase)", "Phase 7").replace("REQ-01", "NOPE-02"))
        report = planning_review.review(self.workspace)
        self.assertTrue({"requirement-id", "requirement-phase", "phase-dependency", "local-reference"}.issubset(self.checks(report)))
        references = [item for item in report["findings"] if item["check"] == "local-reference"]
        self.assertEqual(1, len(references))

    def test_duplicate_phase_and_plan_contract_are_not_automatically_repaired(self):
        write_text(self.workspace.roadmap, ROADMAP + "\n### Phase 1: Duplicate\n**Goal**: Another claim\n")
        directory = self.planning / "phases/01-foundation"
        write_text(directory / "01-01-PLAN.md", "---\nphase: 99-wrong\nplan: '01'\ndepends_on: [77-01]\nrequirements: [UNKNOWN-01]\n---\n<tasks><task><action>Actual work.</action></task></tasks>\n")
        report = planning_review.review(self.workspace)
        self.assertTrue({"phase-id", "plan-id", "plan-contract", "plan-dependency"}.issubset(self.checks(report)))
        self.assertEqual([], report["repairs"])

    def test_quick_and_adr_semantics_remain_unresolved(self):
        write_text(self.planning / "quick/261009-001-small/QUICK.md", "---\nstatus: complete\n---\n# Quick\n## Task\nDo it.\n")
        historic = "---\nstatus: superseded\nsuperseded_by: []\n---\n# ADR-001\n\n## Context\nOriginal rationale must survive.\n"
        adr = self.planning / "decisions/ADR-001-choice.md"
        write_text(adr, historic)
        report = planning_review.review(self.workspace)
        self.assertTrue({"completion-evidence", "adr-replacement"}.issubset(self.checks(report)))
        planning_review.repair(self.workspace, apply=True, expected=report["fingerprint"])
        self.assertEqual(historic, adr.read_text(encoding="utf-8"))

    def test_skeleton_is_exempt_and_not_adopted(self):
        write_text(self.workspace.project, "> Unfilled adoption skeleton: CHANGEME\n" + PROJECT)
        before = self.workspace.state.read_bytes()
        report = planning_review.review(self.workspace)
        self.assertEqual("unfilled", report["status"])
        self.assertEqual([], report["repairs"])
        result = planning_review.repair(self.workspace, apply=True, expected=report["fingerprint"])
        self.assertEqual([], result["changed"])
        self.assertEqual(before, self.workspace.state.read_bytes())

    def test_unknown_selector_cannot_expand_repairs(self):
        with self.assertRaises(VerbError) as caught:
            planning_review.repair(self.workspace, only=["complete-everything"])
        self.assertEqual("unknown-repair", caught.exception.code)

    def test_malformed_verification_is_a_finding_and_never_a_repair(self):
        write_text(self.workspace.roadmap, ROADMAP.replace("- [ ] 01-01", "- [x] 01-01"))
        directory = self.planning / "phases/01-foundation"
        write_text(directory / "01-VERIFICATION.md", "---\nstatus: [malformed\n---\nA partial report.\n")
        report = planning_review.review(self.workspace)
        self.assertIn("frontmatter", self.checks(report))
        self.assertIn("completion-evidence", self.checks(report))
        self.assertEqual([], report["repairs"])

    def test_missing_authored_status_is_not_inferred(self):
        metadata = {key: value for key, value in self.metadata.items() if key != "status"}
        write_text(self.workspace.state, join_frontmatter(metadata, STATE))
        preview = planning_review.repair(self.workspace)
        planning_review.repair(self.workspace, apply=True, expected=preview["fingerprint"])
        actual, body = split_frontmatter(self.workspace.state.read_text(encoding="utf-8"))
        self.assertNotIn("status", actual)
        self.assertEqual(STATE, body)

    def test_wrong_level_heading_and_fenced_anchors_are_not_guessed(self):
        altered = STATE.replace("## Current Position", "### Current Position")
        write_text(self.workspace.state, join_frontmatter(self.metadata, altered))
        self.assertNotIn("restore-state-heading", str(planning_review.repair(self.workspace)["repairs"]))
        altered = STATE.replace("## Current Position\n\n", "```text\n").replace("## Accumulated Context", "```\n\n## Accumulated Context")
        write_text(self.workspace.state, join_frontmatter(self.metadata, altered))
        self.assertNotIn("restore-state-heading", str(planning_review.repair(self.workspace)["repairs"]))

    def test_dependency_cycle_is_reported_even_when_wave_metadata_is_missing(self):
        directory = self.planning / "phases/01-foundation"
        for identifier, dependency in (("01-01", "01-02"), ("01-02", "01-01")):
            write_text(directory / (identifier + "-PLAN.md"), "---\nphase: 01-foundation\nplan: '" + identifier[-2:] + "'\ndepends_on: ['" + dependency + "']\n---\n<tasks></tasks>\n")
        report = planning_review.review(self.workspace)
        self.assertTrue(any("dependency cycle" in finding["message"] for finding in report["findings"]))

    def test_canonical_checkpoint_does_not_need_automatic_task_fields(self):
        path = self.planning / "phases/01-foundation/01-01-PLAN.md"
        write_text(path, "---\nphase: 01-foundation\nplan: '01'\nwave: 1\ndepends_on: []\nfiles_modified: []\nrequirements: [REQ-01]\nacceptance: [REQ-01]\nmust_haves: {}\n---\n" +
                   "<objective>Decide it.</objective><context>Phase context.</context>\n" +
                   '<tasks><task type="checkpoint:decision"><decision>The open choice</decision><resume-signal>Select an option.</resume-signal></task></tasks>\n' +
                   "<verification>Check recorded decision.</verification><success_criteria>Decision recorded.</success_criteria><output>Record.</output>\n")
        report = planning_review.review(self.workspace)
        self.assertFalse(any(item["check"] == "plan-contract" for item in report["findings"]), report["findings"])

    def test_canonical_task_commit_hash_is_resolved_instead_of_metric_count(self):
        def git(*args):
            result = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        git("init", "-q")
        git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.test", "commit", "--allow-empty", "-qm", "Existing implementation evidence")
        revision = git("rev-parse", "HEAD")
        write_text(self.workspace.roadmap, ROADMAP.replace("- [ ] 01-01", "- [x] 01-01"))
        directory = self.planning / "phases/01-foundation"
        write_text(directory / "01-01-PLAN.md", "---\nphase: 01-foundation\nplan: '01'\n---\n<tasks></tasks>\n")
        write_text(directory / "01-01-SUMMARY.md", "---\nstatus: complete\nactuals:\n  commits: 1\n---\n## Task Commits\n1. Implementation: `" + revision + "`\n")
        write_text(directory / "01-VERIFICATION.md", "---\nstatus: passed\nrevision: " + revision + "\nverified_at: 2026-10-09T11:00:00Z\n---\nChecks actually passed.\n")
        report = planning_review.review(self.workspace)
        self.assertNotIn("completion-evidence", self.checks(report))
        self.assertIn("derive-state-progress", str(report["repairs"]))
        write_text(directory / "01-01-SUMMARY.md", "---\nstatus: complete\nactuals:\n  commits: 1\n---\n## Task Commits\nNone recorded.\n")
        report = planning_review.review(self.workspace)
        self.assertIn("completion-evidence", self.checks(report))
        self.assertEqual([], report["repairs"])


if __name__ == "__main__":
    unittest.main()
