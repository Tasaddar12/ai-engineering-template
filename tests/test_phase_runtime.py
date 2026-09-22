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

### Roadmap Evolution

None yet.

## Deferred Items

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: [YYYY-MM-DD HH:MM]
Stopped at: [Description]
Resume file: None
"""

PROJECT = """# Test Project

## What This Is

A project for exercising the runtime.

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| [Choice] | [Why] | [Pending] |

---
*Last updated: 2026-01-01 after setup*
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
        (planning / "PROJECT.md").write_text(PROJECT, encoding="utf-8", newline="\n")
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

    def test_resolve_model_inherits_when_no_override_is_configured(self):
        """Agent files carry no model; the host chooses unless config overrides."""
        result = self.run_verb("resolve-model", "coder")
        self.assertEqual(result["source"], "default")
        self.assertEqual(result["model"], "inherit")
        self.assertTrue(result["inherit"])

    def test_config_overrides_the_agent_model(self):
        self.run_verb("config-set", "agents.coder.model", "opus")
        result = self.run_verb("resolve-model", "coder")
        self.assertEqual(result["model"], "opus")
        self.assertEqual(result["source"], "config")
        self.assertFalse(result["inherit"])


class WorktreeIsolation(RuntimeCase):
    """Isolation resolution, wave integration and conservative cleanup.

    Every test runs against a real repository with real worktrees, because the
    behavior worth pinning here is git behavior, not the module bookkeeping.
    """

    def setUp(self):
        super().setUp()
        # A worktree root has to be ignored before the runtime will use it, and
        # a wave merges into the current branch, so never the default one.
        (self.directory / ".gitignore").write_text(
            ".worktrees/\n", encoding="utf-8", newline="\n")
        (self.directory / "src").mkdir()
        (self.directory / "src" / "kept.txt").write_text(
            "kept\n", encoding="utf-8", newline="\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "baseline")
        self.base_branch = self.git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        self.git("checkout", "-q", "-b", "work")

    def worktree_git(self, path, *args):
        return subprocess.run(["git", *args], cwd=str(path), capture_output=True,
                              text=True, check=False)

    def commit_in(self, path, relative, content, message):
        """Make one real commit inside a linked worktree."""
        target = Path(path) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
        self.worktree_git(path, "add", "-A")
        self.worktree_git(path, "commit", "-qm", message)

    # --- resolution -------------------------------------------------------

    def test_isolation_resolves_to_a_worktree_model(self):
        result = self.run_verb("dispatch-isolation", "--phase", "1")
        self.assertIn(result["isolation"],
                      ("harness-worktree", "orchestrator-worktree"))
        self.assertEqual(result["phase"], "1")

    def test_isolation_never_resolves_to_none(self):
        """There is no configuration, and no flag, that buys an unisolated run."""
        for key, value in (("workflow.isolation", "none"),
                           ("workflow.isolation", "sequential-ish"),
                           ("workflow.isolation", "false")):
            with self.subTest(key=key, value=value):
                self.run_verb("config-set", key, value)
                failure = self.run_verb("dispatch-isolation", expect_ok=False)
                self.assertEqual(failure["code"], "bad-isolation")
                self.assertIn("cannot be turned off", failure["error"])
        self.run_verb("config-set", "workflow.isolation", "auto")

    def test_a_retired_opt_out_key_has_no_effect(self):
        """`use_worktrees: false` used to disable isolation. It no longer exists,
        so a project carrying it from an older config is still isolated."""
        self.run_verb("config-set", "workflow.use_worktrees", "false")
        result = self.run_verb("dispatch-isolation")
        self.assertIn(result["isolation"],
                      ("harness-worktree", "orchestrator-worktree"))

    def test_runtime_isolation_fails_when_the_worktree_root_is_not_ignored(self):
        (self.directory / ".gitignore").write_text("", encoding="utf-8", newline="\n")
        self.git("commit", "-qam", "stop ignoring the worktree root")
        self.run_verb("config-set", "workflow.isolation", "orchestrator-worktree")
        failure = self.run_verb("dispatch-isolation", expect_ok=False)
        self.assertEqual(failure["code"], "root-not-ignored")
        self.assertIn(".gitignore", failure["error"])

    # --- creation ---------------------------------------------------------

    def test_create_makes_an_immediate_child_on_its_own_branch(self):
        result = self.run_verb("worktree.create", "01-01", "--phase", "1",
                               "--files", "src/kept.txt")
        path = Path(result["worktree"])
        self.assertTrue(path.is_dir())
        self.assertEqual(path.parent.name, ".worktrees")
        self.assertTrue(result["branch"].startswith("phase-01-01-"))
        self.assertEqual(
            self.worktree_git(path, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip(),
            result["branch"])

    def test_create_refuses_a_protected_branch_name(self):
        failure = self.run_verb("worktree.create", "01-01", "--branch", "main",
                                expect_ok=False)
        self.assertEqual(failure["code"], "protected-branch")

    def test_create_refuses_a_branch_outside_the_isolation_namespaces(self):
        failure = self.run_verb("worktree.create", "01-01", "--branch", "my-feature",
                                expect_ok=False)
        self.assertEqual(failure["code"], "bad-branch")

    def test_record_agent_needs_the_branch_the_harness_created(self):
        failure = self.run_verb("worktree.record-agent", "01-01", expect_ok=False)
        self.assertEqual(failure["code"], "missing-branch")

    # --- integration ------------------------------------------------------

    def test_merge_wave_integrates_a_committed_branch(self):
        created = self.run_verb("worktree.create", "01-01", "--phase", "1",
                                "--files", "src/added.txt")
        self.commit_in(created["worktree"], "src/added.txt", "added\n", "feat: add")
        result = self.run_verb("worktree.merge-wave", "--phase", "1")
        self.assertTrue(result["wave_clean"])
        self.assertEqual(len(result["merged"]), 1)
        self.assertEqual(result["merged"][0]["commits"], 1)
        self.assertTrue((self.directory / "src" / "added.txt").is_file(),
                        "the merged work must be present in the integration tree")

    def test_merge_wave_blocks_a_deletion_the_plan_did_not_declare(self):
        created = self.run_verb("worktree.create", "01-01", "--phase", "1",
                                "--files", "src/kept.txt")
        self.worktree_git(created["worktree"], "rm", "-q", "src/kept.txt")
        self.worktree_git(created["worktree"], "commit", "-qm", "chore: remove")
        result = self.run_verb("worktree.merge-wave", "--phase", "1")
        self.assertFalse(result["wave_clean"])
        self.assertEqual(result["blocked"][0]["status"], "blocked")
        self.assertEqual(result["blocked"][0]["undeclared_deletions"],
                         ["src/kept.txt"])
        self.assertTrue((self.directory / "src" / "kept.txt").is_file(),
                        "a blocked branch must not have been merged")

    def test_merge_wave_allows_a_declared_deletion(self):
        created = self.run_verb("worktree.create", "01-01", "--phase", "1",
                                "--files", "src/kept.txt",
                                "--deletions", "src/kept.txt")
        self.worktree_git(created["worktree"], "rm", "-q", "src/kept.txt")
        self.worktree_git(created["worktree"], "commit", "-qm", "chore: remove")
        result = self.run_verb("worktree.merge-wave", "--phase", "1")
        self.assertTrue(result["wave_clean"], "a declared deletion is authorized")
        self.assertFalse((self.directory / "src" / "kept.txt").exists())

    def test_merge_wave_blocks_a_rename_that_removes_an_undeclared_path(self):
        """A rename is a removal of the old path, and needs the same authority.

        Git reports a move as a single `R` entry naming the destination, so with
        rename detection on the vanished source never reaches the guard.
        """
        created = self.run_verb("worktree.create", "01-01", "--phase", "1",
                                "--files", "src/kept.txt,src/moved.txt")
        self.worktree_git(created["worktree"], "mv", "src/kept.txt", "src/moved.txt")
        self.worktree_git(created["worktree"], "commit", "-qm", "refactor: move")
        result = self.run_verb("worktree.merge-wave", "--phase", "1")
        self.assertFalse(result["wave_clean"])
        self.assertEqual(result["blocked"][0]["undeclared_deletions"],
                         ["src/kept.txt"])
        self.assertTrue((self.directory / "src" / "kept.txt").is_file())

    def test_merge_wave_allows_a_rename_whose_source_is_declared(self):
        created = self.run_verb("worktree.create", "01-01", "--phase", "1",
                                "--files", "src/kept.txt,src/moved.txt",
                                "--deletions", "src/kept.txt")
        self.worktree_git(created["worktree"], "mv", "src/kept.txt", "src/moved.txt")
        self.worktree_git(created["worktree"], "commit", "-qm", "refactor: move")
        result = self.run_verb("worktree.merge-wave", "--phase", "1")
        self.assertTrue(result["wave_clean"])
        self.assertTrue((self.directory / "src" / "moved.txt").is_file())
        self.assertFalse((self.directory / "src" / "kept.txt").exists())

    def test_merge_wave_reports_out_of_scope_paths_without_blocking(self):
        created = self.run_verb("worktree.create", "01-01", "--phase", "1",
                                "--files", "src/declared.txt")
        self.commit_in(created["worktree"], "src/declared.txt", "a\n",
                       "feat: declared")
        self.commit_in(created["worktree"], "other/stray.txt", "b\n", "feat: stray")
        result = self.run_verb("worktree.merge-wave", "--phase", "1")
        self.assertTrue(result["wave_clean"],
                        "scope drift is advisory, never blocking")
        self.assertEqual(result["merged"][0]["out_of_scope"], ["other/stray.txt"])

    def test_merge_wave_reports_a_branch_with_no_commits(self):
        self.run_verb("worktree.create", "01-01", "--phase", "1")
        result = self.run_verb("worktree.merge-wave", "--phase", "1")
        self.assertFalse(result["wave_clean"])
        self.assertEqual(result["blocked"][0]["status"], "empty")

    def test_merge_wave_refuses_a_protected_target_branch(self):
        self.run_verb("worktree.create", "01-01", "--phase", "1")
        self.git("checkout", "-q", self.base_branch)
        failure = self.run_verb("worktree.merge-wave", "--phase", "1",
                                expect_ok=False)
        self.assertEqual(failure["code"], "protected-branch")

    def test_merge_wave_refuses_a_dirty_integration_tree(self):
        self.run_verb("worktree.create", "01-01", "--phase", "1")
        (self.directory / "src" / "dirty.txt").write_text("x\n", encoding="utf-8")
        failure = self.run_verb("worktree.merge-wave", "--phase", "1",
                                expect_ok=False)
        self.assertEqual(failure["code"], "dirty-tree")

    # --- cleanup ----------------------------------------------------------

    def test_cleanup_removes_a_worktree_whose_branch_is_merged(self):
        created = self.run_verb("worktree.create", "01-01", "--phase", "1",
                                "--files", "src/added.txt")
        self.commit_in(created["worktree"], "src/added.txt", "added\n", "feat: add")
        self.run_verb("worktree.merge-wave", "--phase", "1")
        result = self.run_verb("worktree.cleanup-wave", "--phase", "1")
        self.assertEqual(len(result["removed"]), 1)
        self.assertEqual(result["preserved"], [])
        self.assertFalse(Path(created["worktree"]).exists())

    def test_cleanup_preserves_an_unmerged_worktree_with_a_reason(self):
        created = self.run_verb("worktree.create", "01-01", "--phase", "1")
        self.commit_in(created["worktree"], "src/unmerged.txt", "x\n",
                       "feat: unmerged")
        result = self.run_verb("worktree.cleanup-wave", "--phase", "1")
        self.assertEqual(result["removed"], [])
        self.assertEqual(len(result["preserved"]), 1)
        self.assertIn("status is", result["preserved"][0]["reason"])
        self.assertTrue(Path(created["worktree"]).is_dir(),
                        "unmerged work is work in progress and must be kept")

    def test_cleanup_preserves_a_blocked_entry(self):
        created = self.run_verb("worktree.create", "01-01", "--phase", "1",
                                "--files", "src/kept.txt")
        self.worktree_git(created["worktree"], "rm", "-q", "src/kept.txt")
        self.worktree_git(created["worktree"], "commit", "-qm", "chore: remove")
        self.run_verb("worktree.merge-wave", "--phase", "1")
        result = self.run_verb("worktree.cleanup-wave", "--phase", "1")
        self.assertEqual(result["removed"], [])
        self.assertIn("blocked", result["preserved"][0]["reason"])

    # --- inspection -------------------------------------------------------

    def test_list_separates_the_primary_checkout_from_managed_worktrees(self):
        created = self.run_verb("worktree.create", "01-01", "--phase", "1")
        result = self.run_verb("worktree.list")
        primary = [item for item in result["worktrees"] if item["is_primary"]]
        managed = [item for item in result["worktrees"] if item["managed"]]
        self.assertEqual(len(primary), 1)
        self.assertEqual(len(managed), 1)
        self.assertEqual(managed[0]["branch"], created["branch"])
        self.assertTrue(result["root_ignored"])

    def test_reap_orphans_prunes_metadata_without_touching_a_live_checkout(self):
        live = self.run_verb("worktree.create", "01-01", "--phase", "1")
        orphan = self.run_verb("worktree.create", "01-02", "--phase", "1")
        shutil.rmtree(orphan["worktree"], ignore_errors=True)
        result = self.run_verb("worktree.reap-orphans")
        self.assertEqual(result["pruned_count"], 1)
        self.assertTrue(Path(live["worktree"]).is_dir(),
                        "reaping must never remove a checkout that still exists")

    def test_health_warns_when_the_worktree_root_is_not_ignored(self):
        (self.directory / ".gitignore").write_text("", encoding="utf-8", newline="\n")
        self.git("commit", "-qam", "stop ignoring the worktree root")
        result = self.run_verb("worktree.health")
        self.assertFalse(result["ok_to_isolate"])
        self.assertIn("root-not-ignored",
                      [item["code"] for item in result["findings"]])


if __name__ == "__main__":
    unittest.main()


class StateDigestBudget(RuntimeCase):
    """STATE.md is a digest: bounded sections, nothing lost when they trim."""

    def test_decision_lands_in_project_md_as_well_as_the_digest(self):
        result = self.run_verb("state.add-decision", "Use Postgres",
                               "--rationale", "Already operated in-house")
        self.assertIsNotNone(result["project_record"])
        project = self.read(".planning/PROJECT.md")
        self.assertIn("| Use Postgres | Already operated in-house |", project)
        self.assertIn("- Use Postgres", self.read(".planning/STATE.md"))
        # The placeholder row is replaced, not accumulated alongside real rows.
        self.assertNotIn("| [Choice] |", project)

    def test_a_technology_decision_carries_its_evidence_into_the_record(self):
        """Validation before proposal lives in the rationale, not a separate file."""
        self.run_verb(
            "state.add-decision", "Use SQLite for the local cache",
            "--rationale",
            "Spike: python spike/cache.py, 10k rows, p99 3ms, no lock contention",
            "--outcome", "Accepted")
        project = self.read(".planning/PROJECT.md")
        self.assertIn("| Use SQLite for the local cache |", project)
        self.assertIn("p99 3ms", project)
        self.assertIn("| Accepted |", project)

    def test_a_reversal_is_a_new_row_rather_than_an_edit(self):
        self.run_verb("state.add-decision", "Use SQLite for the local cache",
                      "--rationale", "No server to operate", "--outcome", "Accepted")
        self.run_verb("state.add-decision", "Move the cache to DuckDB",
                      "--rationale", "Replaces SQLite: measured 3x on the same spike",
                      "--outcome", "Accepted")
        project = self.read(".planning/PROJECT.md")
        self.assertIn("| Use SQLite for the local cache |", project)
        self.assertIn("| Move the cache to DuckDB |", project)
        # The superseded decision stays readable: no strikethrough, no "Closed".
        self.assertNotIn("~~", project)

    def test_decisions_trim_to_the_cap_without_losing_any(self):
        """Safe to trim precisely because PROJECT.md already holds them all."""
        for index in range(7):
            self.run_verb("state.add-decision", "Decision " + str(index))
        state = self.read(".planning/STATE.md")
        kept = [line for line in state.splitlines() if line.startswith("- Decision ")]
        self.assertEqual(len(kept), 5)
        self.assertIn("- Decision 6", state)
        self.assertNotIn("- Decision 0", state)
        project = self.read(".planning/PROJECT.md")
        for index in range(7):
            self.assertIn("| Decision " + str(index) + " |", project)

    def test_blockers_are_never_dropped_to_make_room(self):
        """An open blocker has no durable copy, so nothing may trim it away."""
        for index in range(12):
            self.run_verb("state.add-blocker", "Blocker " + str(index))
        state = self.read(".planning/STATE.md")
        kept = [line for line in state.splitlines() if line.startswith("- Blocker ")]
        self.assertEqual(len(kept), 12)
        self.assertIn("- Blocker 0", state)

    def test_an_over_cap_blocker_section_is_reported_instead(self):
        for index in range(12):
            self.run_verb("state.add-blocker", "Blocker " + str(index))
        warnings = self.run_verb("planning.validate", "--skip",
                                 "codebase-freshness")["warnings"]
        self.assertTrue(any(item["check"] == "state-caps"
                            and "Blockers/Concerns" in item["message"]
                            for item in warnings), warnings)

    def test_clear_blocker_removes_the_entry(self):
        self.run_verb("state.add-blocker", "Phase 1: flaky integration suite")
        self.run_verb("state.add-blocker", "Phase 2: missing staging secrets")
        result = self.run_verb("state.clear-blocker", "flaky integration")
        self.assertEqual(result["removed"], ["Phase 1: flaky integration suite"])
        state = self.read(".planning/STATE.md")
        self.assertNotIn("flaky integration", state)
        self.assertIn("missing staging secrets", state)
        # Removed, not struck through.
        self.assertNotIn("~~", state)

    def test_clearing_the_last_blocker_restores_the_placeholder(self):
        self.run_verb("state.add-blocker", "Only blocker")
        self.run_verb("state.clear-blocker", "Only blocker")
        body = self.read(".planning/STATE.md").split("### Blockers/Concerns")[1]
        self.assertIn("None yet.", body.split("###")[0])

    def test_clear_blocker_reports_a_miss_instead_of_silently_passing(self):
        result = self.run_verb("state.clear-blocker", "nothing like this",
                               expect_ok=False)
        self.assertEqual(result["code"], "no-match")

    def test_roadmap_evolution_is_bounded_too(self):
        for index in range(8):
            self.run_verb("state.add-roadmap-evolution", "Change " + str(index))
        state = self.read(".planning/STATE.md")
        kept = [line for line in state.splitlines() if line.startswith("- Change ")]
        self.assertEqual(len(kept), 5)
        self.assertNotIn("- Change 0", state)

    def test_deferred_items_write_a_table_row(self):
        self.run_verb("state.add-deferred", "perf", "Cache the roadmap parse",
                      "--status", "Deferred", "--milestone", "v1")
        state = self.read(".planning/STATE.md")
        self.assertIn("| perf | Cache the roadmap parse | Deferred |", state)
        self.assertNotIn("| *(none)* |", state)

    def test_digest_stays_inside_its_line_budget_under_sustained_use(self):
        """The failure the budget exists to prevent: a week of appends."""
        for index in range(30):
            self.run_verb("state.add-decision", "Decision " + str(index))
            self.run_verb("state.add-roadmap-evolution", "Change " + str(index))
            self.run_verb("state.add-blocker", "Blocker " + str(index))
            self.run_verb("state.clear-blocker", "Blocker " + str(index))
        lines = len(self.read(".planning/STATE.md").splitlines())
        self.assertLessEqual(lines, 150, "STATE.md grew past its digest budget")


class PlanningValidation(RuntimeCase):
    """Drift is reported, and reporting never stalls the session by default."""

    def setUp(self):
        super().setUp()
        requirements = self.directory / ".planning" / "REQUIREMENTS.md"
        requirements.write_text(
            "# Requirements\n\n## Traceability\n\n"
            "| Requirement | Phase | Status |\n"
            "|-------------|-------|--------|\n"
            "| REQ-01 | Phase 1 | Pending |\n"
            "| REQ-02 | Phase 1 | Pending |\n"
            "| REQ-03 | Phase 2 | Pending |\n",
            encoding="utf-8", newline="\n")

    def validate(self, *args, expect_ok=True):
        return self.run_verb("planning.validate", "--skip", "codebase-freshness",
                             *args, expect_ok=expect_ok)

    def test_a_conforming_project_reports_clean(self):
        result = self.validate()
        self.assertEqual(result["status"], "clean", result["warnings"])

    def test_warnings_do_not_fail_the_verb(self):
        """Warn-only is the default so a cosmetic finding cannot stall work."""
        self.run_verb("state.add-blocker", "Phase 1: ~~resolved~~ flaky suite")
        result = self.validate()
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "warnings")
        self.assertFalse(result["strict"])

    def test_strict_is_opt_in_and_fails(self):
        self.run_verb("state.add-blocker", "Phase 1: ~~resolved~~ flaky suite")
        result = self.validate("--strict", expect_ok=False)
        self.assertEqual(result["code"], "validation-failed")

    def test_strikethrough_is_reported(self):
        self.run_verb("state.add-decision", "~~Use MySQL~~ use Postgres")
        checks = [item["check"] for item in self.validate()["warnings"]]
        self.assertIn("retirement-markers", checks)

    def test_in_place_closure_marker_is_reported(self):
        self.run_verb("state.add-blocker", "Phase 1: missing secrets (Closed)")
        messages = [item["message"] for item in self.validate()["warnings"]]
        self.assertTrue(any("closed in place" in message for message in messages),
                        messages)

    def test_a_section_outside_the_contract_is_reported(self):
        state = self.directory / ".planning" / "STATE.md"
        state.write_text(state.read_text(encoding="utf-8")
                         + "\n## Performance Metrics\n\nNot tracked.\n",
                         encoding="utf-8", newline="\n")
        messages = [item["message"] for item in self.validate()["warnings"]]
        self.assertTrue(any("not part of the STATE contract" in message
                            for message in messages), messages)

    def test_a_missing_required_section_is_reported(self):
        state = self.directory / ".planning" / "STATE.md"
        text = state.read_text(encoding="utf-8").replace("## Session Continuity",
                                                         "## Retired Section")
        state.write_text(text, encoding="utf-8", newline="\n")
        messages = [item["message"] for item in self.validate()["warnings"]]
        self.assertTrue(any("Session Continuity" in message for message in messages),
                        messages)

    def test_requirements_pending_under_a_complete_phase_are_reported(self):
        self.run_verb("phase.complete", "1")
        messages = [item["message"] for item in self.validate()["warnings"]]
        self.assertTrue(any("still Pending" in message for message in messages),
                        messages)

    def test_an_over_cap_section_edited_by_hand_is_reported(self):
        state = self.directory / ".planning" / "STATE.md"
        hand_written = "\n".join("- Decision " + str(index) for index in range(9))
        text = state.read_text(encoding="utf-8").replace(
            "### Decisions\n\nNone yet.", "### Decisions\n\n" + hand_written)
        state.write_text(text, encoding="utf-8", newline="\n")
        checks = [item["check"] for item in self.validate()["warnings"]]
        self.assertIn("state-caps", checks)

    def test_an_oversized_digest_is_reported(self):
        state = self.directory / ".planning" / "STATE.md"
        padding = "\n".join("Filler line " + str(index) for index in range(200))
        state.write_text(state.read_text(encoding="utf-8") + "\n" + padding,
                         encoding="utf-8", newline="\n")
        messages = [item["message"] for item in self.validate()["warnings"]]
        self.assertTrue(any("digest budget" in message for message in messages),
                        messages)


class CodebaseMapFreshness(RuntimeCase):
    """A map's freshness is a git question, not a stamp anyone has to maintain."""

    def write_map(self, name, body="# Map\n\nContents.\n", commit=True):
        target = self.directory / ".planning" / "codebase" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8", newline="\n")
        if commit:
            self.git("add", "-A")
            self.git("commit", "-qm", "write " + name)
        return target

    def touch(self, name, contents, message):
        (self.directory / name).write_text(contents, encoding="utf-8", newline="\n")
        self.git("add", "-A")
        self.git("commit", "-qm", message)

    def states(self):
        return {report["name"]: report
                for report in self.run_verb("codebase.status")["maps"]}

    def test_an_absent_map_reports_missing_with_its_focus(self):
        result = self.run_verb("codebase.status")
        states = {report["name"]: report for report in result["maps"]}
        self.assertEqual(states["ARCHITECTURE.md"]["state"], "missing")
        self.assertEqual(states["ARCHITECTURE.md"]["focus"], "arch")
        self.assertEqual(states["STACK.md"]["focus"], "tech")
        self.assertIn("arch", result["focus_areas"])

    def test_a_committed_map_is_fresh_and_names_the_commit_that_wrote_it(self):
        self.write_map("ARCHITECTURE.md")
        report = self.states()["ARCHITECTURE.md"]
        self.assertEqual(report["state"], "fresh")
        self.assertTrue(report["revision"])
        self.assertEqual(report["commits_since"], 0)

    def test_an_uncommitted_map_is_current_by_definition(self):
        """Just written: nothing can have happened to the code since."""
        self.write_map("STACK.md", commit=False)
        report = self.states()["STACK.md"]
        self.assertEqual(report["state"], "fresh")
        self.assertTrue(report.get("pending"))

    def test_a_manifest_change_makes_the_stack_map_stale(self):
        self.write_map("STACK.md")
        self.touch("package.json", '{"name": "app"}\n', "add a manifest")
        report = self.states()["STACK.md"]
        self.assertEqual(report["state"], "stale")
        self.assertEqual(report["commits_since"], 1)

    def test_the_architecture_map_tolerates_ordinary_churn(self):
        """One commit is movement, not a changed architecture."""
        self.write_map("ARCHITECTURE.md")
        self.touch("app.py", "print('hi')\n", "one source change")
        report = self.states()["ARCHITECTURE.md"]
        self.assertEqual(report["state"], "fresh")
        self.assertEqual(report["commits_since"], 1)

    def test_planning_record_writes_do_not_age_the_architecture_map(self):
        """A phase write-up is not a change to the architecture it describes."""
        self.write_map("ARCHITECTURE.md")
        for index in range(20):
            self.run_verb("state.add-blocker", "Blocker " + str(index))
            self.git("add", "-A")
            self.git("commit", "-qm", "planning churn " + str(index))
        report = self.states()["ARCHITECTURE.md"]
        self.assertEqual(report["commits_since"], 0)
        self.assertEqual(report["state"], "fresh")

    def test_sustained_source_movement_makes_the_architecture_map_stale(self):
        self.write_map("ARCHITECTURE.md")
        for index in range(15):
            self.touch("module_" + str(index) + ".py", "value = " + str(index) + "\n",
                       "source change " + str(index))
        self.assertEqual(self.states()["ARCHITECTURE.md"]["state"], "stale")

    def test_rewriting_a_stale_map_makes_it_fresh_again(self):
        """Regeneration needs no bookkeeping step - writing the file is enough."""
        self.write_map("STACK.md")
        self.touch("package.json", '{"name": "app"}\n', "add a manifest")
        self.assertEqual(self.states()["STACK.md"]["state"], "stale")
        self.write_map("STACK.md", "# Map\n\nRewritten.\n")
        self.assertEqual(self.states()["STACK.md"]["state"], "fresh")

    def test_freshness_survives_a_squashed_history(self):
        """A recorded SHA would not: squash is this project's merge default."""
        self.write_map("STACK.md")
        self.touch("notes.md", "notes\n", "unrelated work")
        self.git("checkout", "-q", "--orphan", "squashed")
        self.git("add", "-A")
        self.git("commit", "-qm", "squashed history")
        report = self.states()["STACK.md"]
        self.assertIn(report["state"], ("fresh", "stale"))
        self.assertIsNotNone(report["revision"])

    def test_the_staleness_threshold_is_configurable(self):
        config = self.directory / ".planning" / "config.yaml"
        config.write_text(config.read_text(encoding="utf-8")
                          + "codebase:\n  staleness:\n    architecture: 1\n",
                          encoding="utf-8", newline="\n")
        self.write_map("ARCHITECTURE.md")
        self.touch("app.py", "print('hi')\n", "one source change")
        self.assertEqual(self.states()["ARCHITECTURE.md"]["state"], "stale")

    def test_an_unfilled_skeleton_is_not_reported_as_a_missing_map(self):
        """Before onboarding every record is an example, so nothing is drift."""
        project = self.directory / ".planning" / "PROJECT.md"
        project.write_text("> **Unfilled adoption skeleton:** CHANGEME.\n\n"
                           + project.read_text(encoding="utf-8"),
                           encoding="utf-8", newline="\n")
        warnings = self.run_verb("planning.validate")["warnings"]
        self.assertEqual([item for item in warnings
                          if item["check"] == "codebase-freshness"], [])

    def test_an_onboarded_project_is_told_its_maps_are_missing(self):
        warnings = self.run_verb("planning.validate")["warnings"]
        missing = [item["record"] for item in warnings
                   if item["check"] == "codebase-freshness"]
        self.assertEqual(sorted(missing), ["ARCHITECTURE.md", "STACK.md"])

    def test_validation_reports_a_stale_map(self):
        self.write_map("STACK.md")
        self.touch("package.json", '{"name": "app"}\n', "add a manifest")
        warnings = self.run_verb("planning.validate")["warnings"]
        self.assertTrue(any(item["check"] == "codebase-freshness"
                            and "commits have touched" in item["message"]
                            for item in warnings), warnings)


class RequirementTraceability(RuntimeCase):
    """The Status column only means something if something writes it."""

    def setUp(self):
        super().setUp()
        (self.directory / ".planning" / "REQUIREMENTS.md").write_text(
            "# Requirements\n\n## v1 Requirements\n\n"
            "### Authentication\n\n- AUTH-01: Sign in\n- AUTH-02: Sign out\n\n"
            "## Traceability\n\n"
            "| Requirement | Phase | Status |\n"
            "|-------------|-------|--------|\n"
            "| AUTH-01 | Phase 1 | Pending |\n"
            "| AUTH-02 | Phase 1 | Pending |\n"
            "| DATA-01 | Phase 2 | Pending |\n",
            encoding="utf-8", newline="\n")

    def test_set_status_rewrites_only_the_status_cell(self):
        result = self.run_verb("requirements.set-status", "AUTH-01", "Complete")
        self.assertEqual(result["previous"], "Pending")
        self.assertTrue(result["changed"])
        requirements = self.read(".planning/REQUIREMENTS.md")
        self.assertIn("| AUTH-01 | Phase 1 | Complete |", requirements)
        self.assertIn("| AUTH-02 | Phase 1 | Pending |", requirements)
        # The requirement text itself is never annotated.
        self.assertIn("- AUTH-01: Sign in", requirements)

    def test_an_unknown_status_is_refused(self):
        result = self.run_verb("requirements.set-status", "AUTH-01", "Doneish",
                               expect_ok=False)
        self.assertEqual(result["code"], "bad-status")

    def test_an_unknown_requirement_is_refused_rather_than_invented(self):
        result = self.run_verb("requirements.set-status", "NOPE-01", "Complete",
                               expect_ok=False)
        self.assertEqual(result["code"], "unknown-requirement")
        self.assertNotIn("NOPE-01", self.read(".planning/REQUIREMENTS.md"))

    def test_close_phase_closes_every_requirement_that_phase_owns(self):
        result = self.run_verb("requirements.close-phase", "1")
        self.assertEqual(sorted(result["changed"]), ["AUTH-01", "AUTH-02"])
        requirements = self.read(".planning/REQUIREMENTS.md")
        self.assertIn("| AUTH-01 | Phase 1 | Complete |", requirements)
        self.assertIn("| DATA-01 | Phase 2 | Pending |", requirements)

    def test_close_phase_reports_ids_the_table_does_not_carry(self):
        result = self.run_verb("requirements.close-phase", "1",
                               "--requirements", "AUTH-01", "GHOST-09")
        self.assertEqual(result["unknown"], ["GHOST-09"])
        self.assertEqual(result["changed"], ["AUTH-01"])

    def test_close_phase_refuses_when_the_phase_owns_nothing(self):
        result = self.run_verb("requirements.close-phase", "9", expect_ok=False)
        self.assertEqual(result["code"], "no-requirements")

    def test_outstanding_excludes_closed_requirements(self):
        self.run_verb("requirements.set-status", "AUTH-01", "Complete")
        self.run_verb("requirements.set-status", "AUTH-02", "Deferred")
        outstanding = self.run_verb("requirements.outstanding")
        self.assertEqual([row["Requirement"] for row in outstanding["outstanding"]],
                         ["DATA-01"])

    def test_closing_the_phase_clears_the_validation_warning(self):
        self.run_verb("phase.complete", "1")
        before = [item["check"] for item
                  in self.run_verb("planning.validate", "--skip",
                                   "codebase-freshness")["warnings"]]
        self.assertIn("requirements-traceability", before)
        self.run_verb("requirements.close-phase", "1")
        after = [item["check"] for item
                 in self.run_verb("planning.validate", "--skip",
                                  "codebase-freshness")["warnings"]]
        self.assertNotIn("requirements-traceability", after)


class InstallSeedContract(RuntimeCase):
    """The installed STATE.md must be the shape the state verbs write into.

    The seed is not a copy of the template - its values are install-specific
    prose - but its structure has to match, because `state.*` edits fields by
    regex and silently does nothing when the field line is absent. A seed that
    drifts from the template produces verbs that report success and write
    nothing, for the whole life of the project until onboarding rewrites it.
    """

    SEED = ROOT / ".ai" / "install-assets" / "STATE.txt"
    TEMPLATE = ROOT / ".ai" / "templates" / "state.md"

    def install(self, asset, record):
        """Write one install asset into the fixture as its planning record."""
        target = self.directory / ".planning" / record
        target.write_text(asset.read_text(encoding="utf-8"),
                          encoding="utf-8", newline="\n")
        return target

    def setUp(self):
        super().setUp()
        (self.directory / ".planning" / "STATE.md").write_text(
            self.SEED.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")

    @staticmethod
    def headings(markdown):
        return [line.strip() for line in markdown.splitlines()
                if line.startswith("#") and not line.startswith("####")]

    def template_skeleton(self):
        """The File Template block: the shape an adopting project starts from."""
        body = self.TEMPLATE.read_text(encoding="utf-8")
        start = body.index("```markdown")
        return body[start:body.index("```", start + 3)]

    def test_the_seed_carries_the_templates_sections(self):
        self.assertEqual(self.headings(self.SEED.read_text(encoding="utf-8")),
                         self.headings(self.template_skeleton()))

    def test_the_seed_carries_every_field_the_runtime_writes(self):
        seed = self.SEED.read_text(encoding="utf-8")
        for field in ("Phase:", "Plan:", "Status:", "Last activity:",
                      "Last session:", "Stopped at:", "Resume file:", "Progress:"):
            with self.subTest(field=field):
                self.assertIn("\n" + field, seed,
                              field + " is absent, so the verb that writes it "
                              "would silently do nothing")

    def test_begin_phase_actually_writes_to_the_installed_file(self):
        self.run_verb("state.begin-phase", "1", "Foundation")
        position = self.read(".planning/STATE.md")
        self.assertIn("Phase: 1 of 2 (Foundation)", position)
        self.assertNotIn("Phase: Not started", position)

    def test_record_session_actually_writes_to_the_installed_file(self):
        self.run_verb("state.record-session", "--stopped-at", "planned the phase")
        continuity = self.read(".planning/STATE.md")
        self.assertIn("Stopped at: planned the phase", continuity)
        self.assertNotIn("Stopped at: Workflow installed", continuity)

    def test_the_digest_verbs_reach_their_sections(self):
        self.run_verb("state.add-blocker", "Phase 1: staging secrets missing")
        self.run_verb("state.add-roadmap-evolution", "Phase 2 inserted")
        self.run_verb("state.add-deferred", "perf", "Cache the roadmap parse")
        state = self.read(".planning/STATE.md")
        self.assertIn("- Phase 1: staging secrets missing", state)
        self.assertIn("- Phase 2 inserted", state)
        self.assertIn("| perf | Cache the roadmap parse |", state)

    def test_updating_progress_keeps_the_blank_line_before_the_next_heading(self):
        for _ in range(3):
            self.run_verb("state.update-progress")
        self.assertIn("%\n\n## Accumulated Context", self.read(".planning/STATE.md"))

    def test_a_freshly_installed_record_set_validates_clean(self):
        """What an adopting project sees on day one should not be drift."""
        assets = ROOT / ".ai" / "install-assets"
        for asset, record in (("PROJECT.txt", "PROJECT.md"),
                              ("REQUIREMENTS.txt", "REQUIREMENTS.md")):
            self.install(assets / asset, record)
        result = self.run_verb("planning.validate", "--skip", "codebase-freshness")
        self.assertEqual(result["status"], "clean", result["warnings"])

    def test_a_decision_reaches_the_installed_project_record(self):
        """The seed's Key Decisions table has to exist for the log to be durable."""
        self.install(ROOT / ".ai" / "install-assets" / "PROJECT.txt", "PROJECT.md")
        result = self.run_verb("state.add-decision", "Use Postgres",
                               "--rationale", "Already operated in-house")
        self.assertIsNotNone(result["project_record"],
                             result.get("warning", "no warning reported"))
        self.assertIn("| Use Postgres | Already operated in-house |",
                      self.read(".planning/PROJECT.md"))
