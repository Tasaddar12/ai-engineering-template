"""Behavioral tests for the phase runtime against real repositories.

Every test drives `phase.py` the way a workflow does — as a subprocess emitting
JSON — so the tests exercise the contract the workflows depend on, not internals.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".ai" / "runtime" / "phase.py"

ROADMAP = """# Roadmap: Test Project

## Overview

A roadmap for exercising the runtime.

## Phases

- [ ] **Phase 1: Foundation** - Set up the base
- [ ] **Phase 2: Features** - Build the thing

## Phase Details

### Phase 1: Foundation
**Goal**: Set up the base
**Depends on**: Nothing (first phase)
**Requirements**: REQ-01, REQ-02
**Plans**: 2 plans

Plans:
- [ ] 01-01: Scaffold
- [ ] 01-02: Wire it up

### Phase 2: Features
**Goal**: Build the thing
**Depends on**: Phase 1
**Requirements**: REQ-03
**Plans**: 1 plan

Plans:
- [ ] 02-01: The feature

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 0/2 | Not started | - |
| 2. Features | 0/1 | Not started | - |
"""

STATE = """---
workflow_state_version: '1.0'
status: planning
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Current Position

Phase: [X] of [Y] ([Phase name])
Plan: [A] of [B] in current phase
Status: [Ready to plan]
Last activity: [YYYY-MM-DD] - [What happened]

Progress: [__________] 0%

## Accumulated Context

### Decisions

None yet.

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: [YYYY-MM-DD HH:MM]
Stopped at: [Description]
Resume file: None
"""

CONFIG = """commit_docs: true
verification:
  commands: []
"""


class RuntimeCase(unittest.TestCase):
    """A real git repository with a populated .planning directory."""

    def setUp(self):
        self.directory = Path(tempfile.mkdtemp(prefix="phase-runtime-"))
        self.addCleanup(shutil.rmtree, self.directory, ignore_errors=True)
        self.git("init", "-q", ".")
        self.git("config", "user.email", "runtime@example.test")
        self.git("config", "user.name", "Runtime Test")
        planning = self.directory / ".planning"
        planning.mkdir()
        (planning / "ROADMAP.md").write_text(ROADMAP, encoding="utf-8", newline="\n")
        (planning / "STATE.md").write_text(STATE, encoding="utf-8", newline="\n")
        (planning / "config.yaml").write_text(CONFIG, encoding="utf-8", newline="\n")
        (planning / "PROJECT.md").write_text("# Project\n", encoding="utf-8", newline="\n")
        (planning / "REQUIREMENTS.md").write_text(
            "# Requirements\n\n- REQ-01: one\n- REQ-02: two\n- REQ-03: three\n",
            encoding="utf-8", newline="\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "initial")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=str(self.directory),
                              capture_output=True, text=True, check=False)

    def run_verb(self, *args, expect_ok=True):
        """Invoke one runtime verb and return its parsed result."""
        environment = dict(os.environ, PYTHONIOENCODING="utf-8")
        completed = subprocess.run([sys.executable, str(RUNTIME), "query", *args],
                                   cwd=str(self.directory), capture_output=True,
                                   text=True, encoding="utf-8", env=environment)
        self.assertNotIn("Traceback", completed.stderr,
                         "verb raised instead of returning a result: " + completed.stderr)
        payload = json.loads(completed.stdout)
        if expect_ok:
            self.assertTrue(payload.get("ok"), "verb failed: " + completed.stdout)
        else:
            self.assertFalse(payload.get("ok"), "verb unexpectedly succeeded")
        return payload

    def read(self, relative):
        return (self.directory / relative).read_text(encoding="utf-8")


class PhaseCrud(RuntimeCase):
    def test_add_allocates_next_number_and_directory(self):
        result = self.run_verb("phase.add", "API key session hardening",
                               "--goal", "IDP-managed sessions")
        self.assertEqual(result["phase_number"], "3")
        self.assertEqual(result["padded"], "03")
        self.assertEqual(result["slug"], "api-key-session-hardening")
        self.assertTrue((self.directory / result["directory"]).is_dir())
        roadmap = self.read(".planning/ROADMAP.md")
        self.assertIn("### Phase 3: API key session hardening", roadmap)
        self.assertIn("**Goal**: IDP-managed sessions", roadmap)
        self.assertIn("- [ ] **Phase 3: API key session hardening**", roadmap)

    def test_add_warns_on_goal_shaped_description(self):
        result = self.run_verb(
            "phase.add",
            "We want to redesign API key sessions so they are hardened. They should "
            "be managed through an IDP rather than static keys.")
        self.assertIn("warning", result)

    def test_insert_allocates_decimal_after_target(self):
        result = self.run_verb("phase.insert", "1", "Rotate leaked key")
        self.assertEqual(result["phase_number"], "1.1")
        self.assertEqual(result["padded"], "01.1")
        roadmap = self.read(".planning/ROADMAP.md")
        self.assertIn("### Phase 1.1: Rotate leaked key (INSERTED)", roadmap)
        self.assertLess(roadmap.index("Phase 1.1"), roadmap.index("### Phase 2:"))

    def test_insert_numbers_second_decimal_sequentially(self):
        self.run_verb("phase.insert", "1", "First fix")
        second = self.run_verb("phase.insert", "1", "Second fix")
        self.assertEqual(second["phase_number"], "1.2")

    def test_remove_renumbers_later_phases_and_directories(self):
        self.run_verb("phase.add", "Third phase")
        removed = self.run_verb("phase.remove", "2")
        self.assertEqual(removed["removed"], "2")
        self.assertEqual(removed["renumbered"], [{"from": "3", "to": "2"}])
        roadmap = self.read(".planning/ROADMAP.md")
        self.assertIn("### Phase 2: Third phase", roadmap)
        self.assertNotIn("### Phase 3:", roadmap)
        self.assertTrue((self.directory / ".planning/phases/02-third-phase").is_dir())

    def test_remove_refuses_a_phase_with_completed_plans(self):
        self.run_verb("roadmap.update-plan-progress", "01-01")
        failure = self.run_verb("phase.remove", "1", expect_ok=False)
        self.assertEqual(failure["code"], "phase-started")
        self.assertIn("### Phase 1: Foundation", self.read(".planning/ROADMAP.md"))

    def test_edit_updates_entry_checklist_and_directory(self):
        self.run_verb("phase.add", "Original title", "--goal", "Original goal")
        result = self.run_verb("phase.edit", "3", "--name", "Renamed title",
                               "--goal", "Revised goal")
        self.assertEqual(result["changed"]["name"], "Renamed title")
        roadmap = self.read(".planning/ROADMAP.md")
        self.assertIn("### Phase 3: Renamed title", roadmap)
        self.assertIn("**Goal**: Revised goal", roadmap)
        self.assertIn("- [ ] **Phase 3: Renamed title**", roadmap)
        self.assertNotIn("Original title", roadmap)
        self.assertTrue((self.directory / ".planning/phases/03-renamed-title").is_dir())

    def test_edit_without_fields_is_rejected(self):
        failure = self.run_verb("phase.edit", "1", expect_ok=False)
        self.assertEqual(failure["code"], "no-changes")

    def test_edit_preserves_the_plan_checklist(self):
        self.run_verb("phase.edit", "1", "--goal", "A different goal")
        roadmap = self.read(".planning/ROADMAP.md")
        self.assertIn("- [ ] 01-01: Scaffold", roadmap)
        self.assertIn("- [ ] 01-02: Wire it up", roadmap)

    def test_missing_phase_reports_a_handled_failure(self):
        failure = self.run_verb("roadmap.get-phase", "9", expect_ok=False)
        self.assertEqual(failure["code"], "phase-not-found")


class PlanProgress(RuntimeCase):
    def test_advancing_a_plan_ticks_it_and_updates_state(self):
        result = self.run_verb("roadmap.update-plan-progress", "01-01")
        self.assertEqual(result["progress"]["completed_plans"], 1)
        self.assertIn("- [x] 01-01: Scaffold", self.read(".planning/ROADMAP.md"))

    def test_completing_every_plan_marks_the_phase_complete(self):
        self.run_verb("roadmap.update-plan-progress", "01-01")
        self.run_verb("roadmap.update-plan-progress", "01-02")
        roadmap = self.read(".planning/ROADMAP.md")
        self.assertIn("- [x] **Phase 1: Foundation**", roadmap)
        self.assertIn("| 1. Foundation | 2/2 | Complete |", roadmap)

    def test_phase_complete_ticks_all_plans(self):
        result = self.run_verb("phase.complete", "1")
        self.assertEqual(result["plans_completed"], 2)
        roadmap = self.read(".planning/ROADMAP.md")
        self.assertIn("- [x] 01-01: Scaffold", roadmap)
        self.assertIn("- [x] 01-02: Wire it up", roadmap)

    def test_state_frontmatter_is_derived_from_the_roadmap(self):
        self.run_verb("phase.complete", "1")
        state = self.run_verb("state.get")
        self.assertEqual(state["progress"]["completed_phases"], 1)
        self.assertEqual(state["progress"]["completed_plans"], 2)
        self.assertEqual(state["progress"]["total_plans"], 3)


class StateWrites(RuntimeCase):
    def test_record_session_updates_continuity_without_losing_the_file(self):
        self.run_verb("state.record-session", "--stopped-at", "Phase 1 discussed",
                      "--resume-file", ".planning/phases/01-foundation/01-CONTEXT.md")
        state = self.read(".planning/STATE.md")
        self.assertIn("Stopped at: Phase 1 discussed", state)
        self.assertIn("Resume file: .planning/phases/01-foundation/01-CONTEXT.md", state)
        self.assertTrue(state.endswith("\n"))
        self.assertIn("## Session Continuity", state)

    def test_begin_phase_points_current_position_at_the_phase(self):
        self.run_verb("state.begin-phase", "2", "--status", "In progress")
        state = self.read(".planning/STATE.md")
        self.assertIn("Phase: 2 of 2 (Features)", state)
        self.assertIn("Status: In progress", state)

    def test_decisions_and_blockers_replace_placeholder_text(self):
        self.run_verb("state.add-decision", "Use the IDP for session issuance")
        self.run_verb("state.add-blocker", "Waiting on IDP tenant access")
        view = self.run_verb("state.get")
        self.assertEqual(view["decisions"], ["Use the IDP for session issuance"])
        self.assertEqual(view["blockers"], ["Waiting on IDP tenant access"])
        self.assertNotIn("None yet.", self.read(".planning/STATE.md").split(
            "### Decisions")[1].split("###")[0])

    def test_roadmap_evolution_section_is_created_on_demand(self):
        self.run_verb("state.add-roadmap-evolution", "Phase 3 added: hardening")
        state = self.read(".planning/STATE.md")
        self.assertIn("### Roadmap Evolution", state)
        self.assertIn("- Phase 3 added: hardening", state)

    def test_missing_state_file_reports_a_handled_failure(self):
        (self.directory / ".planning/STATE.md").unlink()
        failure = self.run_verb("state.record-session", "--stopped-at", "x",
                                expect_ok=False)
        self.assertEqual(failure["code"], "missing-state")


class Todos(RuntimeCase):
    def test_add_writes_frontmatter_and_infers_the_area(self):
        result = self.run_verb("todo.add", "Rotate service account keys",
                               "--severity", "minor",
                               "--files", "src/auth/keys.ts:44")
        self.assertEqual(result["area"], "auth")
        content = self.read(result["file"])
        self.assertIn("title: Rotate service account keys", content)
        self.assertIn("severity: minor", content)
        self.assertIn("  - src/auth/keys.ts:44", content)
        self.assertIn("## Problem", content)

    def test_invalid_severity_is_rejected(self):
        failure = self.run_verb("todo.add", "Something", "--severity", "urgent",
                                expect_ok=False)
        self.assertEqual(failure["code"], "bad-severity")

    def test_sync_replaces_the_state_section_wholesale(self):
        self.run_verb("todo.add", "First todo", "--severity", "major")
        self.run_verb("todo.add", "Second todo", "--severity", "blocker")
        self.run_verb("state.sync-todos")
        section = self.read(".planning/STATE.md").split("### Pending Todos")[1]
        section = section.split("###")[0]
        self.assertIn("- Second todo (general, blocker)", section)
        self.assertIn("- First todo (general, major)", section)
        self.assertNotIn("None yet.", section)

    def test_completing_a_todo_moves_it_out_of_pending(self):
        added = self.run_verb("todo.add", "Transient idea")
        name = Path(added["file"]).name
        self.run_verb("todo.complete", name)
        self.assertFalse((self.directory / added["file"]).exists())
        self.assertTrue((self.directory / ".planning/todos/completed" / name).exists())

    def test_match_phase_scores_shared_keywords(self):
        self.run_verb("todo.add", "Harden the foundation scaffold")
        matches = self.run_verb("todo.match-phase", "1")
        self.assertEqual(matches["phase_name"], "Foundation")
        self.assertEqual(len(matches["matches"]), 1)
        self.assertIn("foundation", matches["matches"][0]["reasons"])


class QuickTasks(RuntimeCase):
    def test_create_allocates_a_dated_sequence_directory(self):
        result = self.run_verb("quick.create", "Fix typo in login copy")
        self.assertTrue(result["id"].endswith("-001-fix-typo-login-copy"))
        self.assertEqual(result["status"], "open")
        self.assertTrue((self.directory / result["record"]).is_file())

    def test_second_task_on_the_same_day_increments_the_sequence(self):
        self.run_verb("quick.create", "First task")
        second = self.run_verb("quick.create", "Second task")
        self.assertEqual(second["sequence"], 2)

    def test_update_records_completion(self):
        created = self.run_verb("quick.create", "Fix the thing")
        updated = self.run_verb("quick.update", created["id"], "--status", "complete",
                                "--files", "src/app.py")
        self.assertEqual(updated["status"], "complete")
        self.assertTrue(updated["completed"])
        self.assertEqual(updated["files"], ["src/app.py"])

    def test_listing_filters_by_status(self):
        first = self.run_verb("quick.create", "Open task")
        second = self.run_verb("quick.create", "Done task")
        self.run_verb("quick.update", second["id"], "--status", "complete")
        open_tasks = self.run_verb("quick.list", "--status", "open")
        self.assertEqual([task["id"] for task in open_tasks["tasks"]], [first["id"]])


class Milestones(RuntimeCase):
    def test_create_declares_an_in_progress_milestone(self):
        result = self.run_verb("milestone.create", "v1.1 Hardening",
                               "--goal", "IDP-managed credentials")
        self.assertEqual(result["status"], "in_progress")
        roadmap = self.read(".planning/ROADMAP.md")
        self.assertIn("**v1.1 Hardening**", roadmap)
        self.assertIn("**Milestone Goal:** IDP-managed credentials", roadmap)
        listed = self.run_verb("milestone.list")
        self.assertEqual(listed["current"], "v1.1 Hardening")

    def test_duplicate_milestone_is_rejected(self):
        self.run_verb("milestone.create", "v1.1 Hardening")
        failure = self.run_verb("milestone.create", "v1.1 Hardening", expect_ok=False)
        self.assertEqual(failure["code"], "milestone-exists")

    def test_complete_requires_confirmation(self):
        self.run_verb("milestone.create", "v1.1 Hardening")
        failure = self.run_verb("milestone.complete", "v1.1", expect_ok=False)
        self.assertEqual(failure["code"], "needs-confirm")

    def test_complete_refuses_while_phases_are_open(self):
        self.run_verb("milestone.create", "v1.1 Hardening")
        self.run_verb("phase.add", "Hardening work")
        failure = self.run_verb("milestone.complete", "v1.1", "--confirm",
                                expect_ok=False)
        self.assertIn(failure["code"], ("milestone-incomplete", "empty-milestone"))

    def test_complete_writes_the_milestones_entry(self):
        self.run_verb("milestone.create", "v1.1 Hardening")
        self.run_verb("phase.add", "Hardening work", "--goal", "Harden it")
        self.run_verb("phase.complete", "3")
        result = self.run_verb("milestone.complete", "v1.1", "--name", "Hardening",
                               "--confirm")
        self.assertEqual(result["plans"], 1)
        entry = self.read(".planning/MILESTONES.md")
        self.assertIn("## v1.1 Hardening (Shipped:", entry)
        self.assertIn("**Phases completed:** 3", entry)


class Bundles(RuntimeCase):
    def test_phase_op_reports_artifacts_and_paths(self):
        bundle = self.run_verb("init.phase-op", "1")
        self.assertTrue(bundle["phase_found"])
        self.assertEqual(bundle["padded_phase"], "01")
        self.assertEqual(bundle["phase_name"], "Foundation")
        self.assertFalse(bundle["has_context"])
        self.assertEqual(bundle["expected_phase_dir"], ".planning/phases/01-foundation")
        self.assertEqual(bundle["paths"]["roadmap"], ".planning/ROADMAP.md")

    def test_phase_op_reports_a_missing_phase_without_failing(self):
        bundle = self.run_verb("init.phase-op", "9")
        self.assertFalse(bundle["phase_found"])

    def test_progress_bundle_flags_incomplete_execution(self):
        directory = self.directory / ".planning/phases/01-foundation"
        directory.mkdir(parents=True)
        (directory / "01-01-PLAN.md").write_text("# plan\n", encoding="utf-8")
        bundle = self.run_verb("init.progress")
        self.assertEqual(bundle["incomplete_phase"], "1")
        self.assertEqual(bundle["totals"]["plans"], 3)

    def test_progress_bundle_has_no_incomplete_phase_when_summaries_match(self):
        directory = self.directory / ".planning/phases/01-foundation"
        directory.mkdir(parents=True)
        (directory / "01-01-PLAN.md").write_text("# plan\n", encoding="utf-8")
        (directory / "01-01-SUMMARY.md").write_text("# summary\n", encoding="utf-8")
        bundle = self.run_verb("init.progress")
        self.assertIsNone(bundle["incomplete_phase"])

    def test_todo_bundle_renders_state_ready_markdown(self):
        self.run_verb("todo.add", "An idea", "--severity", "minor")
        bundle = self.run_verb("init.todos")
        self.assertEqual(bundle["todo_count"], 1)
        self.assertTrue(bundle["pending_read_ok"])
        self.assertIn("- An idea (general, minor)", bundle["pending_todos_markdown"])

    def test_plan_phase_bundle_carries_models_and_requirements(self):
        bundle = self.run_verb("init.plan-phase", "1")
        self.assertIn("phase-preparer", bundle["models"])
        self.assertEqual(bundle["requirements"], ["REQ-01", "REQ-02"])
        self.assertEqual(bundle["project_requirements"],
                         ["REQ-01", "REQ-02", "REQ-03"])

    def test_unknown_bundle_reports_a_handled_failure(self):
        failure = self.run_verb("init.nonsense", expect_ok=False)
        self.assertEqual(failure["code"], "unknown-verb")


class CommitAndConfig(RuntimeCase):
    def test_commit_stages_only_the_named_files(self):
        (self.directory / "untracked.txt").write_text("stray\n", encoding="utf-8")
        self.run_verb("phase.add", "Committed phase")
        result = self.run_verb("commit", "docs(roadmap): add phase",
                               "--files", ".planning/ROADMAP.md")
        self.assertTrue(result["committed"])
        tracked = self.git("ls-files").stdout
        self.assertNotIn("untracked.txt", tracked)

    def test_commit_is_skipped_when_commit_docs_is_false(self):
        self.run_verb("config-set", "commit_docs", "false")
        self.run_verb("phase.add", "Another phase")
        result = self.run_verb("commit", "docs: nope", "--files", ".planning/ROADMAP.md")
        self.assertFalse(result["committed"])
        self.assertEqual(result["reason"], "commit_docs is false")

    def test_config_round_trips_dotted_keys(self):
        self.run_verb("config-set", "workflow.text_mode", "true")
        value = self.run_verb("config-get", "workflow.text_mode")
        self.assertIs(value["value"], True)
        self.assertIn("commands: []", self.read(".planning/config.yaml"))

    def test_generate_slug_is_stable(self):
        result = self.run_verb("generate-slug", "API Key Session hardening")
        self.assertEqual(result["slug"], "api-key-session-hardening")


class Dispatch(RuntimeCase):
    def test_identity_names_the_runtime(self):
        result = self.run_verb("runtime-identity")
        self.assertEqual(result["packageName"], "ai-phase-runtime")

    def test_unknown_verb_reports_a_handled_failure(self):
        failure = self.run_verb("no-such-verb", expect_ok=False)
        self.assertEqual(failure["code"], "unknown-verb")

    def test_resolve_model_reads_the_agent_definition(self):
        result = self.run_verb("resolve-model", "coder")
        self.assertEqual(result["source"], "agent-file")
        self.assertTrue(result["model"])

    def test_config_overrides_the_agent_model(self):
        self.run_verb("config-set", "agents.coder.model", "opus")
        result = self.run_verb("resolve-model", "coder")
        self.assertEqual(result["model"], "opus")
        self.assertEqual(result["source"], "config")


if __name__ == "__main__":
    unittest.main()
