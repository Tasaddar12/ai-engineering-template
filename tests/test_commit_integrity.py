"""Prospective bytes and exact index isolation through the public Engineer CLI.

These regressions exercise real disposable repositories. Checks remain deferred
until the user-authorized final verification batch.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_engineer_runtime import RuntimeCase, RUNTIME


PLAN = """---
phase: 01-foundation
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified: []
files_deleted: []
resources: []
autonomous: true
requirements: [REQ-01]
acceptance: []
documentation: []
checks: []
issue_refs: []
must_haves: {truths: [], artifacts: [], key_links: []}
---
# Prospective record
"""
RECORD = ".planning/phases/01-foundation/01-01-PLAN.md"
INVALID = PLAN.replace("issue_refs: []\n", "")


class ProspectiveCommitIntegrity(RuntimeCase):
    def invoke(self, *args, environment=None):
        process = subprocess.run([sys.executable, "-I", str(RUNTIME), "query", *args],
                                 cwd=self.root, env=environment or self.env,
                                 capture_output=True, text=True)
        self.assertNotIn("Traceback", process.stderr)
        stream = process.stdout or process.stderr
        # Existing-schema diagnostics may precede the command's JSON diagnostic.
        packet = json.loads(stream) if process.stdout else json.loads(stream.strip().splitlines()[-1])
        return process, packet

    def index(self):
        return (self.root/".git/index").read_bytes()

    def test_rejected_worktree_bytes_preserve_previous_index_and_head(self):
        self.put(RECORD, PLAN)
        self.git("add", "--", RECORD)
        self.put(RECORD, INVALID)
        original, head = self.index(), self.git("rev-parse", "HEAD")
        process, packet = self.invoke("commit", "reject malformed record", "--files", RECORD)
        self.assertEqual(1, process.returncode, packet)
        self.assertEqual("planning-integrity", packet["error"])
        self.assertIn("issue_refs", str(packet))
        self.assertEqual(original, self.index())
        self.assertEqual(head, self.git("rev-parse", "HEAD"))

    def test_invalid_staged_record_cannot_hide_behind_valid_worktree_bytes(self):
        self.put(RECORD, INVALID)
        self.git("add", "--", RECORD)
        self.put(RECORD, PLAN)
        self.put("source.txt", "new source\n")
        original = self.index()
        process, packet = self.invoke("commit", "inspect staged record", "--files", "source.txt")
        self.assertEqual(1, process.returncode, packet)
        self.assertEqual("planning-integrity", packet["error"])
        self.assertEqual(original, self.index())

    def test_success_commits_only_owned_paths_and_retains_unrelated_staged_blob(self):
        self.put(RECORD, PLAN)
        self.put("unrelated.txt", "staged contents\n")
        self.git("add", "--", "unrelated.txt")
        self.put("unrelated.txt", "working contents\n")
        blob = self.git("rev-parse", ":unrelated.txt")
        process, packet = self.invoke("commit", "commit valid record", "--files", RECORD)
        self.assertEqual(0, process.returncode, packet)
        self.assertTrue(packet["committed"])
        self.assertEqual([RECORD], self.git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines())
        self.assertEqual(blob, self.git("rev-parse", ":unrelated.txt"))
        self.assertEqual("working contents\n", (self.root/"unrelated.txt").read_text())

    def test_unchanged_historical_malformed_record_does_not_block_source_commit(self):
        self.put(RECORD, "# Historical record without metadata\n")
        self.git("add", "--", RECORD)
        self.git("commit", "-m", "historical fixture")
        self.put("source.txt", "new source\n")
        process, packet = self.invoke("commit", "source maintenance", "--files", "source.txt")
        self.assertEqual(0, process.returncode, packet)
        self.assertTrue(packet["committed"])

    def test_staged_record_deletion_is_allowed_without_parsing_empty_bytes(self):
        self.put(RECORD, PLAN)
        self.git("add", "--", RECORD)
        self.git("commit", "-m", "record fixture")
        (self.root/RECORD).unlink()
        process, packet = self.invoke("commit", "remove record", "--files-removed", RECORD)
        self.assertEqual(0, process.returncode, packet)
        self.assertEqual("D\t"+RECORD, self.git("diff-tree", "--no-commit-id", "--name-status", "-r", "HEAD"))

    def test_clean_filter_is_refused_before_index_mutation(self):
        self.put(RECORD, PLAN)
        self.git("add", "--", RECORD)
        self.put(".gitattributes", "*.md filter=external\n")
        original = self.index()
        process, packet = self.invoke("commit", "filtered record", "--files", RECORD)
        self.assertEqual(1, process.returncode, packet)
        self.assertIn("clean filter", packet["message"])
        self.assertEqual(original, self.index())

    def test_snapshot_root_never_falls_back_to_live_worktree_or_index(self):
        self.put(RECORD, INVALID)
        self.git("add", "--", RECORD)
        original = self.index()
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory)
            selected = snapshot/RECORD
            selected.parent.mkdir(parents=True)
            selected.write_text(PLAN, encoding="utf-8")
            env = {**self.env, "ENGINEER_ROOT": str(snapshot)}
            process, packet = self.invoke("planning.integrity", "--files", RECORD, environment=env)
            self.assertEqual(0, process.returncode, packet)
            self.assertTrue(packet["valid"])
            selected.write_text(INVALID, encoding="utf-8")
            self.put(RECORD, PLAN)
            process, packet = self.invoke("planning.integrity", "--files", RECORD, environment=env)
            self.assertEqual(1, process.returncode, packet)
            self.assertIn("issue_refs", str(packet))
        self.assertEqual(original, self.index())

    def test_schema_gate_is_independent_of_consistency_diagnostics(self):
        self.put(RECORD, PLAN)
        self.assertTrue(self.cli("planning.integrity", "--files", RECORD)["valid"])
        result = self.cli("planning.validate")
        self.assertFalse(result["valid"])
        self.assertTrue(result["warnings"])
        process = subprocess.run([sys.executable, "-I", str(RUNTIME), "query", "planning.validate", "--strict"],
                                 cwd=self.root, env=self.env, capture_output=True, text=True)
        self.assertEqual(1, process.returncode)
        self.assertTrue(json.loads(process.stdout)["errors"])

    def test_boolean_wave_duplicate_keys_and_unaccepted_human_closure_fail(self):
        variants = [PLAN.replace("wave: 1", "wave: true"),
                    PLAN.replace("wave: 1", "wave: -1"),
                    PLAN.replace("wave: 1", "wave: -1\nwave: 1"),
                    PLAN.replace("issue_refs: []", "requirements-completed: 7\nissue_refs: []"),
                    PLAN.replace("issue_refs: []", "issue_refs: [{id: uat-1, state: pending-human, relationship: resolving}]")]
        for content in variants:
            with self.subTest(content=content):
                self.put(RECORD, content)
                process = subprocess.run([sys.executable, "-I", str(RUNTIME), "query", "planning.integrity", "--files", RECORD],
                                         cwd=self.root, env=self.env, capture_output=True, text=True)
                self.assertEqual(1, process.returncode, process.stdout+process.stderr)
                self.assertFalse(json.loads(process.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()
