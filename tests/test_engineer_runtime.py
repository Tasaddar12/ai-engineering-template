"""Behavior contracts for the fresh stdlib runtime; fixtures execute only in tests."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]
RUNTIME = SOURCE/"engineer/bin/engineer.py"


class RuntimeCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.env = {**os.environ, "ENGINEER_ROOT": str(self.root), "ENGINEER_HOST": "codex"}
        self.git("init", "-b", "main")
        self.git("config", "core.autocrlf", "false")
        self.git("config", "user.name", "Runtime Test")
        self.git("config", "user.email", "runtime@example.invalid")
        self.put("README.md", "# Fixture\n")
        self.git("add", ".")
        self.git("commit", "-m", "fixture")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, text=True, capture_output=True, check=True).stdout.strip()

    def put(self, path, content):
        destination = self.root/path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        return destination

    def cli(self, *args, status=0, raw=False, stdin=None):
        process = subprocess.run([sys.executable, "-I", str(RUNTIME), "query", *map(str, args)],
                                 cwd=self.root, env=self.env, input=stdin, text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(status, process.returncode, process.stderr or process.stdout)
        return process.stdout.strip() if raw else json.loads(process.stdout)

    def phase(self, name="Behavior"):
        return self.cli("phase.add", name)["directory"]

    def plan(self, directory, body=None, extra=""):
        path = Path(directory)/"01-01-PLAN.md"
        content = """---
phase: "01"
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified: ["src/app.py"]
files_deleted: []
resources: []
autonomous: true
requirements: [REQ-01]
acceptance: []
documentation: []
checks: []
issue_refs: []
must_haves:
  truths: ["A behavior exists"]
  artifacts: []
  key_links: []
""" + extra + "---\n" + (body or """<tasks>
<task type="auto"><name>Add behavior</name><files>src/app.py</files>
<read_first>README.md</read_first><action>Implement behavior</action>
<verify>python -m unittest discover</verify><done>Behavior is observable</done></task>
</tasks>
""")
        path.write_text(content, encoding="utf-8")
        return path


class RecordBehavior(RuntimeCase):
    def test_phase_state_and_roadmap_stay_queryable(self):
        directory = self.phase()
        self.assertEqual("01", self.cli("find-phase", "1")["number"])
        self.cli("state.patch", '{"Phase":"01","Status":"Planning"}')
        self.assertEqual("Planning", self.cli("state.get", "status"))
        self.cli("phase.edit", "01", "--goal", "A revised goal")
        self.assertEqual("A revised goal", self.cli("roadmap.get-phase", "1")["goal"])

    def test_remove_archives_instead_of_deleting_artifacts(self):
        directory = self.phase()
        self.plan(directory)
        self.cli("phase.remove", "1", status=1, raw=True)
        result = self.cli("phase.remove", "1", "--force")
        self.assertTrue(Path(result["archive"]).joinpath("01-01-PLAN.md").exists())

    def test_quick_and_todo_records(self):
        quick = self.cli("quick.create", "Repair the login")
        self.cli("quick.update", quick["quick_id"], "--status", "complete")
        self.assertEqual("complete", self.cli("quick.get", quick["quick_id"])["status"])
        self.phase()
        todo = self.cli("todo.add", "Inspect a boundary", "--phase", "1")
        self.assertEqual(1, self.cli("todo.match-phase", "1")["count"])
        self.cli("todo.complete", todo["path"])
        self.assertEqual(0, self.cli("todo.list")["count"])


class IsolationSafety(RuntimeCase):
    def prepare_isolation(self):
        self.put(".gitignore", ".worktrees/\n")
        self.git("add", ".gitignore")
        self.git("commit", "-m", "chore: ignore worktrees")

    def test_session_refuses_unignored_root_and_reuses_owned_checkout(self):
        self.cli("session.open", "quick", "repair", status=1, raw=True)
        self.prepare_isolation()
        first = self.cli("session.open", "quick", "repair")
        second = self.cli("session.open", "quick", "repair")
        self.assertFalse(first["reused"])
        self.assertTrue(second["reused"])
        self.assertEqual(first["worktree"], second["worktree"])
        self.assertEqual(1, self.cli("session.status")["open_count"])

    def test_cleanup_requires_exact_preview_and_revalidates_dirty_resources(self):
        self.prepare_isolation()
        session = self.cli("session.open", "quick", "repair")
        # Offline provider evidence still runs real ownership, Git, token and
        # filesystem checks through the public CLI in each fresh process.
        driver = "import sys,runpy;sys.dont_write_bytecode=True;sys.path.insert(0,sys.argv.pop(1));from lib import cleanup;cleanup.provider_evidence=lambda *a,**k:{'offline':'closed'};runpy.run_path(sys.argv.pop(1),run_name='__main__')"
        def cleanup_cli(verb, *args, status=0):
            process = subprocess.run([sys.executable, "-I", "-c", driver, str(SOURCE/"engineer/bin"), str(RUNTIME), "query", verb, *map(str, args)], cwd=self.root, env=self.env, text=True, capture_output=True)
            self.assertEqual(status, process.returncode, process.stderr or process.stdout)
            return json.loads(process.stdout) if status == 0 else None
        preview = cleanup_cli("cleanup.preview")
        self.assertEqual(2, preview["count"])
        cleanup_cli("cleanup.apply", "--approval-token", preview["approval_token"], status=1)
        target = Path(session["worktree"])
        (target/"untracked.txt").write_text("keep", encoding="utf-8")
        cleanup_cli("cleanup.apply", "--approval-token", preview["approval_token"], "--confirm", status=1)
        self.assertTrue(target.exists())
        (target/"untracked.txt").unlink()
        preview = cleanup_cli("cleanup.preview")
        self.assertEqual(2, cleanup_cli("cleanup.apply", "--approval-token", preview["approval_token"], "--confirm")["count"])
        self.assertFalse(target.exists())
        cleanup_cli("cleanup.apply", "--approval-token", preview["approval_token"], "--confirm", status=1)

    def test_worker_undeclared_deletion_blocks_integration(self):
        self.prepare_isolation()
        worker = self.cli("worktree.create", "01-01", "--phase", "1", "--base", "HEAD", "--files", "src/app.py")
        target = Path(worker["path"])
        summary = target/".planning/phases/01-behavior/01-01-SUMMARY.md"
        summary.parent.mkdir(parents=True)
        summary.write_text('---\nphase: "01"\nplan: "01"\nstatus: complete\nrequirements-completed: []\nacceptance: []\ndocumentation: []\nissue_refs: []\n---\nDelivered\n', encoding="utf-8")
        (target/"README.md").unlink()
        self.git("-C", str(target), "add", "--all")
        self.git("-C", str(target), "commit", "-m", "feat(01-01): unexpected deletion")
        self.cli("worktree.merge-wave", "--phase", "1", status=1, raw=True)
        self.assertTrue((self.root/"README.md").exists())
        self.assertTrue(target.exists())

    def test_merge_requires_confirmation_and_fresh_evidence_before_provider(self):
        directory = Path(self.phase())
        (directory/"01-VERIFICATION.md").write_text('---\nphase: "01"\nstatus: passed\n---\nUnbound evidence\n', encoding="utf-8")
        self.cli("pr.merge", "worker", "--phase", "1", status=1, raw=True)
        self.cli("pr.merge", "worker", "--phase", "1", "--confirm", status=1, raw=True)


class PlanningReviewSafety(RuntimeCase):
    def test_repair_requires_fresh_exact_snapshot(self):
        self.put(".planning/STATE.md", "# Project State\n\n## Current Position\n\nPhase: 01\n\nLast session: 2026-01-01\nStopped at: Reviewed fixture\nResume file: None\n")
        preview = self.cli("planning.review")
        self.assertTrue(preview["repairable"])
        self.cli("planning.repair", "--apply", "--expect", "stale", status=1, raw=True)
        self.assertEqual(preview["snapshotDigest"], self.cli("planning.review")["snapshotDigest"])
        self.assertTrue(self.cli("planning.repair", "--apply", "--expect", preview["snapshotDigest"])["applied"])
        self.assertIn("## Session Continuity", (self.root/".planning/STATE.md").read_text())

    def test_exact_archive_previews_recover_without_overwriting(self):
        retired = self.put(".planning/todos/completed/old.md", "Retired completed record\n")
        preview = self.cli("planning.archive", "--paths", retired)
        self.assertTrue(retired.exists())
        self.cli("planning.archive", "--paths", retired, "--expect", "stale", "--confirm", status=1, raw=True)
        archived = self.cli("planning.archive", "--paths", retired, "--expect", preview["snapshotDigest"], "--confirm")
        self.assertFalse(retired.exists())
        self.assertEqual(1, self.cli("planning.archives")["count"])
        recovery = self.cli("planning.archive-recover", archived["recovery_id"])
        self.assertFalse(retired.exists())
        self.cli("planning.archive-recover", archived["recovery_id"], "--expect", recovery["recoveryDigest"], "--confirm")
        self.assertTrue(retired.exists())
