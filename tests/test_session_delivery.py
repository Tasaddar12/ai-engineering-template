"""Session and delivery contracts for the standalone engineer runtime.

Session tests use real temporary repositories and the current command API.
Provider writes are deterministic offline seams; currentness, identity and
readback gates remain in production code. All check execution waits for the
user-authorized final batch.
"""
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
RUNTIME = ROOT / "engineer" / "bin" / "engineer.py"

sys.path.insert(0, str(ROOT / "engineer" / "bin"))
from lib import delivery  # noqa: E402
from lib.core import Args, Failure

CONFIG = """commit_docs: true
worktree:
  directory: .worktrees
verification:
  commands: []
git:
  protected_branches: [main, master, develop]
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
        if completed.returncode:
            failure = json.loads(completed.stderr.splitlines()[-1])
            payload = {"ok": False, "code": failure["error"], "error": json.dumps(failure)}
        else:
            payload = {"ok": True, **json.loads(completed.stdout)}
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
        self.assertTrue(result["branch"].startswith("codex/phase-01"))
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
        self.assertEqual(failed["code"], "invalid-session-kind")

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
        return self.directory / ".git" / "engineer" / "sessions.json"

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
        second = {**first, "label": "1"}
        self.change_sessions([first, second])
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


class SessionAdoption(SessionCase):
    manifest = PhaseLocate.manifest
    add_phase = PhaseLocate.add_phase
    snapshot = PhaseLocate.snapshot
    locate = PhaseLocate.locate

    def linked(self, branch="feature-existing", detached=False, phase=True):
        target = self.directory / ".worktrees" / branch
        arguments = (["--detach"] if detached else ["-b", branch])
        result = self.git("worktree", "add", *arguments, str(target), "HEAD")
        self.assertEqual(result.returncode, 0, result.stderr)
        if phase:
            self.add_phase(target)
        return target.resolve()

    def write_sessions(self, entries):
        self.manifest.parent.mkdir(parents=True, exist_ok=True)
        self.manifest.write_text(json.dumps({"sessions": entries}), encoding="utf-8")

    def refused(self, target, code, label="01", kind="phase"):
        before = self.snapshot()
        failed = self.run_verb("session.adopt", kind, label, cwd=target, expect_ok=False)
        self.assertEqual(failed["code"], code, failed)
        self.assertEqual(before, self.snapshot(), "refused adoption changed repository state")
        return failed

    def test_adopts_existing_dirty_phase_and_reroutes_bundle_without_changing_checkout(self):
        common_base = self.git("rev-parse", "HEAD").stdout.strip()
        target = self.linked()
        (target / "branch-only.txt").write_text("committed branch work\n", encoding="utf-8")
        self.git("add", "branch-only.txt", cwd=target)
        self.git("commit", "-qm", "branch work", cwd=target)
        (self.directory / "base-only.txt").write_text("base advances\n", encoding="utf-8")
        self.git("add", "base-only.txt")
        self.git("commit", "-qm", "base work")
        phase_dir = target / ".planning" / "phases" / "01-located-phase"
        (phase_dir / "01-CONTEXT.md").write_text("# Dirty context\n", encoding="utf-8")
        (phase_dir / "01-01-PLAN.md").write_text("# Dirty plan\n", encoding="utf-8")
        (target / "README.md").write_text("# Dirty staged file\n", encoding="utf-8")
        self.git("add", "README.md", cwd=target)
        self.assertEqual(self.locate("1")["source"], "registered-worktree")
        before = self.snapshot()
        adopted = self.run_verb("session.adopt", "phase", "1", cwd=target)
        after = self.snapshot()
        self.assertIsNone(before.pop("manifest"))
        self.assertIsNotNone(after.pop("manifest"))
        self.assertEqual(before, after)
        self.assertFalse(adopted["reused"])
        self.assertTrue(adopted["adopted"])
        self.assertIsNone(adopted["synced"])
        self.assertEqual(adopted["label"], "01")
        self.assertEqual(adopted["base"], common_base)
        self.assertEqual(adopted["base_branch"], self.base)
        self.assertEqual(adopted["branch"], "feature-existing")
        self.assertEqual(adopted["worktree"], str(target))
        self.assertEqual(adopted["status"], "open")
        self.assertIsNone(adopted["pr"])
        self.assertTrue(adopted["created_at"])
        located = self.locate("01")
        self.assertEqual(located["source"], "session")
        self.assertEqual(located["worktree"], str(target))
        bundle = self.run_verb("init.plan-phase", located["padded_phase"], cwd=target)
        self.assertTrue(bundle["has_context"])
        self.assertEqual(bundle["artifacts"]["plans"], ["01-01-PLAN.md"])
        self.assertEqual((target / bundle["phase_dir"] / bundle["artifacts"]["context"])
                         .read_text(), "# Dirty context\n")
        self.assertEqual((target / bundle["phase_dir"] / bundle["artifacts"]["plans"][0])
                         .read_text(), "# Dirty plan\n")
        closed = self.run_verb("session.close", adopted["branch"])
        self.assertFalse(closed["closed"])
        self.assertTrue(closed["preserved"])
        self.assertEqual(closed["evidence"]["evidence"], "ancestry")
        self.assertFalse(closed["evidence"]["merged"])
        self.assertEqual(after, {k: v for k, v in self.snapshot().items() if k != "manifest"})

    def test_adoption_is_idempotent_across_equivalent_decimal_labels(self):
        target = self.linked()
        self.run_verb("phase.insert", "1", "Inserted phase", cwd=target)
        first = self.run_verb("session.adopt", "phase", "1.10", cwd=target)
        before = self.snapshot()
        second = self.run_verb("session.adopt", "phase", "01.1", cwd=target)
        self.assertEqual(before, self.snapshot())
        self.assertTrue(second["reused"])
        self.assertTrue(second["adopted"])
        self.assertIsNone(second["synced"])
        self.assertEqual(second["label"], "01.1")
        self.assertEqual(first["base"], second["base"])
        self.assertEqual(len(json.loads(self.manifest.read_text())["sessions"]), 1)

    def test_reuses_valid_existing_phase_session_without_rewriting_manifest(self):
        session = self.run_verb("session.open", "phase", "1")
        self.add_phase(session["worktree"])
        before = self.snapshot()
        result = self.run_verb("session.adopt", "phase", "01", cwd=session["worktree"])
        self.assertTrue(result["reused"])
        self.assertEqual(result["label"], "01")
        self.assertEqual(before, self.snapshot())

    def test_primary_checkout_is_refused(self):
        self.add_phase(self.directory)
        self.refused(self.directory, "session-adopt-not-linked")

    def test_detached_checkout_is_refused(self):
        target = self.linked(detached=True)
        self.refused(target, "session-adopt-detached")

    def test_protected_branch_is_refused(self):
        target = self.linked(branch="develop")
        self.refused(target, "protected-branch")

    def test_missing_phase_is_refused_without_creating_manifest(self):
        target = self.linked(phase=False)
        self.refused(target, "phase-not-found")
        self.assertFalse(self.manifest.exists())

    def test_another_selected_checkout_is_refused(self):
        target = self.linked()
        session = self.run_verb("session.open", "phase", "01")
        self.add_phase(session["worktree"])
        self.refused(target, "session-adopt-wrong-checkout")

    def test_conflicting_open_session_on_branch_or_path_is_refused(self):
        target = self.linked()
        cases = [
            {"kind": "quick", "label": "fix", "branch": "other-branch", "worktree": str(target)},
            {"kind": "phase", "label": "02", "branch": "feature-existing", "worktree": str(self.directory)},
        ]
        for entry in cases:
            with self.subTest(entry=entry):
                self.write_sessions([dict(entry, status="open")])
                self.refused(target, "session-adopt-conflict")

    def test_valid_matching_session_does_not_hide_a_conflicting_owner(self):
        target = self.linked()
        self.run_verb("session.adopt", "phase", "01", cwd=target)
        existing = json.loads(self.manifest.read_text())["sessions"]
        conflict = {"kind": "quick", "label": "fix", "branch": "other-branch",
                    "worktree": str(target), "status": "open"}
        self.write_sessions(existing + [conflict])
        self.refused(target, "session-adopt-conflict")

    def test_duplicate_or_disagreeing_phase_sessions_are_refused(self):
        target = self.linked()
        self.run_verb("session.adopt", "phase", "01", cwd=target)
        entry = json.loads(self.manifest.read_text())["sessions"][0]
        self.write_sessions([entry, dict(entry, label="1")])
        self.refused(target, "ambiguous-phase-session")
        self.write_sessions([dict(entry, branch="wrong-branch")])
        self.refused(target, "session-branch-mismatch")


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
        self.assertEqual(failed["code"], "session-not-found")

    def test_force_does_not_override_unmerged_resource_preservation(self):
        session = self.open_and_commit()
        result = self.run_verb("session.close", session["branch"], "--force")
        self.assertFalse(result["closed"])
        self.assertTrue(result["preserved"])
        self.assertEqual(result["reason"], "session-not-integrated")
        self.assertTrue(Path(session["worktree"]).is_dir())


class OpeningPullRequests(unittest.TestCase):
    """Real checkout identity and an offline stateful provider boundary."""
    BRANCH = "phase-child"

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="engineer-pr-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name).resolve()
        for args in (("init", "-q", "-b", self.BRANCH), ("config", "user.name", "PR Fixture"), ("config", "user.email", "pr@example.invalid")):
            subprocess.run(["git", *args], cwd=self.directory, check=True, capture_output=True)
        (self.directory/"source").write_text("fixture")
        for args in (("add", "."), ("commit", "-qm", "Fixture change"), ("branch", "main"), ("branch", "stack-parent"), ("branch", "new-parent"), ("remote", "add", "origin", "https://github.com/owner/repo.git")):
            subprocess.run(["git", *args], cwd=self.directory, check=True, capture_output=True)
        self.head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.directory, check=True, capture_output=True, text=True).stdout.strip()
        self.body = "## Goal\nExercise reviewed publication in a disposable fixture.\n## Changes\nUpdate provider metadata with exact readback.\n## Verification\nNot run; fixture authoring only.\n## Known gaps\nProvider evidence comes from a deterministic offline fixture.\n## Risks or rollback\nDiscard the temporary repository after the test.\n"
        self.pull = {"number": 7, "url": "https://github.com/owner/repo/pull/7", "state": "OPEN", "isDraft": True, "baseRefName": "stack-parent", "headRefName": self.BRANCH, "headRefOid": self.head, "title": "Original", "body": self.body, "statusCheckRollup": [{"conclusion": "SUCCESS"}]}
        self.calls, self.pushes = [], []
        self.edit_error = None
        self.authenticated = True
        environment = patch.dict(os.environ, {"ENGINEER_ROOT": str(self.directory)})
        environment.start()
        self.addCleanup(environment.stop)
        from lib import core
        self.real_run = core.run
        boundary = patch.object(delivery, "run", side_effect=self.local_run)
        boundary.start()
        self.addCleanup(boundary.stop)
        provider = patch.object(delivery, "gh", side_effect=self.fake_gh)
        provider.start()
        self.addCleanup(provider.stop)

    def local_run(self, argv, cwd=None, **options):
        if argv[0:2] == ["git", "push"]:
            self.pushes.append(argv)
            return subprocess.CompletedProcess(argv, 0, "", "")
        return self.real_run(argv, cwd, **options)

    def fake_gh(self, args, check=True):
        self.calls.append(args)
        if not self.authenticated:
            if check: raise Failure("provider-query-failed", "authentication required")
            return subprocess.CompletedProcess(args, 1, "", "authentication required")
        if args[:2] == ["pr", "view"]:
            if self.pull is None:
                return subprocess.CompletedProcess(args, 1, "", "no pull requests found")
            return subprocess.CompletedProcess(args, 0, json.dumps(self.pull), "")
        if args[:2] == ["pr", "merge"]:
            self.merge_calls += 1
            self.pull = self.merge_response
        elif args[:2] == ["pr", "edit"]:
            self.assertEqual(args[2], str(self.pull["number"]))
            if self.edit_error: raise Failure("command-failed", self.edit_error)
            self.apply_fields(args)
        elif args[:2] == ["pr", "create"]:
            self.assertIsNone(self.pull)
            self.pull = {"number": 8, "url": "https://github.com/owner/repo/pull/8", "state": "OPEN", "headRefName": self.BRANCH, "headRefOid": self.head, "isDraft": "--draft" in args}
            self.apply_fields(args)
        else:
            self.fail("Unexpected provider mutation: "+repr(args))
        return subprocess.CompletedProcess(args, 0, "", "")

    def apply_fields(self, args):
        for option, field in (("--base", "baseRefName"), ("--title", "title")):
            if option in args: self.pull[field] = args[args.index(option)+1]
        if "--body-file" in args:
            self.pull["body"] = Path(args[args.index("--body-file")+1]).read_text(encoding="utf-8")

    def open(self, **options):
        values = [self.BRANCH]
        for key, value in options.items():
            values.extend(["--"+key.replace("_", "-"), str(value)])
        return delivery.command(Args(values), "open")

    def mutations(self):
        return [call for call in self.calls if call[:2] in (["pr", "edit"], ["pr", "create"], ["pr", "merge"])]

    def test_merge_command_success_needs_matching_merged_readback(self):
        original = dict(self.pull, isDraft=False)
        for response in (None, dict(original, state="OPEN"), dict(original, state="CLOSED"), dict(original, state="MERGED", number=99), dict(original, state="MERGED", url="https://github.com/foreign/repo/pull/7"), dict(original, state="MERGED", headRefName="other"), {}):
            with self.subTest(response=response):
                self.pull, self.merge_response, self.merge_calls = dict(original), response, 0
                with patch.object(delivery, "verified_delivery", return_value=original):
                    with self.assertRaises(Failure):
                        delivery.command(Args([self.BRANCH, "--confirm"]), "merge")
                self.assertEqual(1, self.merge_calls)

    def test_explicit_base_only_retargets_and_returns_refreshed_pr(self):
        result = self.open(base="main")
        self.assertEqual("main", result["baseRefName"])
        self.assertFalse(result["created"])
        self.assertTrue(result["updated"])
        self.assertEqual(7, result["number"])
        self.assertEqual([["pr", "edit", "7", "--base", "main"]], self.mutations())

    def test_omitted_base_with_no_fields_preserves_nondefault_target(self):
        result = self.open()
        self.assertEqual("stack-parent", result["baseRefName"])
        self.assertFalse(result["created"])
        self.assertFalse(result["updated"])
        self.assertEqual([], self.mutations())
        self.assertEqual([], self.pushes)

    def test_metadata_edits_preserve_target_and_body_file_precedence(self):
        body_file = self.directory/"pull body.md"
        body_file.write_text(self.body+"\nReviewed file body.\n", encoding="utf-8")
        result = self.open(title="Updated", body="Ignored", body_file=body_file)
        self.assertEqual("stack-parent", result["baseRefName"])
        self.assertEqual("Updated", result["title"])
        self.assertEqual(body_file.read_text(), result["body"])
        self.assertTrue(result["updated"])
        self.assertNotIn("--base", self.mutations()[0])
        self.assertNotIn("--body", self.mutations()[0])

    def test_explicit_base_and_metadata_update_the_same_pr(self):
        result = self.open(base="new-parent", title="Retargeted", body=self.body+"\nReviewed retarget.\n")
        self.assertEqual("new-parent", result["baseRefName"])
        self.assertEqual("Retargeted", result["title"])
        self.assertEqual(7, result["number"])
        self.assertEqual(1, len(self.mutations()))
        with self.assertRaises(Failure): self.open(body="")
        self.assertEqual(1, len(self.mutations()))

    def test_existing_draft_and_ready_state_ignore_creation_draft_argument(self):
        for is_draft in (True, False):
            self.pull["isDraft"] = is_draft
            for requested in ("true", "false"):
                self.calls.clear()
                self.assertEqual(is_draft, self.open(base="main", draft=requested)["isDraft"])
                self.assertEqual([["pr", "edit", "7", "--base", "main"]], self.mutations())

    def test_new_pr_uses_default_base_title_and_draft(self):
        self.pull = None
        result = self.open(body=self.body)
        self.assertEqual("main", result["baseRefName"])
        self.assertEqual("Fixture change", result["title"])
        self.assertTrue(result["isDraft"])
        self.assertTrue(result["created"])
        self.assertFalse(result["updated"])

    def test_new_pr_uses_explicit_base_metadata_and_ready_state(self):
        # Creation always produces a draft; explicit verified pr.ready owns the
        # transition to ready and cannot be replaced by a creation argument.
        body_file = self.directory/"pull body.md"
        body_file.write_text(self.body+"\nCreation file.\n", encoding="utf-8")
        for options, expected in (({"body": self.body}, self.body), ({"body": "Ignored", "body_file": body_file}, body_file.read_text())):
            self.pull = None
            self.calls.clear()
            result = self.open(base="stack-parent", title="Child work", draft="false", **options)
            self.assertEqual("stack-parent", result["baseRefName"])
            self.assertEqual("Child work", result["title"])
            self.assertEqual(expected, result["body"])
            self.assertTrue(result["isDraft"])
            self.assertTrue(result["created"])
            self.assertFalse(result["updated"])

    def test_failed_retarget_propagates_gh_error_without_success(self):
        self.edit_error = "target branch does not exist"
        with self.assertRaises(Failure) as caught:
            self.open(base="main")
        self.assertEqual("command-failed", caught.exception.code)
        self.assertIn(self.edit_error, str(caught.exception))
        self.assertEqual("stack-parent", self.pull["baseRefName"])
        self.assertEqual(1, sum(call[:2] == ["pr", "view"] for call in self.calls))

    def test_unauthenticated_open_is_refused_without_mutation(self):
        self.authenticated = False
        with self.assertRaises(Failure): self.open(base="main")
        self.assertEqual([], self.mutations())
        self.assertEqual([], self.pushes)

class CheckClassification(unittest.TestCase):
    """The verdict that decides whether a merge may happen at all."""

    def test_no_checks_is_not_a_pass(self):
        verdict = delivery.classify_checks([])
        self.assertEqual(verdict["status"], "none")
        self.assertEqual(verdict["count"], 0)

    def test_all_successful_checks_pass(self):
        verdict = delivery.classify_checks([
            {"name": "validate", "status": "COMPLETED", "conclusion": "SUCCESS"},
            {"context": "legacy", "state": "SUCCESS"},
        ])
        self.assertEqual(verdict["status"], "passed")
        self.assertEqual(verdict["count"], 2)

    def test_a_running_check_is_pending_not_passing(self):
        verdict = delivery.classify_checks([
            {"name": "validate", "status": "COMPLETED", "conclusion": "SUCCESS"},
            {"name": "slow", "status": "IN_PROGRESS", "conclusion": None},
        ])
        self.assertEqual(verdict["status"], "pending")
        self.assertEqual(verdict["pending"], ["slow"])

    def test_a_failing_check_outranks_a_pending_one(self):
        verdict = delivery.classify_checks([
            {"name": "slow", "status": "QUEUED"},
            {"name": "unit", "status": "COMPLETED", "conclusion": "FAILURE"},
        ])
        self.assertEqual(verdict["status"], "failed")
        self.assertEqual(verdict["failed"], ["unit"])

    def test_skipped_and_neutral_do_not_block(self):
        verdict = delivery.classify_checks([
            {"name": "optional", "status": "COMPLETED", "conclusion": "SKIPPED"},
            {"name": "advisory", "status": "COMPLETED", "conclusion": "NEUTRAL"},
        ])
        self.assertEqual(verdict["status"], "passed")

    def test_a_cancelled_check_blocks_because_it_never_reported(self):
        verdict = delivery.classify_checks([
            {"name": "unit", "status": "COMPLETED", "conclusion": "CANCELLED"},
        ])
        self.assertEqual(verdict["status"], "failed")

    def test_an_unrecognised_conclusion_is_not_assumed_benign(self):
        verdict = delivery.classify_checks([
            {"name": "mystery", "status": "COMPLETED", "conclusion": "WAT"},
        ])
        self.assertEqual(verdict["status"], "failed")
        self.assertEqual(verdict["failed"], ["mystery"])


class WaitingForChecks(unittest.TestCase):
    """Current command waits with a bounded clock and re-reads each verdict."""
    RUNNING = [{"name": "unit", "status": "IN_PROGRESS"}]
    GREEN = [{"name": "unit", "status": "COMPLETED", "conclusion": "SUCCESS"}]

    def setUp(self):
        self.now, self.slept, self.rollups = 0.0, [], []

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds

    def verdict(self, wait=0):
        def view(branch):
            rollup = self.rollups.pop(0) if len(self.rollups) > 1 else self.rollups[0]
            return {"url": "https://github.com/owner/repo/pull/7", "statusCheckRollup": rollup}
        with patch.object(delivery, "view", side_effect=view), patch.object(delivery.time, "monotonic", side_effect=lambda: self.now), patch.object(delivery.time, "sleep", side_effect=self.sleep):
            result, status = delivery.command(Args(["phase-01", "--timeout", str(wait)]), "checks")
        self.assertEqual(1 if result["status"] == "pending" else 0, status)
        return result

    def test_without_wait_a_pending_verdict_returns_at_once(self):
        self.rollups = [self.RUNNING]
        self.assertEqual("pending", self.verdict()["status"])
        self.assertEqual([], self.slept)

    def test_a_wait_rereads_until_the_checks_settle(self):
        self.rollups = [self.RUNNING, self.RUNNING, self.GREEN]
        self.assertEqual("passed", self.verdict(wait=300)["status"])
        self.assertEqual([5, 5], self.slept)
        self.assertEqual(10, self.now)

    def test_the_wait_is_bounded_and_still_reports_pending(self):
        self.rollups = [self.RUNNING]
        self.assertEqual("pending", self.verdict(wait=12)["status"])
        self.assertEqual([5, 5, 2], self.slept)
        self.assertEqual(12, self.now)

    def test_a_settled_verdict_never_waits(self):
        self.rollups = [self.GREEN]
        self.assertEqual("passed", self.verdict(wait=300)["status"])
        self.assertEqual([], self.slept)

class MergeGate(SessionCase):
    def test_merge_without_a_pull_request_is_refused(self):
        with patch.object(delivery, "gh") as provider:
            with self.assertRaises(Failure) as caught:
                delivery.command(Args(["phase-01-absent"]), "merge")
        self.assertEqual("merge-not-authorized", caught.exception.code)
        provider.assert_not_called()

    def test_checks_on_a_branch_with_no_pull_request_is_refused(self):
        with patch.object(delivery, "view", return_value=None):
            with self.assertRaises(Failure) as caught:
                delivery.command(Args(["phase-01-absent"]), "checks")
        self.assertEqual("pr-not-found", caught.exception.code)

class BaseSync(SessionCase):
    def test_sync_reports_honestly_when_there_is_no_remote(self):
        result = self.run_verb("pr.sync")
        self.assertFalse(result["synced"])
        self.assertIn("remote", result["reason"])
        self.assertEqual(result["base"], self.base)


class ReviewedProviderDelivery(unittest.TestCase):
    """Provider boundary regressions for the current reviewed publication API."""
    def test_completed_without_success_conclusion_remains_pending(self):
        self.assertEqual(delivery.classify_checks([{"name": "unfinished", "status": "COMPLETED"}])["status"], "pending")

    def test_merge_requires_explicit_confirmation_before_provider_or_verification(self):
        with patch.object(delivery, "verified_delivery") as gate:
            with self.assertRaises(Failure) as raised:
                delivery.command(Args(["topic"]), "merge")
            self.assertEqual(raised.exception.code, "merge-not-authorized")
            gate.assert_not_called()

    def test_successful_merge_command_requires_same_head_merged_readback(self):
        current = {"number": 7, "url": "https://github.com/owner/repo/pull/7", "headRefOid": "abc", "statusCheckRollup": [{"conclusion": "SUCCESS"}], "mergeable": "MERGEABLE"}
        for final in (None, {**current, "state": "OPEN"}, {**current, "state": "MERGED", "headRefOid": "changed", "mergedAt": "2026-10-27"}):
            with self.subTest(final=final), patch.object(delivery, "verified_delivery", return_value=current), patch.object(delivery, "gh"), patch.object(delivery, "view", return_value=final):
                with self.assertRaises(Failure) as raised:
                    delivery.command(Args(["topic", "--confirm"]), "merge")
                self.assertEqual(raised.exception.code, "pr-merge-uncertain")
        final = {**current, "state": "MERGED", "mergedAt": "2026-10-27"}
        with patch.object(delivery, "verified_delivery", return_value=current), patch.object(delivery, "gh"), patch.object(delivery, "view", return_value=final):
            self.assertTrue(delivery.command(Args(["topic", "--confirm"]), "merge")["merged"])

    def test_ready_readback_cannot_silently_accept_changed_head(self):
        reviewed = {"url": "https://github.com/owner/repo/pull/7", "headRefOid": "abc"}
        final = {**reviewed, "state": "OPEN", "isDraft": False, "headRefOid": "changed"}
        with patch.object(delivery, "verified_delivery", return_value=reviewed), patch.object(delivery, "gh"), patch.object(delivery, "view", return_value=final):
            with self.assertRaises(Failure) as raised:
                delivery.command(Args(["topic", "--phase", "01"]), "ready")
            self.assertEqual(raised.exception.code, "pr-ready-uncertain")

    def test_canonical_provider_url_rejects_redirect_decorations_and_wrong_repository(self):
        from lib import repository
        identity = {"hostname": "github.com", "owner": "owner", "repository": "repo"}
        with patch.object(repository, "identity", return_value=identity):
            self.assertEqual(repository.require_url("https://github.com/owner/repo/pull/7", "pull"), 7)
            for url in ("https://github.com/owner/repo/pull/7?redirect=elsewhere", "https://github.com/owner/repo/pull/7#fragment", "https://evil@github.com/owner/repo/pull/7", "https://github.com/another/repo/pull/7"):
                with self.subTest(url=url), self.assertRaises(Failure):
                    repository.require_url(url, "pull")


if __name__ == "__main__":
    unittest.main()





