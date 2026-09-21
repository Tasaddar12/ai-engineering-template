"""Behavioral tests for session worktrees and pull-request delivery.

Session tests drive `phase.py` as a subprocess against real temporary
repositories, the same way a workflow does. They deliberately do not require
`gh`: a repository with no GitHub remote makes `gh pr view` fail, the delivery
layer treats that as "no pull request", and session bookkeeping falls back to
git ancestry. That fallback is itself part of the contract, so exercising it
here is not a compromise.

The check classifier is tested directly because it is a pure function over the
JSON `gh` emits, and pinning its verdicts is the only way to be sure a merge
never happens on an unfinished or absent result.
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

sys.path.insert(0, str(ROOT / ".ai" / "runtime"))
from lib import delivery  # noqa: E402

CONFIG = """commit_docs: true
worktree:
  root: .worktrees
verification:
  commands: []
"""


class SessionCase(unittest.TestCase):
    """A real git repository whose worktree root is ignored."""

    def setUp(self):
        self.directory = Path(tempfile.mkdtemp(prefix="phase-session-"))
        self.addCleanup(self.cleanup)
        self.git("init", "-q", ".")
        self.git("config", "user.email", "session@example.test")
        self.git("config", "user.name", "Session Test")
        planning = self.directory / ".planning"
        planning.mkdir()
        (planning / "config.yaml").write_text(CONFIG, encoding="utf-8", newline="\n")
        (self.directory / ".gitignore").write_text(".worktrees/\n", encoding="utf-8",
                                                   newline="\n")
        (self.directory / "README.md").write_text("# Session\n", encoding="utf-8",
                                                  newline="\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "initial")
        self.base = self.git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()

    def cleanup(self):
        # Worktrees hold file handles on Windows; prune before removing the tree.
        self.git("worktree", "prune")
        shutil.rmtree(self.directory, ignore_errors=True)

    def git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=str(cwd or self.directory),
                              capture_output=True, text=True, check=False)

    def run_verb(self, *args, expect_ok=True, cwd=None):
        environment = dict(os.environ, PYTHONIOENCODING="utf-8")
        completed = subprocess.run([sys.executable, str(RUNTIME), "query", *args],
                                   cwd=str(cwd or self.directory),
                                   capture_output=True, text=True,
                                   encoding="utf-8", env=environment)
        self.assertNotIn("Traceback", completed.stderr,
                         "verb raised instead of returning a result: "
                         + completed.stderr)
        payload = json.loads(completed.stdout)
        if expect_ok:
            self.assertTrue(payload.get("ok"), "verb failed: " + completed.stdout)
        else:
            self.assertFalse(payload.get("ok"), "verb unexpectedly succeeded")
        return payload


class SessionLifecycle(SessionCase):
    def test_open_creates_a_worktree_on_its_own_branch(self):
        result = self.run_verb("session.open", "phase", "01")
        self.assertEqual(result["kind"], "phase")
        self.assertEqual(result["label"], "01")
        self.assertFalse(result["reused"])
        self.assertTrue(result["branch"].startswith("phase-01-"))
        self.assertTrue(Path(result["worktree"]).is_dir())
        listed = self.git("worktree", "list", "--porcelain").stdout
        self.assertIn(result["branch"], listed)

    def test_worktree_is_an_immediate_child_of_the_configured_root(self):
        result = self.run_verb("session.open", "quick", "fix-login")
        path = Path(result["worktree"])
        self.assertEqual(path.parent.name, ".worktrees")
        self.assertEqual(path.parent.parent, self.directory.resolve())

    def test_reopening_the_same_unit_returns_the_same_session(self):
        first = self.run_verb("session.open", "phase", "01")
        second = self.run_verb("session.open", "phase", "01")
        self.assertTrue(second["reused"])
        self.assertEqual(first["branch"], second["branch"])
        self.assertEqual(first["worktree"], second["worktree"])

    def test_a_different_unit_gets_its_own_session(self):
        first = self.run_verb("session.open", "phase", "01")
        second = self.run_verb("session.open", "phase", "02")
        self.assertNotEqual(first["branch"], second["branch"])
        self.assertNotEqual(first["worktree"], second["worktree"])

    def test_status_reports_open_sessions(self):
        self.run_verb("session.open", "phase", "01")
        self.run_verb("session.open", "quick", "typo")
        status = self.run_verb("session.status")
        self.assertEqual(status["open_count"], 2)
        self.assertTrue(all(item["exists"] for item in status["open"]))

    def test_unknown_kind_is_refused(self):
        failed = self.run_verb("session.open", "hotfix", "01", expect_ok=False)
        self.assertEqual(failed["code"], "bad-session-kind")

    def test_open_refuses_when_the_worktree_root_is_not_ignored(self):
        (self.directory / ".gitignore").write_text("", encoding="utf-8", newline="\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "stop ignoring worktrees")
        failed = self.run_verb("session.open", "phase", "01", expect_ok=False)
        self.assertEqual(failed["code"], "root-not-ignored")


class SessionClose(SessionCase):
    def open_and_commit(self, kind="phase", label="01"):
        """Open a session and put one real commit on its branch."""
        session = self.run_verb("session.open", kind, label)
        worktree = Path(session["worktree"])
        (worktree / "feature.txt").write_text("work\n", encoding="utf-8", newline="\n")
        self.git("add", "-A", cwd=worktree)
        self.git("commit", "-qm", "do the work", cwd=worktree)
        return session

    def test_close_preserves_a_session_whose_work_never_merged(self):
        session = self.open_and_commit()
        result = self.run_verb("session.close", session["branch"])
        self.assertFalse(result["closed"])
        self.assertTrue(result["preserved"])
        self.assertTrue(Path(session["worktree"]).is_dir())
        self.assertFalse(result["evidence"]["merged"])

    def test_close_removes_a_session_whose_work_reached_the_base(self):
        session = self.open_and_commit()
        merged = self.git("merge", "--no-ff", "-m", "integrate", session["branch"])
        self.assertEqual(merged.returncode, 0, merged.stderr)
        result = self.run_verb("session.close", session["branch"])
        self.assertTrue(result["closed"], result)
        self.assertEqual(result["evidence"]["evidence"], "ancestry")
        self.assertFalse(Path(session["worktree"]).exists())
        branches = self.git("branch", "--list", session["branch"]).stdout.strip()
        self.assertEqual(branches, "")

    def test_closing_an_unknown_branch_is_an_expected_failure(self):
        failed = self.run_verb("session.close", "phase-nope-000000000",
                               expect_ok=False)
        self.assertEqual(failed["code"], "no-session")

    def test_force_closes_unmerged_work_when_explicitly_asked(self):
        session = self.open_and_commit()
        result = self.run_verb("session.close", session["branch"], "--force")
        self.assertTrue(result["closed"])
        self.assertTrue(result["forced"])


class CheckClassification(unittest.TestCase):
    """The verdict that decides whether a merge may happen at all."""

    def test_no_checks_is_not_a_pass(self):
        verdict = delivery.classify_checks([])
        self.assertEqual(verdict["state"], "none")
        self.assertEqual(verdict["total"], 0)

    def test_all_successful_checks_pass(self):
        verdict = delivery.classify_checks([
            {"name": "validate", "status": "COMPLETED", "conclusion": "SUCCESS"},
            {"context": "legacy", "state": "SUCCESS"},
        ])
        self.assertEqual(verdict["state"], "passing")
        self.assertEqual(len(verdict["passing"]), 2)

    def test_a_running_check_is_pending_not_passing(self):
        verdict = delivery.classify_checks([
            {"name": "validate", "status": "COMPLETED", "conclusion": "SUCCESS"},
            {"name": "slow", "status": "IN_PROGRESS", "conclusion": None},
        ])
        self.assertEqual(verdict["state"], "pending")
        self.assertEqual([item["name"] for item in verdict["pending"]], ["slow"])

    def test_a_failing_check_outranks_a_pending_one(self):
        verdict = delivery.classify_checks([
            {"name": "slow", "status": "QUEUED"},
            {"name": "unit", "status": "COMPLETED", "conclusion": "FAILURE"},
        ])
        self.assertEqual(verdict["state"], "failing")
        self.assertEqual([item["name"] for item in verdict["failing"]], ["unit"])

    def test_skipped_and_neutral_do_not_block(self):
        verdict = delivery.classify_checks([
            {"name": "optional", "status": "COMPLETED", "conclusion": "SKIPPED"},
            {"name": "advisory", "status": "COMPLETED", "conclusion": "NEUTRAL"},
        ])
        self.assertEqual(verdict["state"], "passing")

    def test_a_cancelled_check_blocks_because_it_never_reported(self):
        verdict = delivery.classify_checks([
            {"name": "unit", "status": "COMPLETED", "conclusion": "CANCELLED"},
        ])
        self.assertEqual(verdict["state"], "failing")

    def test_an_unrecognised_conclusion_is_not_assumed_benign(self):
        verdict = delivery.classify_checks([
            {"name": "mystery", "status": "COMPLETED", "conclusion": "WAT"},
        ])
        self.assertEqual(verdict["state"], "failing")
        self.assertEqual(verdict["failing"][0]["reason"], "unrecognised conclusion")


class MergeGate(SessionCase):
    """A merge needs evidence; absence of a pull request is not evidence."""

    def test_merge_without_a_pull_request_is_refused(self):
        failed = self.run_verb("pr.merge", "phase-01-000000000", expect_ok=False)
        # No gh, unauthenticated gh, or gh with nothing to show all block the
        # merge. What matters is that none of them let it through.
        self.assertIn(failed["code"],
                      {"no-pr", "gh-missing", "gh-unauthenticated", "gh-failed"})

    def test_checks_on_a_branch_with_no_pull_request_is_refused(self):
        failed = self.run_verb("pr.checks", "phase-01-000000000", expect_ok=False)
        self.assertIn(failed["code"],
                      {"no-pr", "gh-missing", "gh-unauthenticated", "gh-failed"})


class BaseSync(SessionCase):
    def test_sync_reports_honestly_when_there_is_no_remote(self):
        result = self.run_verb("pr.sync")
        self.assertFalse(result["synced"])
        self.assertIn("remote", result["reason"])
        self.assertEqual(result["base"], self.base)


if __name__ == "__main__":
    unittest.main()
