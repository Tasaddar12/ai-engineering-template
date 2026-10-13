"""Offline phase declaration and publication boundary tests."""
import json
import unittest
from pathlib import Path
import yaml
import test_todo_issues as fixtures

class PhaseIssues(unittest.TestCase):
    setUp = fixtures.TodoIssues.setUp
    git = fixtures.TodoIssues.git
    save = fixtures.TodoIssues.save
    remote = fixtures.TodoIssues.remote
    run_verb = fixtures.TodoIssues.run_verb
    issue = fixtures.TodoIssues.issue

    def phase(self, entries=None, declaration=True, status="complete"):
        directory = self.directory / ".planning/phases/01-fixture"
        directory.mkdir(parents=True, exist_ok=True)
        self.record = directory / "01-01-SUMMARY.md"
        self.name = self.record.relative_to(self.directory).as_posix()
        (self.directory / ".planning/ROADMAP.md").write_text("# Roadmap\n\n## Phases\n\n- [ ] **Phase 1: Fixture** - Test\n\n## Phase Details\n\n### Phase 1: Fixture\n**Goal**: Test\n**Plans**: 1 plan\n\nPlans:\n- [ ] 01-01: Test\n", encoding="utf-8")
        self.write_record(entries, declaration, status)

    def write_record(self, entries=None, declaration=True, status="complete"):
        metadata = {"status": status}
        if declaration:
            metadata["issue_refs"] = entries if entries is not None else []
        self.record.write_text("---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\nPrivate phase evidence\n", encoding="utf-8")

    def entry(self, **changes):
        return dict({"id": "P1", "summary": "Private problem", "variant": "Bug", "state": "unresolved", "relationship": "followup"}, **changes)

    def test_reviewed_empty_handoff_and_complete(self):
        self.phase()
        self.assertTrue(self.run_verb("phase.handoff", "1")["ready"])
        self.run_verb("phase.complete", "1")

    def test_missing_declaration_blocks_before_roadmap_write(self):
        self.phase(declaration=False)
        roadmap = self.directory / ".planning/ROADMAP.md"
        before = roadmap.read_bytes()
        self.assertEqual(self.run_verb("phase.complete", "1", ok=False)["code"], "phase-issues")
        self.assertEqual(roadmap.read_bytes(), before)

    def test_unlinked_halted_problem_cannot_handoff(self):
        self.phase([self.entry()], status="halted")
        self.assertEqual(self.run_verb("phase.handoff", "1", ok=False)["code"], "phase-issues")

if __name__ == "__main__":
    unittest.main()
