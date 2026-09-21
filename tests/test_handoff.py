"""Behavioral tests for handoff records, driven through the runtime verbs.

The hook that writes handoffs is covered by `.ai/hooks/context-handoff.test.sh`.
This suite covers the other half: what the orchestrator can do with a record
once it exists -- resolve the limit, list what is pending, read a continuation
brief, and consume a record so no second agent picks up the same work.
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

CONFIG = """commit_docs: true
context_window: 200000
handoff:
  context_percent: 60
  context_tokens: 250000
verification:
  commands: []
"""


class HandoffCase(unittest.TestCase):
    """A real repository carrying real handoff records."""

    def setUp(self):
        self.directory = Path(tempfile.mkdtemp(prefix="handoff-"))
        self.addCleanup(shutil.rmtree, self.directory, ignore_errors=True)
        subprocess.run(["git", "init", "-q", "."], cwd=str(self.directory),
                       capture_output=True, text=True, check=False)
        planning = self.directory / ".planning"
        planning.mkdir()
        (planning / "config.yaml").write_text(CONFIG, encoding="utf-8", newline="\n")
        self.handoffs = planning / "handoffs"
        self.handoffs.mkdir()

    def run_verb(self, *args, expect_ok=True):
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

    def put(self, name, **fields):
        record = {"schema": 1, "status": "pending", "reason": "context-threshold"}
        record.update(fields)
        path = self.handoffs / (name + ".json")
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
        return path

    def set_config(self, text):
        (self.directory / ".planning" / "config.yaml").write_text(
            text, encoding="utf-8", newline="\n")


class Limits(HandoffCase):

    def test_percentage_binds_on_a_small_window(self):
        """60% of 200k is 120k, well under the 250k ceiling."""
        payload = self.run_verb("handoff.limits")
        self.assertEqual(120000, payload["threshold_tokens"])
        self.assertEqual("percent", payload["binding"])

    def test_ceiling_binds_on_a_large_window(self):
        """60% of a million would be 600k -- far past where a plan should still
        be accumulating context, which is the whole reason for the ceiling."""
        self.set_config("context_window: 1000000\n"
                        "handoff:\n  context_percent: 60\n  context_tokens: 250000\n")
        payload = self.run_verb("handoff.limits")
        self.assertEqual(250000, payload["threshold_tokens"])
        self.assertEqual("ceiling", payload["binding"])

    def test_defaults_apply_when_the_keys_are_absent(self):
        self.set_config("commit_docs: true\n")
        payload = self.run_verb("handoff.limits")
        self.assertEqual(60, payload["context_percent"])
        self.assertEqual(250000, payload["context_tokens"])
        self.assertEqual(120000, payload["threshold_tokens"])

    def test_a_project_can_lower_the_fire_point(self):
        self.set_config("context_window: 200000\n"
                        "handoff:\n  context_percent: 40\n  context_tokens: 250000\n")
        self.assertEqual(80000, self.run_verb("handoff.limits")["threshold_tokens"])


class Listing(HandoffCase):

    def test_an_empty_directory_lists_nothing(self):
        payload = self.run_verb("handoff.list")
        self.assertEqual(0, payload["count"])
        self.assertEqual([], payload["handoffs"])

    def test_records_are_listed_oldest_first(self):
        self.put("second", created_at="2026-09-21T12:00:00Z")
        self.put("first", created_at="2026-09-21T09:00:00Z")
        payload = self.run_verb("handoff.list")
        self.assertEqual(["first", "second"], [item["id"] for item in payload["handoffs"]])

    def test_hook_bookkeeping_is_not_a_handoff(self):
        """The debounce sentinel and the active-agent stack share the directory
        but are not records the orchestrator should ever dispatch against."""
        self.put("real", created_at="2026-09-21T09:00:00Z")
        (self.handoffs / ".state-abc.json").write_text('{"calls": 2}\n', encoding="utf-8")
        (self.handoffs / ".active-abc.jsonl").write_text('{"agent": "coder"}\n', encoding="utf-8")
        payload = self.run_verb("handoff.list")
        self.assertEqual(["real"], [item["id"] for item in payload["handoffs"]])

    def test_one_corrupt_record_does_not_hide_the_others(self):
        """A killed process can leave a fragment. Losing every other pending
        handoff to it would turn one interrupted agent into all of them."""
        self.put("good", created_at="2026-09-21T09:00:00Z")
        (self.handoffs / "broken.json").write_text("{not json", encoding="utf-8")
        payload = self.run_verb("handoff.list")
        self.assertEqual(["good"], [item["id"] for item in payload["handoffs"]])


class Reading(HandoffCase):

    def test_a_brief_tells_the_next_agent_not_to_restart(self):
        self.put("sess--03-01", reason="incomplete-exit", agent="coder",
                 plan=".planning/phases/03-x/03-01-PLAN.md",
                 summary=".planning/phases/03-x/03-01-SUMMARY.md",
                 branch="phase-03", head="abc1234", dirty=" M src/thing.py")
        brief = self.run_verb("handoff.read", "sess--03-01")["continuation"]
        self.assertIn("Do not restart the plan", brief)
        self.assertIn("03-01-PLAN.md", brief)
        self.assertIn("03-01-SUMMARY.md", brief)
        self.assertIn("abc1234", brief)
        self.assertIn("src/thing.py", brief)
        self.assertIn("incomplete-exit", brief)

    def test_reading_does_not_consume(self):
        """Inspection is not dispatch. A read that deleted the record would lose
        the work whenever the orchestrator merely looked before deciding."""
        path = self.put("keep")
        self.run_verb("handoff.read", "keep")
        self.assertTrue(path.is_file())

    def test_a_json_suffix_is_accepted(self):
        self.put("suffixed")
        self.assertEqual("suffixed", self.run_verb("handoff.read", "suffixed.json")["id"])

    def test_an_unknown_id_fails_rather_than_inventing_one(self):
        payload = self.run_verb("handoff.read", "absent", expect_ok=False)
        self.assertEqual("no-handoff", payload["code"])

    def test_a_traversing_id_is_refused(self):
        outside = self.directory / "secret.json"
        outside.write_text('{"reason": "x"}\n', encoding="utf-8")
        for identifier in ("../secret", "..\\secret", "sub/secret", ".state-abc"):
            with self.subTest(identifier=identifier):
                payload = self.run_verb("handoff.read", identifier, expect_ok=False)
                self.assertEqual("bad-handoff-id", payload["code"])


class Consuming(HandoffCase):

    def test_consuming_deletes_the_record(self):
        """Consumption is a delete, not a status flip: a record left on disk
        after its work is reassigned invites a second agent onto the same plan."""
        path = self.put("done", plan=".planning/phases/03-x/03-01-PLAN.md")
        payload = self.run_verb("handoff.consume", "done")
        self.assertEqual("done", payload["consumed"])
        self.assertEqual(".planning/phases/03-x/03-01-PLAN.md", payload["plan"])
        self.assertFalse(path.is_file())
        self.assertEqual(0, self.run_verb("handoff.list")["count"])

    def test_consuming_twice_fails(self):
        self.put("once")
        self.run_verb("handoff.consume", "once")
        self.assertEqual("no-handoff",
                         self.run_verb("handoff.consume", "once", expect_ok=False)["code"])

    def test_consuming_one_leaves_the_others(self):
        self.put("a", created_at="2026-09-21T09:00:00Z")
        self.put("b", created_at="2026-09-21T10:00:00Z")
        self.run_verb("handoff.consume", "a")
        self.assertEqual(["b"], [item["id"] for item in self.run_verb("handoff.list")["handoffs"]])

    def test_a_traversing_id_deletes_nothing(self):
        outside = self.directory / "victim.json"
        outside.write_text("{}\n", encoding="utf-8")
        self.run_verb("handoff.consume", "../victim", expect_ok=False)
        self.assertTrue(outside.is_file())


class Writing(HandoffCase):

    def test_an_agent_can_record_its_own_stop(self):
        payload = self.run_verb(
            "handoff.write", "sess--04-01",
            "--reason", "turn limit reached",
            "--agent", "coder",
            "--plan", ".planning/phases/04-y/04-01-PLAN.md",
            "--remaining", "task-2", "task-3")
        self.assertEqual("pending", payload["status"])
        self.assertEqual(["task-2", "task-3"], payload["remaining"])
        # The SUMMARY path is derived rather than asked for: it is always the
        # plan's sibling, and one fewer field is one fewer field to get wrong.
        self.assertEqual(".planning/phases/04-y/04-01-SUMMARY.md", payload["summary"])
        self.assertEqual(1, self.run_verb("handoff.list")["count"])

    def test_a_reason_is_required(self):
        payload = self.run_verb("handoff.write", "sess--04-02", expect_ok=False)
        self.assertEqual("missing-reason", payload["code"])

    def test_rewriting_preserves_when_the_attempt_first_stopped(self):
        """created_at orders the queue. Refreshing a record must not reorder it."""
        first = self.run_verb("handoff.write", "sess--04-03", "--reason", "context")
        again = self.run_verb("handoff.write", "sess--04-03", "--reason", "context again")
        self.assertEqual(first["created_at"], again["created_at"])
        self.assertEqual("context again", again["reason"])
        self.assertEqual(1, self.run_verb("handoff.list")["count"])

    def test_a_written_record_reads_back_with_a_brief(self):
        self.run_verb("handoff.write", "sess--04-04", "--reason", "blocked on review",
                      "--plan", ".planning/phases/04-y/04-04-PLAN.md")
        brief = self.run_verb("handoff.read", "sess--04-04")["continuation"]
        self.assertIn("blocked on review", brief)
        self.assertIn("04-04-PLAN.md", brief)

    def test_a_traversing_id_is_refused(self):
        payload = self.run_verb("handoff.write", "../escape", "--reason", "x",
                                expect_ok=False)
        self.assertEqual("bad-handoff-id", payload["code"])
        self.assertFalse((self.directory / ".planning" / "escape.json").exists())


class Gitignored(unittest.TestCase):
    """The handoff directory must never reach a commit."""

    def test_the_repository_ignores_handoff_records(self):
        probe = ".planning/handoffs/some-session.json"
        completed = subprocess.run(["git", "check-ignore", "-q", probe],
                                   cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(0, completed.returncode,
                         f"{probe} is not gitignored: handoffs name local worktree "
                         "paths and dirty files that mean nothing in another checkout")


if __name__ == "__main__":
    unittest.main()
