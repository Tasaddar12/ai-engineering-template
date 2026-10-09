"""Archive contract tests using isolated repositories and real CLI calls."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".ai/runtime/phase.py"
sys.path.insert(0, str(RUNTIME.parent))
from lib import archive
from lib.paths import Workspace
from lib.results import VerbError

ROADMAP = """# Roadmap

## Phases

- [x] **Phase 1: Foundation** - Completed foundation
- [ ] **Phase 2: Feature** - New feature

## Phase Details

### Phase 1: Foundation
**Goal**: Foundation
**Depends on**: Nothing
**Plans**: 1 plan

Plans:
- [x] 01-01: Build foundation

### Phase 2: Feature
**Goal**: Feature
**Depends on**: Phase 1
**Plans**: 1 plan

Plans:
- [ ] 02-01: Build feature

## Progress

| Phase | Plans Complete | Status | Completed |
|---|---|---|---|
| 1. Foundation | 1/1 | Complete | 2026-01-02 |
| 2. Feature | 0/1 | Not started | - |
"""
STATE = """---
status: planning
progress: {}
---
# Project State

## Current Position

Phase: 2 of 2 (Feature)
Plan: 1 of 1 in current phase
Status: Planning
Progress: [__________] 0%

## Accumulated Context

### Decisions

None yet.

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Resume file: None
"""


class PlanningArchive(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="planning-archive-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)
        self.write(".planning/ROADMAP.md", ROADMAP)
        self.write(".planning/STATE.md", STATE)
        self.write(".planning/PROJECT.md", "# Test project\n")
        self.write(".planning/config.yaml", "verification:\n  commands: []\n")
        self.write(".planning/phases/01-foundation/01-01-PLAN.md", "---\nphase: 01-foundation\n---\n# Plan\n")
        self.write(".planning/phases/01-foundation/01-01-SUMMARY.md", "---\nstatus: complete\n---\n# Summary\n\n## Accomplishments\n\nBuilt and checked foundation.\n")
        self.write(".planning/phases/01-foundation/01-VERIFICATION.md", "---\nstatus: passed\nrevision: abcdef\n---\n# Verified\n")
        self.write(".planning/phases/01-foundation/01-CONTEXT.md", "# Context\n\n## Decisions\n\nFoundation is shared.\n")
        self.write(".planning/phases/02-feature/02-01-PLAN.md", "---\ndepends_on: [01-01]\n---\n# Plan\n")

    def write(self, path, text):
        path = self.root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")

    def read(self, path):
        return (self.root / path).read_text(encoding="utf-8")

    def cli(self, *args, ok=True):
        result = subprocess.run([sys.executable, str(RUNTIME), "query", *args], cwd=self.root,
                                capture_output=True, text=True, encoding="utf-8",
                                env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        self.assertNotIn("Traceback", result.stderr, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["ok"], ok, data)
        self.assertEqual(result.returncode, 0 if ok else 1)
        return data

    def snapshot(self):
        return {path.relative_to(self.root).as_posix(): path.read_bytes()
                for path in self.root.rglob("*") if path.is_file() and ".git" not in path.parts}

    def quick(self, status="complete", evidence=True, name="260101-001-small-fix"):
        verification = "Checked the fixed output with unit tests." if evidence else "How the change was confirmed to work. Filled on completion."
        retirement = "\n## Retirement\n\nUser cancelled this obsolete change.\n" if status in ("abandoned", "obsolete") and evidence else ""
        self.write(".planning/quick/" + name + "/QUICK.md", "---\nstatus: " + status + "\ncompleted: '2026-01-02'\n---\n# Quick\n\n## Verification\n\n" + verification + retirement)
        return name

    def adr(self, status="superseded"):
        self.write(".planning/decisions/ADR-001-old.md", "---\nstatus: " + status + "\nsuperseded_by: [ADR-002-new]\n---\n# Old choice\n\nOriginal historical reasoning.\n")
        self.write(".planning/decisions/ADR-002-new.md", "---\nstatus: accepted\nsupersedes: []\n---\n# Replacement\n\nNew decision approved.\n")

    def test_phase_preview_is_deterministic_and_does_not_write(self):
        before = self.snapshot()
        first = self.cli("planning.archive", "phase", "1")
        second = self.cli("planning.archive", "phase", "01")
        self.assertEqual(first, second)
        self.assertTrue(first["dry_run"])
        self.assertEqual(first["state"], "preview")
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.root / ".planning/archive").exists())
        self.assertFalse((self.root / ".planning/.lock").exists())

    def test_phase_apply_preserves_ids_discovery_dependencies_and_active_counts(self):
        result = self.cli("planning.archive", "phase", "1", "--apply")
        target = self.root / ".planning/archive/phases/01-foundation"
        self.assertTrue((target / "01-01-SUMMARY.md").is_file())
        self.assertFalse((self.root / ".planning/phases/01-foundation").exists())
        self.assertEqual(result["state"], "archived")
        phase = self.cli("find-phase", "1")
        self.assertTrue(phase["phase_found"])
        self.assertTrue(phase["archived"])
        self.assertEqual(phase["phase_dir"], ".planning/archive/phases/01-foundation")
        self.assertTrue(self.cli("find-phase", "foundation")["archived"])
        self.assertEqual(self.cli("phase-plan-index", "1")["plans"][0]["id"], "01-01")
        self.assertTrue(self.cli("verification.status", "1")["status"] == "passed")
        phases = self.cli("phases.list")
        self.assertEqual((phases["count"], phases["archived_count"], phases["total_count"]), (1, 1, 2))
        progress = self.cli("init.progress")
        self.assertEqual(progress["totals"]["phases"], 1)
        self.assertEqual(progress["totals"]["plans"], 1)
        self.assertEqual(progress["next_phase"]["number"], "2")
        self.assertEqual(self.cli("init.plan-phase", "2")["prior_context"][0]["phase"], "1")
        self.assertEqual(self.cli("phase-plan-index", "2")["plans"][0]["depends_on"], ["01-01"])
        self.assertEqual(self.cli("roadmap.analyze")["blocked"], [])
        self.assertTrue(self.cli("phase.locate", "1")["phase_found"])
        self.assertEqual(self.cli("state.get")["progress"]["total_phases"], 1)
        self.assertEqual(self.cli("phase.add", "Next phase")["phase_number"], "3")
        self.assertEqual(self.cli("planning.archives")["count"], 1)
        self.assertIn("01-foundation", self.read(".planning/archive/INDEX.md"))

    def test_repeated_apply_has_no_additional_writes(self):
        first = self.cli("planning.archive", "phase", "1", "--apply")
        before = self.snapshot()
        second = self.cli("planning.archive", "phase", "1", "--apply")
        self.assertEqual(second["state"], "already_archived")
        self.assertEqual(second["recovery_id"], first["recovery_id"])
        self.assertEqual(before, self.snapshot())

    def test_collision_preflight_never_overwrites(self):
        self.write(".planning/archive/phases/01-foundation/keep.md", "Keep original.\n")
        before = self.snapshot()
        result = self.cli("planning.archive", "phase", "1", "--apply", ok=False)
        self.assertEqual(result["code"], "archive-collision")
        self.assertEqual(before, self.snapshot())

    def test_phase_status_without_outcome_evidence_is_denied(self):
        (self.root / ".planning/phases/01-foundation/01-VERIFICATION.md").unlink()
        before = self.snapshot()
        result = self.cli("planning.archive", "phase", "1", "--apply", ok=False)
        self.assertEqual(result["code"], "archive-evidence-required")
        self.assertEqual(before, self.snapshot())

    def test_active_phase_denied_even_with_legacy_evidence(self):
        self.write(".planning/legacy.md", "---\narchive_kind: phase\narchive_id: 02-feature\narchive_status: complete\narchive_reason: Reviewed legacy completion evidence.\n---\n")
        before = self.snapshot()
        result = self.cli("planning.archive", "phase", "2", "--evidence", ".planning/legacy.md", "--apply", ok=False)
        self.assertEqual(result["code"], "archive-active")
        self.assertEqual(before, self.snapshot())

    def test_explicit_legacy_selection_preserves_orphan_phase(self):
        self.write(".planning/phases/08-legacy/notes.md", "# Historical work\n")
        self.write(".planning/legacy.md", "---\narchive_kind: phase\narchive_id: 08-legacy\narchive_status: complete\narchive_reason: User confirmed completed legacy migration from recorded release.\n---\n")
        result = self.cli("planning.archive", "phase", ".planning/phases/08-legacy", "--evidence", ".planning/legacy.md", "--apply")
        self.assertEqual(result["state"], "archived")
        self.assertTrue(self.cli("find-phase", "8")["phase_found"])
        self.assertTrue(self.cli("find-phase", "8")["archived"])
        self.assertEqual(self.cli("find-phase", "8")["status"], "Complete")
        self.assertEqual(self.cli("phases.list")["archived_count"], 1)
        self.assertTrue(self.cli("find-phase", "legacy")["archived"])
        self.assertEqual(self.cli("phase.add", "New work")["phase_number"], "9")

    def test_links_rebase_in_moved_and_unmoved_records(self):
        self.write(".planning/specs/shared.md", "# Shared\n")
        self.write("source.py", "print('hello')\n")
        self.write(".planning/phases/01-foundation/nested/notes.md", "# Notes\n[context](../01-CONTEXT.md)\n")
        self.write(".planning/phases/01-foundation/links.md", "[shared](../../specs/shared.md#part)\n[code](../../../source.py)\n[internal](01-CONTEXT.md)\n[remote](https://example.test/a)\n[ref]: ../../specs/shared.md\ncanonical_refs: [.planning/phases/01-foundation/01-CONTEXT.md]\n")
        self.write(".planning/specs/reader.md", "[old](../phases/01-foundation/links.md#x)\n[ref]: ../phases/01-foundation/01-CONTEXT.md\n`.planning/phases/01-foundation/01-01-SUMMARY.md`\n")
        self.cli("planning.archive", "phase", "1", "--apply")
        links = self.read(".planning/archive/phases/01-foundation/links.md")
        self.assertIn("../../../specs/shared.md#part", links)
        self.assertIn("../../../../source.py", links)
        self.assertIn("[internal](01-CONTEXT.md)", links)
        self.assertIn("https://example.test/a", links)
        self.assertIn("[ref]: ../../../specs/shared.md", links)
        self.assertIn(".planning/archive/phases/01-foundation/01-CONTEXT.md", links)
        reader = self.read(".planning/specs/reader.md")
        self.assertIn("../archive/phases/01-foundation/links.md#x", reader)
        self.assertIn(".planning/archive/phases/01-foundation/01-01-SUMMARY.md", reader)
        self.assertEqual(self.read(".planning/archive/phases/01-foundation/nested/notes.md"), "# Notes\n[context](../01-CONTEXT.md)\n")

    def test_adr_preserves_reasoning_and_bidirectional_replacement_links(self):
        self.adr()
        before = self.snapshot()
        preview = self.cli("planning.archive", "adr", "ADR-001")
        self.assertEqual(before, self.snapshot())
        result = self.cli("planning.archive", "adr", "ADR-001", "--apply")
        self.assertEqual(preview["recovery_id"], result["recovery_id"])
        self.assertIn("Original historical reasoning.", self.read(".planning/archive/decisions/ADR-001-old.md"))
        self.assertIn(".planning/decisions/ADR-002-new.md", self.read(".planning/archive/decisions/ADR-001-old.md"))
        self.assertIn(".planning/archive/decisions/ADR-001-old.md", self.read(".planning/decisions/ADR-002-new.md"))
        self.assertEqual(self.cli("planning.archives", "--kind", "adr")["count"], 1)

    def test_accepted_adr_cannot_archive_on_status_or_age(self):
        self.adr("accepted")
        result = self.cli("planning.archive", "adr", "ADR-001", "--apply", ok=False)
        self.assertEqual(result["code"], "archive-evidence-required")

    def test_adr_missing_replacement_denied(self):
        self.adr()
        (self.root / ".planning/decisions/ADR-002-new.md").unlink()
        before = self.snapshot()
        self.cli("planning.archive", "adr", "ADR-001", "--apply", ok=False)
        self.assertEqual(before, self.snapshot())

    def test_quick_completed_and_retired_discovery_does_not_inflate_counts(self):
        for index, status in enumerate(("complete", "abandoned", "obsolete"), 1):
            name = self.quick(status, name="260101-00" + str(index) + "-small-fix")
            before = self.snapshot()
            self.cli("planning.archive", "quick", name)
            self.assertEqual(before, self.snapshot())
            self.cli("planning.archive", "quick", name, "--apply")
        listing = self.cli("quick.list")
        self.assertEqual(listing["count"], 0)
        self.assertEqual(listing["archived_count"], 3)
        self.assertEqual(len(listing["archived_tasks"]), 3)
        self.assertEqual(self.cli("planning.archives", "--kind", "quick")["count"], 3)

    def test_quick_active_and_status_only_completion_denied(self):
        for status in ("open", "in_progress", "complete", "abandoned"):
            name = self.quick(status, evidence=False)
            before = self.snapshot()
            result = self.cli("planning.archive", "quick", name, "--apply", ok=False)
            self.assertIn(result["code"], {"archive-active", "archive-evidence-required"})
            self.assertEqual(before, self.snapshot())

    def test_quick_sequence_reserves_archived_identity(self):
        from datetime import datetime
        stamp = datetime.now().strftime("%y%m%d")
        name = self.quick(name=stamp + "-001-small-fix")
        self.cli("planning.archive", "quick", name, "--apply")
        self.assertEqual(self.cli("quick.create", "Another fix")["sequence"], 2)

    def test_recovery_preview_and_apply_restore_exact_original_bytes(self):
        self.adr()
        before = self.snapshot()
        result = self.cli("planning.archive", "adr", "ADR-001", "--apply")
        archived = self.snapshot()
        preview = self.cli("planning.archive-recover", result["recovery_id"])
        self.assertTrue(preview["dry_run"])
        self.assertEqual(archived, self.snapshot())
        self.assertEqual(self.cli("planning.archive-recover", result["recovery_id"], "--apply")["state"], "recovered")
        recovered = self.snapshot()
        journals = {key: value for key, value in recovered.items() if "/recovery/" in key}
        self.assertEqual({key: value for key, value in recovered.items() if "/recovery/" not in key}, before)
        self.assertEqual(len(journals), 1)
        repeat = self.cli("planning.archive-recover", result["recovery_id"], "--apply")
        self.assertEqual(repeat["state"], "already_recovered")
        self.assertEqual(recovered, self.snapshot())

    def test_recovery_refuses_subsequent_edits_and_new_nested_files(self):
        result = self.cli("planning.archive", "phase", "1", "--apply")
        self.write(".planning/archive/phases/01-foundation/new.md", "Keep user work.\n")
        before = self.snapshot()
        denied = self.cli("planning.archive-recover", result["recovery_id"], "--apply", ok=False)
        self.assertEqual(denied["code"], "archive-recovery-conflict")
        self.assertEqual(before, self.snapshot())
        (self.root / ".planning/archive/phases/01-foundation/new.md").unlink()
        self.write(".planning/ROADMAP.md", self.read(".planning/ROADMAP.md") + "\nUser added context.\n")
        before = self.snapshot()
        self.cli("planning.archive-recover", result["recovery_id"], "--apply", ok=False)
        self.assertEqual(before, self.snapshot())

    def test_interrupted_apply_can_recover_binary_and_empty_directory(self):
        source = self.root / ".planning/phases/01-foundation"
        self.write(".planning/phases/01-foundation/links.md", "[state](../../STATE.md)\n")
        (source / "binary.dat").write_bytes(b"\x00\xff\x10")
        (source / "empty").mkdir()
        before = self.snapshot()
        workspace = Workspace(self.root)
        original_write = archive.atomic_write
        calls = []
        def interrupt(ws, path, content):
            calls.append(path)
            if len(calls) == 3:
                raise OSError("simulated write interruption")
            return original_write(ws, path, content)
        with patch.object(archive, "atomic_write", side_effect=interrupt):
            with self.assertRaises(VerbError) as error:
                archive.archive(workspace, "phase", "1", apply=True)
        self.assertEqual(error.exception.code, "archive-interrupted")
        recoveries = self.cli("planning.archives")["recoveries"]
        self.assertEqual(recoveries[0]["state"], "pending")
        self.cli("planning.archive-recover", recoveries[0]["recovery_id"], "--apply")
        recovered = self.snapshot()
        self.assertEqual({key: value for key, value in recovered.items() if "/recovery/" not in key}, before)
        self.assertTrue((source / "empty").is_dir())

    def test_selector_traversal_and_invalid_recovery_id_are_denied(self):
        for selector in ("../outside", ".planning/quick/../phases/01-foundation", ".planning/phases/01-foundation/01-01-PLAN.md"):
            before = self.snapshot()
            self.cli("planning.archive", "phase", selector, "--apply", ok=False)
            self.assertEqual(before, self.snapshot())
        self.cli("planning.archive-recover", "../outside", "--apply", ok=False)

    def test_symlink_escape_is_denied_without_touching_target(self):
        outside = Path(tempfile.mkdtemp(prefix="archive-outside-"))
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        (outside / "protected.md").write_text("Do not change.\n", encoding="utf-8")
        link = self.root / ".planning/phases/01-foundation/escape"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            if os.name != "nt":
                self.skipTest("host cannot create symlink: " + str(exc))
            result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True, text=True)
            if result.returncode:
                self.skipTest("host cannot create symlink/junction: " + result.stderr)
        result = self.cli("planning.archive", "phase", "1", "--apply", ok=False)
        self.assertEqual(result["code"], "path-escape")
        self.assertEqual((outside / "protected.md").read_text(encoding="utf-8"), "Do not change.\n")

    def test_reapply_after_recovery_preserves_journal_history(self):
        first = self.cli("planning.archive", "phase", "1", "--apply")
        self.cli("planning.archive-recover", first["recovery_id"], "--apply")
        second = self.cli("planning.archive", "phase", "1", "--apply")
        self.assertEqual(first["recovery_id"], second["recovery_id"])
        journal = json.loads(self.read(".planning/archive/recovery/" + first["recovery_id"] + ".json"))
        self.assertEqual(journal["history"], ["recovered"])
        self.cli("planning.archive-recover", first["recovery_id"], "--apply")

    def test_journal_corruption_is_denied_without_writes(self):
        result = self.cli("planning.archive", "phase", "1", "--apply")
        path = ".planning/archive/recovery/" + result["recovery_id"] + ".json"
        journal = json.loads(self.read(path))
        journal["changes"][0]["path"] = ".planning/PROJECT.md"
        self.write(path, json.dumps(journal))
        before = self.snapshot()
        self.assertEqual(self.cli("planning.archive-recover", result["recovery_id"], "--apply", ok=False)["code"], "bad-recovery-journal")
        self.assertEqual(before, self.snapshot())

    def test_new_empty_directory_blocks_recovery(self):
        result = self.cli("planning.archive", "phase", "1", "--apply")
        (self.root / ".planning/archive/phases/01-foundation/new-empty").mkdir()
        self.assertEqual(self.cli("planning.archive-recover", result["recovery_id"], "--apply", ok=False)["code"], "archive-recovery-conflict")
        self.assertTrue((self.root / ".planning/archive/phases/01-foundation/new-empty").is_dir())

    def test_summary_status_without_authored_accomplishments_is_denied(self):
        self.write(".planning/phases/01-foundation/01-01-SUMMARY.md", "---\nstatus: complete\n---\n# Summary\n")
        self.assertEqual(self.cli("planning.archive", "phase", "1", "--apply", ok=False)["code"], "archive-evidence-required")

    def test_existing_archive_catalog_links_follow_later_adr_move(self):
        self.adr()
        self.cli("planning.archive", "adr", "ADR-001", "--apply")
        self.write(".planning/decisions/ADR-002-new.md", "---\nstatus: superseded\nsuperseded_by: [ADR-003-third]\n---\n# Second decision\n")
        self.write(".planning/decisions/ADR-003-third.md", "---\nstatus: accepted\n---\n# Third decision\n")
        self.cli("planning.archive", "adr", "ADR-002", "--apply")
        entries = self.cli("planning.archives")["entries"]
        first = next(entry for entry in entries if entry["id"] == "ADR-001-old")
        self.assertEqual(first["replacement"], ".planning/archive/decisions/ADR-002-new.md")
        self.assertIn(".planning/archive/decisions/ADR-002-new.md", self.read(".planning/archive/decisions/ADR-001-old.md"))
        self.assertNotIn("](../decisions/ADR-002-new.md)", self.read(".planning/archive/INDEX.md"))

    def test_completed_milestone_preserves_archived_membership_and_accomplishments(self):
        roadmap = ROADMAP.replace("## Phases", "## Milestones\n\n- ?? **v1.0 First release** - in progress\n\n## Phases")
        roadmap = roadmap.replace("### Phase 1: Foundation", "### v1.0 First release (In Progress)\n\n#### Phase 1: Foundation")
        roadmap = roadmap.replace("### Phase 2: Feature", "### v2.0 Next release (Planned)\n\n#### Phase 2: Feature")
        self.write(".planning/ROADMAP.md", roadmap)
        self.cli("planning.archive", "phase", "1", "--apply")
        readiness = self.cli("init.complete-milestone", "v1.0")
        self.assertTrue(readiness["ready_to_complete"])
        self.assertEqual(readiness["milestone_phases"][0]["number"], "1")
        self.assertTrue(readiness["milestone_phases"][0]["archived"])
        complete = self.cli("milestone.complete", "v1.0", "--confirm")
        self.assertEqual(complete["phases"], ["1"])
        self.assertTrue(complete["accomplishments"])
        self.assertIn("1 (1 plans total)", self.read(".planning/MILESTONES.md"))

    def test_authored_markdown_evidence_links_are_accepted(self):
        self.write(".planning/phases/01-foundation/01-01-SUMMARY.md", "---\nstatus: complete\n---\n# Summary\n\n## Accomplishments\n\nBuilt foundation; [verification](01-VERIFICATION.md) proves the outcome.\n")
        self.assertEqual(self.cli("planning.archive", "phase", "1", "--apply")["state"], "archived")

    def test_pending_journal_blocks_additional_archive_operations(self):
        task = self.quick()
        workspace = Workspace(self.root)
        original_write = archive.atomic_write
        calls = []
        def interrupt(ws, path, content):
            calls.append(path)
            if len(calls) == 2:
                raise OSError("simulated interruption")
            return original_write(ws, path, content)
        with patch.object(archive, "atomic_write", side_effect=interrupt):
            with self.assertRaises(VerbError):
                archive.archive(workspace, "phase", "1", apply=True)
        before = self.snapshot()
        self.assertEqual(self.cli("planning.archive", "quick", task, "--apply", ok=False)["code"], "archive-pending")
        self.assertEqual(before, self.snapshot())

    def test_legacy_archived_phase_satisfies_dependency(self):
        self.write(".planning/phases/08-legacy/notes.md", "# Recorded historical release\n")
        self.write(".planning/legacy.md", "---\narchive_kind: phase\narchive_id: 08-legacy\narchive_status: complete\narchive_reason: User confirmed completed legacy migration from recorded release.\n---\n")
        self.write(".planning/ROADMAP.md", ROADMAP.replace("**Depends on**: Phase 1", "**Depends on**: Phase 8"))
        self.cli("planning.archive", "phase", "8", "--evidence", ".planning/legacy.md", "--apply")
        self.assertEqual(self.cli("roadmap.analyze")["blocked"], [])

    def phase_legacy_evidence(self):
        self.write(".planning/legacy.md", "---\narchive_kind: phase\narchive_id: 01-foundation\narchive_status: complete\narchive_reason: User confirmed completed work from recorded release.\n---\n")
        return ".planning/legacy.md"

    def assert_archive_denied_without_writes(self, *args):
        before = self.snapshot()
        for flag in ((), ("--apply",)):
            result = self.cli("planning.archive", *args, *flag, ok=False)
            self.assertIn(result["code"], {"archive-active", "archive-evidence-required"})
            self.assertEqual(before, self.snapshot())

    def test_noncanonical_plan_case_blocks_archive_with_and_without_legacy_evidence(self):
        self.write(".planning/phases/01-foundation/01-02-PLAN.MD", "# Unfinished extra plan\n")
        evidence = self.phase_legacy_evidence()
        self.assert_archive_denied_without_writes("phase", "1")
        self.assert_archive_denied_without_writes("phase", "1", "--evidence", evidence)
        self.assertEqual(self.cli("phases.list")["count"], 2)
        self.assertTrue((self.root / ".planning/phases/01-foundation/01-02-PLAN.MD").is_file())

    def test_unregistered_plan_file_blocks_archive_even_with_legacy_evidence(self):
        self.write(".planning/phases/01-foundation/01-02-PLAN.md", "# Pending extra work\n")
        evidence = self.phase_legacy_evidence()
        self.assert_archive_denied_without_writes("phase", "1")
        self.assert_archive_denied_without_writes("phase", "1", "--evidence", evidence)
        self.assertEqual(self.cli("phases.list")["count"], 2)
        self.assertTrue((self.root / ".planning/phases/01-foundation/01-02-PLAN.md").is_file())

    def test_even_completed_unregistered_plan_requires_roadmap_reconciliation(self):
        self.write(".planning/phases/01-foundation/01-02-PLAN.md", "# Extra work\n")
        self.write(".planning/phases/01-foundation/01-02-SUMMARY.md", "---\nstatus: complete\n---\n## Accomplishments\n\nDelivered the extra work.\n")
        self.assert_archive_denied_without_writes("phase", "1", "--evidence", self.phase_legacy_evidence())

    def test_registered_missing_plan_file_blocks_archive_even_with_legacy_evidence(self):
        (self.root / ".planning/phases/01-foundation/01-01-PLAN.md").unlink()
        self.assert_archive_denied_without_writes("phase", "1", "--evidence", self.phase_legacy_evidence())

    def test_unsummarized_plan_blocks_legacy_archive(self):
        (self.root / ".planning/phases/01-foundation/01-01-SUMMARY.md").unlink()
        self.assert_archive_denied_without_writes("phase", "1", "--evidence", self.phase_legacy_evidence())

    def test_affirmatively_incomplete_plan_and_summary_block_legacy_archive(self):
        evidence = self.phase_legacy_evidence()
        plan = ".planning/phases/01-foundation/01-01-PLAN.md"
        summary = ".planning/phases/01-foundation/01-01-SUMMARY.md"
        for status in ("in_progress", "blocked", "halted", "open"):
            with self.subTest(artifact="plan", status=status):
                self.write(plan, "---\nstatus: " + status + "\n---\n# Unfinished plan\n")
                self.assert_archive_denied_without_writes("phase", "1", "--evidence", evidence)
            self.write(plan, "# Plan\n")
            with self.subTest(artifact="summary", status=status):
                self.write(summary, "---\nstatus: " + status + "\n---\n## Accomplishments\n\nPartial implementation.\n")
                self.assert_archive_denied_without_writes("phase", "1", "--evidence", evidence)
            self.write(summary, "---\nstatus: complete\n---\n## Accomplishments\n\nBuilt foundation.\n")

    def test_nested_plan_cannot_escape_phase_inventory(self):
        self.write(".planning/phases/01-foundation/nested/01-02-PLAN.md", "# Unfinished nested work\n")
        self.assert_archive_denied_without_writes("phase", "1", "--evidence", self.phase_legacy_evidence())

    def test_repeated_adr_alias_preview_and_apply_are_noops(self):
        self.adr()
        first = self.cli("planning.archive", "adr", "ADR-001", "--apply")
        before = self.snapshot()
        for selector in ("1", "001", "ADR-001", "adr-1", "ADR-001-old", "ADR-001-old.md", ".planning/decisions/ADR-001-old.md"):
            for flag in ((), ("--apply",)):
                with self.subTest(selector=selector, apply=bool(flag)):
                    result = self.cli("planning.archive", "adr", selector, *flag)
                    self.assertEqual(result["state"], "already_archived")
                    self.assertEqual(result["recovery_id"], first["recovery_id"])
                    self.assertEqual(before, self.snapshot())

    def test_archived_adr_alias_collision_with_active_record_is_denied(self):
        self.adr()
        self.cli("planning.archive", "adr", "1", "--apply")
        self.write(".planning/decisions/ADR-001-another.md", "---\nstatus: accepted\n---\n# New record reusing identity\n")
        before = self.snapshot()
        for selector in ("1", "ADR-001"):
            self.assertEqual(self.cli("planning.archive", "adr", selector, "--apply", ok=False)["code"], "archive-collision")
            self.assertEqual(before, self.snapshot())

    def test_ambiguous_archived_adr_number_is_denied(self):
        self.adr()
        self.cli("planning.archive", "adr", "ADR-001-old", "--apply")
        self.write(".planning/decisions/ADR-001-another.md", "---\nstatus: superseded\nsuperseded_by: [ADR-002-new]\n---\n# Separate historic record\n")
        self.cli("planning.archive", "adr", "ADR-001-another", "--apply")
        before = self.snapshot()
        self.assertEqual(self.cli("planning.archive", "adr", "ADR-001", "--apply", ok=False)["code"], "archive-ambiguous")
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.cli("planning.archive", "adr", "ADR-001-old")["state"], "already_archived")

    @unittest.skipUnless(os.name == "nt", "Windows junction compatibility scenario")
    def test_internal_junction_denied_without_path_is_junction_api(self):
        self.write(".planning/shared/protected.md", "Keep internal target.\n")
        target = self.root / ".planning/shared"
        link = self.root / ".planning/phases/01-foundation/junction"
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        before = self.snapshot()
        def unavailable(_):
            raise AttributeError("Path.is_junction is unavailable in Python 3.11")
        with patch.object(type(link), "is_junction", property(unavailable), create=True):
            for path in (link, link / "protected.md"):
                with self.assertRaises(VerbError) as error:
                    archive.guarded(Workspace(self.root), path)
                self.assertEqual(error.exception.code, "path-escape")
            for apply in (False, True):
                with self.assertRaises(VerbError) as error:
                    archive.archive(Workspace(self.root), "phase", "1", apply=apply)
                self.assertEqual(error.exception.code, "path-escape")
        self.assertEqual(before, self.snapshot())
        self.assertEqual((target / "protected.md").read_text(encoding="utf-8"), "Keep internal target.\n")

    def test_completion_value_does_not_require_timestamp_format(self):
        name = self.quick()
        path = ".planning/quick/" + name + "/QUICK.md"
        self.write(path, self.read(path).replace("completed: '2026-01-02'", "completed: recorded release confirmation"))
        self.assertEqual(self.cli("planning.archive", "quick", name, "--apply")["state"], "archived")

    def test_archived_phase_mutation_requires_recovery(self):
        self.cli("planning.archive", "phase", "1", "--apply")
        before = self.snapshot()
        self.assertEqual(self.cli("phase.complete", "1", ok=False)["code"], "phase-archived")
        self.assertEqual(self.cli("phase.remove", "1", "--force", ok=False)["code"], "phase-archived")
        self.assertEqual(self.cli("roadmap.update-plan-progress", "01-01", "--undo", ok=False)["code"], "phase-archived")
        self.assertEqual(self.cli("state.begin-phase", "1", ok=False)["code"], "phase-archived")
        self.assertEqual(before, self.snapshot())


if __name__ == "__main__":
    unittest.main()
