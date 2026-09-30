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


class PhaseLocate(SessionCase):
    """Routing uses real session metadata and checkout-local phase records."""

    @property
    def manifest(self):
        return self.directory / ".git" / "ai-phase" / "sessions.json"

    def add_phase(self, cwd, name="Located phase"):
        roadmap = Path(cwd) / ".planning" / "ROADMAP.md"
        if not roadmap.exists():
            roadmap.write_text("# Roadmap\n\n## Phases\n\n## Progress\n",
                               encoding="utf-8", newline="\n")
        return self.run_verb("phase.add", name, cwd=cwd)

    def phase_session(self, label="01"):
        session = self.run_verb("session.open", "phase", label)
        self.add_phase(session["worktree"])
        return session

    def change_sessions(self, entries):
        self.manifest.write_text(json.dumps({"sessions": entries}),
                                 encoding="utf-8", newline="\n")

    def snapshot(self):
        listed = self.git("worktree", "list", "--porcelain").stdout
        roots = [Path(line[len("worktree "):]) for line in listed.splitlines()
                 if line.startswith("worktree ")]
        planning = {str(root): {str(path.relative_to(root)): path.read_bytes()
                               for path in (root / ".planning").rglob("*")
                               if path.is_file()}
                    for root in roots if root.is_dir()}
        return {"worktrees": listed, "planning": planning,
                "refs": self.git("show-ref").stdout,
                "manifest": self.manifest.read_bytes() if self.manifest.exists() else None,
                "status": {str(root): self.git("status", "--porcelain", cwd=root).stdout
                           for root in roots if root.is_dir()}}

    def locate(self, number, **options):
        before = self.snapshot()
        result = self.run_verb("phase.locate", number, **options)
        self.assertEqual(before, self.snapshot(), "phase.locate changed repository state")
        return result

    def test_primary_locates_session_then_bundle_reads_context_and_plan_there(self):
        session = self.phase_session()
        target = Path(session["worktree"])
        phase_dir = target / ".planning" / "phases" / "01-located-phase"
        (phase_dir / "01-CONTEXT.md").write_text("# Session context\n", encoding="utf-8")
        (phase_dir / "01-01-PLAN.md").write_text("# Session plan\n", encoding="utf-8")
        self.assertFalse((self.directory / ".planning" / "ROADMAP.md").exists())
        self.assertFalse(self.run_verb("init.plan-phase", "01")["phase_found"])
        located = self.locate("1")
        self.assertEqual(located["source"], "session")
        self.assertEqual(located["padded_phase"], "01")
        self.assertEqual(located["branch"], session["branch"])
        self.assertEqual(Path(located["worktree"]), target.resolve())
        self.assertTrue(Path(located["worktree"]).is_absolute())
        self.assertEqual(located["session"], json.loads(self.manifest.read_text())["sessions"][0])
        before = self.snapshot()
        bundle = self.run_verb("init.plan-phase", located["padded_phase"],
                               cwd=located["worktree"])
        self.assertTrue(bundle["phase_found"])
        self.assertTrue(bundle["has_context"])
        self.assertTrue(bundle["has_plans"])
        self.assertEqual(bundle["artifacts"]["plans"], ["01-01-PLAN.md"])
        self.assertEqual((target / bundle["phase_dir"] / bundle["artifacts"]["context"])
                         .read_text(), "# Session context\n")
        self.assertEqual((target / bundle["phase_dir"] / bundle["artifacts"]["plans"][0])
                         .read_text(), "# Session plan\n")
        self.assertEqual(before, self.snapshot())

    def test_session_takes_precedence_over_phase_copied_into_current_checkout(self):
        session = self.phase_session("1")
        self.add_phase(self.directory, "Primary copy")
        located = self.locate("01")
        self.assertEqual(located["source"], "session")
        self.assertEqual(located["worktree"], session["worktree"])

    def test_decimal_session_and_input_labels_normalize_consistently(self):
        session = self.phase_session("1.10")
        inserted = self.run_verb("phase.insert", "1", "Inserted phase", cwd=session["worktree"])
        self.assertEqual(inserted["padded"], "01.1")
        for label in ("1.1", "01.1", "1.10", "001.100"):
            with self.subTest(label=label):
                located = self.locate(label)
                self.assertEqual(located["padded_phase"], "01.1")
                self.assertEqual(located["worktree"], session["worktree"])
                self.assertEqual(located["source"], "session")

    def test_no_session_prefers_current_checkout_even_with_another_phase_copy(self):
        self.add_phase(self.directory)
        other = self.run_verb("session.open", "quick", "other-copy")
        self.add_phase(other["worktree"], "Other copy")
        self.manifest.unlink()
        located = self.locate("1", cwd=other["worktree"])
        self.assertEqual(located["source"], "current-checkout")
        self.assertEqual(located["worktree"], other["worktree"])
        self.assertIsNone(located["session"])
        self.assertFalse(self.manifest.exists())

    def test_no_session_falls_back_to_unique_registered_worktree(self):
        session = self.phase_session()
        self.manifest.unlink()
        located = self.locate("01")
        self.assertEqual(located["source"], "registered-worktree")
        self.assertEqual(located["worktree"], session["worktree"])
        self.assertEqual(located["branch"], session["branch"])
        self.assertIsNone(located["session"])
        self.assertFalse(self.manifest.exists())

    def test_multiple_registered_phase_copies_fail_with_paths_and_branches(self):
        first = self.phase_session()
        second = self.run_verb("session.open", "quick", "phase-copy")
        self.add_phase(second["worktree"])
        self.manifest.unlink()
        failed = self.locate("1", expect_ok=False)
        self.assertEqual(failed["code"], "ambiguous-phase-worktree")
        for session in (first, second):
            self.assertIn(session["worktree"], failed["error"])
            self.assertIn(session["branch"], failed["error"])

    def test_duplicate_equivalent_session_labels_fail(self):
        first = self.phase_session("01")
        second = self.run_verb("session.open", "phase", "1")
        failed = self.locate("1", expect_ok=False)
        self.assertEqual(failed["code"], "ambiguous-phase-session")
        for session in (first, second):
            self.assertIn(session["worktree"], failed["error"])
            self.assertIn(session["branch"], failed["error"])

    def test_missing_session_checkout_fails_without_fallback_or_manifest_repair(self):
        session = self.phase_session()
        self.add_phase(self.directory, "Available copy")
        target = Path(session["worktree"]).resolve()
        self.assertEqual(target.parent, (self.directory / ".worktrees").resolve())
        target.rename(target.with_name("moved-checkout"))
        failed = self.locate("01", expect_ok=False)
        self.assertEqual(failed["code"], "missing-session-worktree")
        self.assertEqual(json.loads(self.manifest.read_text())["sessions"][0]["status"], "open")

    def test_existing_but_unregistered_session_checkout_fails(self):
        session = self.phase_session()
        self.add_phase(self.directory, "Available copy")
        unregistered = self.directory / "unregistered"
        unregistered.mkdir()
        entry = json.loads(self.manifest.read_text())["sessions"][0]
        entry["worktree"] = str(unregistered.resolve())
        self.change_sessions([entry])
        failed = self.locate("1", expect_ok=False)
        self.assertEqual(failed["code"], "unregistered-session-worktree")

    def test_session_branch_disagreement_fails_without_fallback(self):
        session = self.phase_session()
        self.add_phase(self.directory, "Available copy")
        entry = json.loads(self.manifest.read_text())["sessions"][0]
        entry["branch"] = "phase-wrong-branch"
        self.change_sessions([entry])
        failed = self.locate("01", expect_ok=False)
        self.assertEqual(failed["code"], "session-branch-mismatch")
        self.assertIn(session["branch"], failed["error"])
        self.assertIn("phase-wrong-branch", failed["error"])

    def test_selected_session_without_phase_fails_even_when_current_has_phase(self):
        self.run_verb("session.open", "phase", "01")
        self.add_phase(self.directory, "Available copy")
        failed = self.locate("1", expect_ok=False)
        self.assertEqual(failed["code"], "session-phase-missing")

    def test_closed_session_is_ignored(self):
        session = self.phase_session()
        entry = json.loads(self.manifest.read_text())["sessions"][0]
        entry["status"] = "closed"
        self.change_sessions([entry])
        located = self.locate("01")
        self.assertEqual(located["source"], "registered-worktree")
        self.assertEqual(located["worktree"], session["worktree"])
        self.assertIsNone(located["session"])

    def test_no_phase_returns_false_without_creating_any_records_or_worktrees(self):
        for label in ("1", "01", "01.20"):
            with self.subTest(label=label):
                located = self.locate(label)
                self.assertFalse(located["phase_found"])
                self.assertEqual(located["source"], "none")
                self.assertIsNone(located["worktree"])
                self.assertIsNone(located["branch"])
                self.assertIsNone(located["session"])
        self.assertFalse(self.manifest.exists())
        self.assertFalse((self.directory / ".worktrees").exists())

    def test_branch_and_directory_names_are_not_evidence_of_phase_existence(self):
        session = self.run_verb("session.open", "quick", "phase-01")
        (Path(session["worktree"]) / ".planning" / "phases" / "01-directory-only").mkdir(
            parents=True)
        self.manifest.unlink()
        self.assertFalse(self.locate("01")["phase_found"])


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


class WaitingForChecks(unittest.TestCase):
    """Shipping waits for CI itself instead of stopping for the user to re-run it."""

    def setUp(self):
        self.now = 0.0
        self.slept = []
        self.rollups = []
        originals = (delivery.require_gh, delivery.view)
        self.addCleanup(lambda: (setattr(delivery, "require_gh", originals[0]),
                                 setattr(delivery, "view", originals[1])))
        delivery.require_gh = lambda workspace: None
        delivery.view = lambda workspace, branch, cwd=None: {
            "number": 7, "url": "u", "state": "OPEN",
            "statusCheckRollup": self.rollups.pop(0) if len(self.rollups) > 1
            else self.rollups[0]}

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds

    def verdict(self, **options):
        return delivery.checks(None, "phase-01", sleep=self.sleep,
                               clock=lambda: self.now, **options)

    RUNNING = [{"name": "unit", "status": "IN_PROGRESS"}]
    GREEN = [{"name": "unit", "status": "COMPLETED", "conclusion": "SUCCESS"}]

    def test_without_wait_a_pending_verdict_returns_at_once(self):
        self.rollups = [self.RUNNING]
        self.assertEqual("pending", self.verdict()["state"])
        self.assertEqual([], self.slept)

    def test_a_wait_rereads_until_the_checks_settle(self):
        self.rollups = [self.RUNNING, self.RUNNING, self.GREEN]
        result = self.verdict(wait=300, interval=30)
        self.assertEqual("passing", result["state"])
        self.assertEqual([30, 30], self.slept)
        self.assertEqual(60, result["waited"])

    def test_the_wait_is_bounded_and_still_reports_pending(self):
        self.rollups = [self.RUNNING]
        result = self.verdict(wait=90, interval=30)
        self.assertEqual("pending", result["state"])
        self.assertLessEqual(sum(self.slept), 90)

    def test_a_settled_verdict_never_waits(self):
        self.rollups = [self.GREEN]
        self.assertEqual("passing", self.verdict(wait=300)["state"])
        self.assertEqual([], self.slept)


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
