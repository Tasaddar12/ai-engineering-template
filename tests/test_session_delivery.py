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
from types import SimpleNamespace
from unittest.mock import patch

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
        self.assertEqual(failed["code"], "no-session")

    def test_force_closes_unmerged_work_when_explicitly_asked(self):
        session = self.open_and_commit()
        result = self.run_verb("session.close", session["branch"], "--force")
        self.assertTrue(result["closed"])
        self.assertTrue(result["forced"])


class OpeningPullRequests(unittest.TestCase):
    """A stateful gh seam exercises delivery without credentials or a network."""

    BRANCH = "phase-child"

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="phase-pr-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.workspace = SimpleNamespace(root=self.directory)
        self.pull = {
            "number": 7, "url": "https://example.test/pull/7", "state": "OPEN",
            "isDraft": True, "baseRefName": "stack-parent",
            "headRefName": self.BRANCH, "title": "Original", "body": "Original body",
        }
        self.calls = []
        self.edit_error = None
        self.authenticated = True
        self.provider = patch.object(delivery.subprocess, "run", side_effect=self.fake_gh)
        self.provider.start()
        self.addCleanup(self.provider.stop)
        self.default_base = patch.object(delivery.gitops, "base_branch", return_value="main")
        self.default_base.start()
        self.addCleanup(self.default_base.stop)

    def fake_gh(self, command, **options):
        self.assertEqual(command[0], "gh")
        self.calls.append(command[1:])
        args = command[1:]
        stdout, stderr, code = "", "", 0
        if args == ["--version"]:
            stdout = "gh version test\n"
        elif args == ["auth", "status"]:
            if not self.authenticated:
                code, stderr = 1, "authentication required"
        elif args[:2] == ["pr", "view"]:
            self.assertEqual(args[2], self.BRANCH)
            self.assertEqual(args[3:], ["--json", delivery.PR_FIELDS])
            selected_fields = args[4].split(",")
            if self.pull is None:
                code, stderr = 1, "no pull request"
            else:
                stdout = json.dumps({key: value for key, value in self.pull.items()
                                     if key in selected_fields})
        elif args[:2] == ["pr", "edit"]:
            self.assertEqual(args[2], self.BRANCH)
            if self.edit_error:
                code, stderr = 1, self.edit_error
            else:
                self.apply_fields(args)
        elif args[:2] == ["pr", "create"]:
            self.assertIsNone(self.pull, "must update the existing PR")
            self.assertEqual(args[args.index("--head") + 1], self.BRANCH)
            self.pull = {
                "number": 8, "url": "https://example.test/pull/8", "state": "OPEN",
                "headRefName": self.BRANCH, "isDraft": "--draft" in args,
            }
            self.apply_fields(args)
        else:
            self.fail("unexpected gh command: " + repr(args))
        return subprocess.CompletedProcess(command, code, stdout, stderr)

    def apply_fields(self, args):
        for option, field in (("--base", "baseRefName"), ("--title", "title"),
                              ("--body", "body")):
            if option in args:
                self.pull[field] = args[args.index(option) + 1]
        if "--body-file" in args:
            self.pull["body"] = Path(args[args.index("--body-file") + 1]).read_text(
                encoding="utf-8")

    def mutations(self):
        return [args for args in self.calls
                if args[:2] in (["pr", "edit"], ["pr", "create"], ["pr", "ready"])]

    def test_explicit_base_only_retargets_and_returns_refreshed_pr(self):
        result = delivery.open_pr(self.workspace, self.BRANCH, base="main")
        self.assertEqual(result["baseRefName"], "main")
        self.assertFalse(result["created"])
        self.assertTrue(result["updated"])
        self.assertEqual(result["number"], 7)
        self.assertEqual(self.mutations(), [["pr", "edit", self.BRANCH, "--base", "main"]])

    def test_omitted_base_with_no_fields_preserves_nondefault_target(self):
        result = delivery.open_pr(self.workspace, self.BRANCH)
        self.assertEqual(result["baseRefName"], "stack-parent")
        self.assertFalse(result["created"])
        self.assertFalse(result["updated"])
        self.assertEqual(self.mutations(), [])

    def test_metadata_edits_preserve_target_and_body_file_precedence(self):
        body_file = self.directory / "pull body.md"
        body_file.write_text("File body", encoding="utf-8")
        result = delivery.open_pr(self.workspace, self.BRANCH, title="Updated",
                                  body="Ignored body", body_file=body_file)
        self.assertEqual(result["baseRefName"], "stack-parent")
        self.assertEqual(self.pull["title"], "Updated")
        self.assertEqual(self.pull["body"], "File body")
        self.assertTrue(result["updated"])
        self.assertNotIn("--base", self.mutations()[0])
        self.assertNotIn("--body", self.mutations()[0])

    def test_explicit_base_and_metadata_update_the_same_pr(self):
        result = delivery.open_pr(self.workspace, self.BRANCH, base="new-parent",
                                  title="Retargeted", body="")
        self.assertEqual(result["baseRefName"], "new-parent")
        self.assertEqual(self.pull["title"], "Retargeted")
        self.assertEqual(self.pull["body"], "")
        self.assertEqual(result["number"], 7)
        self.assertEqual(len(self.mutations()), 1)

    def test_existing_draft_and_ready_state_ignore_creation_draft_argument(self):
        for is_draft in (True, False):
            for requested_draft in (True, False):
                with self.subTest(is_draft=is_draft, draft=requested_draft):
                    self.pull["isDraft"] = is_draft
                    self.calls.clear()
                    result = delivery.open_pr(self.workspace, self.BRANCH, base="main",
                                              draft=requested_draft)
                    self.assertEqual(result["isDraft"], is_draft)
                    self.assertEqual(self.mutations(),
                                     [["pr", "edit", self.BRANCH, "--base", "main"]])

    def test_new_pr_uses_default_base_title_and_draft(self):
        self.pull = None
        result = delivery.open_pr(self.workspace, self.BRANCH)
        self.assertEqual(result["baseRefName"], "main")
        self.assertEqual(self.pull["title"], self.BRANCH)
        self.assertEqual(self.pull["body"], "")
        self.assertTrue(result["isDraft"])
        self.assertTrue(result["created"])
        self.assertFalse(result["updated"])

    def test_new_pr_uses_explicit_base_metadata_and_ready_state(self):
        body_file = self.directory / "pull body.md"
        body_file.write_text("Creation body", encoding="utf-8")
        for body_options, expected_body in (
                ({"body": "Inline body"}, "Inline body"),
                ({"body": "Ignored body", "body_file": body_file}, "Creation body")):
            with self.subTest(body_options=body_options):
                self.pull = None
                self.calls.clear()
                result = delivery.open_pr(self.workspace, self.BRANCH, base="stack-parent",
                                          title="Child work", draft=False, **body_options)
                self.assertEqual(result["baseRefName"], "stack-parent")
                self.assertEqual(self.pull["title"], "Child work")
                self.assertEqual(self.pull["body"], expected_body)
                self.assertFalse(result["isDraft"])
                self.assertTrue(result["created"])
                self.assertFalse(result["updated"])

    def test_failed_retarget_propagates_gh_error_without_success(self):
        self.edit_error = "target branch does not exist"
        with self.assertRaises(delivery.VerbError) as raised:
            delivery.open_pr(self.workspace, self.BRANCH, base="missing-parent")
        self.assertEqual(raised.exception.code, "gh-failed")
        self.assertIn(self.edit_error, str(raised.exception))
        self.assertEqual(self.pull["baseRefName"], "stack-parent")
        self.assertEqual(sum(args[:2] == ["pr", "view"] for args in self.calls), 1)

    def test_unauthenticated_open_is_refused_without_mutation(self):
        self.authenticated = False
        with self.assertRaises(delivery.VerbError) as raised:
            delivery.open_pr(self.workspace, self.BRANCH, base="main")
        self.assertEqual(raised.exception.code, "gh-unauthenticated")
        self.assertEqual(self.mutations(), [])


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
