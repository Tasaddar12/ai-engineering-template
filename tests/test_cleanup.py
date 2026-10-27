"""Cleanup contracts against the standalone runtime, disposable Git and offline APIs.

The token protocol replaces the old approval-envelope hook. Every inherited case
still exercises its original destructive or preservation boundary through the
current public command, without loading or installing the retired runtime.
"""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"engineer/bin"))
from lib import cleanup, core, sessions
from lib.core import Args, Failure


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                          text=True, encoding="utf-8", check=True).stdout.strip()


class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cleanup unicode café ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()/"repo"
        self.root.mkdir()
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "config", "user.name", "Cleanup Fixture")
        git(self.root, "config", "user.email", "cleanup@example.invalid")
        (self.root/".gitignore").write_text(".worktrees/\n.workflow-backups/\n.planning/\nignored\n", encoding="utf-8")
        (self.root/"tracked").write_text("original\n", encoding="utf-8")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "fixture")
        git(self.root, "remote", "add", "origin", "https://github.com/owner/repo.git")
        self.head = git(self.root, "rev-parse", "HEAD")
        self.tree = self.root/".worktrees/owned tree"
        git(self.root, "worktree", "add", "-qb", "phase-owned", str(self.tree))
        self.state = self.root/".git/engineer"
        self.state.mkdir()
        self.owner = {"branch": "phase-owned", "worktree": str(self.tree), "base_branch": "main", "session_id": "fixture", "status": "open"}
        self.write_owner()
        self.case = "merged"
        self.other_provider_open = False
        self.mutations = []
        self.mutate = None
        environment = patch.dict(os.environ, {"ENGINEER_ROOT": str(self.root)})
        environment.start()
        self.addCleanup(environment.stop)
        runner = patch.object(cleanup, "run", side_effect=self.runner)
        runner.start()
        self.addCleanup(runner.stop)

    def write_owner(self):
        owners = [self.owner]+([self.other_owner] if hasattr(self, "other_owner") else [])
        (self.state/"sessions.json").write_text(json.dumps({"sessions": owners}), encoding="utf-8")

    def runner(self, argv, cwd=None, check=True, **options):
        if argv[0] == "git":
            destructive = argv[1:3] == ["worktree", "remove"] or argv[1:2] == ["update-ref"] and "-d" in argv
            if destructive:
                self.mutations.append(argv)
                if self.mutate:
                    result = self.mutate(argv, cwd)
                    if result is not None:
                        if check and result.returncode:
                            raise Failure("command-failed", "offline injected mutation failure")
                        return result
            return core.run(argv, cwd, check=check, **options)
        if self.case == "offline":
            return subprocess.CompletedProcess(argv, 1, "", "offline")
        endpoint = argv[-1]
        if endpoint.startswith("projects/") and "/merge_requests" not in endpoint:
            data = {"id": 7, "path_with_namespace": "owner/repo"}
        else:
            rows = []
            for number, branch in ((42, "phase-owned"), (43, "phase-z-other")):
                if number == 43 and not hasattr(self, "other_owner"):
                    continue
                opened = self.case == "open" or branch == "phase-z-other" and self.other_provider_open
                if "/merge_requests" in endpoint:
                    row = {"iid": number, "state": "opened" if opened else "merged" if self.case == "merged" else "closed", "source_branch": branch, "sha": self.head, "source_project_id": 7, "target_project_id": 7}
                    if self.case == "fork": row["source_project_id"] = 8
                    if self.case == "recordless": row.pop("iid")
                else:
                    row = {"number": number, "state": "open" if opened else "closed", "head": {"ref": branch, "sha": self.head, "repo": {"full_name": "owner/repo"}}, "base": {"repo": {"full_name": "owner/repo"}}}
                    if self.case == "fork": row["head"]["repo"]["full_name"] = "fork/repo"
                    if self.case == "recordless": row.pop("number")
                rows.append(row)
            if self.case == "missing": rows = []
            if self.case == "mixed":
                rows.append(dict(rows[0], state="opened" if "/merge_requests" in endpoint else "open"))
            page = int(parse_qs(urlparse(endpoint).query).get("page", ["1"])[0])
            if self.case == "partial": rows = {"partial": True}
            elif self.case == "pages" and page == 1:
                row = copy.deepcopy(rows[0])
                if "/merge_requests" in endpoint: row["source_branch"] = "unrelated"
                else: row["head"]["ref"] = "unrelated"
                rows = [row]*100
            data = rows
        return subprocess.CompletedProcess(argv, 0, json.dumps(data), "")

    def preview(self):
        return cleanup.command(Args([]), "preview")

    def apply(self, preview):
        return cleanup.command(Args(["--approval-token", preview["approval_token"], "--confirm"]), "apply")

    def refused(self, preview, code=None, removed=0):
        with self.assertRaises(Failure) as caught:
            self.apply(preview)
        if code: self.assertEqual(caught.exception.code, code)
        self.assertEqual(len(caught.exception.details.get("removed", [])), removed)
        return caught.exception

    def assert_posix_backup_refused(self, preview, backup):
        self.refused(preview, "cleanup-backup-unsupported")
        self.assertEqual("approved original", (backup/"valuable").read_text())
        self.assertTrue(self.tree.is_dir())
        self.assertEqual(self.head, self.repair_ref_output("refs/heads/phase-owned"))
        if hasattr(self, "other_tree"):
            self.assertTrue(self.other_tree.is_dir())
            self.assertEqual(self.head, self.repair_ref_output("refs/heads/phase-z-other"))
        self.assertEqual([], self.mutations)

    def backup(self, name="group/owned"):
        path = self.root/".workflow-backups"/name
        path.mkdir(parents=True)
        (path/"valuable").write_text("approved original", encoding="utf-8")
        self.owner["backups"] = [str(path)]
        self.write_owner()
        return path

    def test_cleanup_preview_is_readonly_and_lists_distinct_operations(self):
        before = (git(self.root, "show-ref"), git(self.root, "worktree", "list", "--porcelain"), (self.state/"sessions.json").read_bytes())
        first, second = self.preview(), self.preview()
        self.assertEqual(["worktree_remove", "branch_delete"], [entry["kind"] for entry in first["entries"]])
        self.assertEqual(first["entries"], second["entries"])
        self.assertNotEqual(first["approval_token"], second["approval_token"])
        self.assertEqual(before, (git(self.root, "show-ref"), git(self.root, "worktree", "list", "--porcelain"), (self.state/"sessions.json").read_bytes()))
        self.assertEqual([], self.mutations)

    def test_cleanup_provider_matrix_preserves_open_unknown_fork_and_partial(self):
        for provider in ("github", "gitlab"):
            git(self.root, "remote", "set-url", "origin", f"https://{provider}.com/owner/repo.git")
            for case in ("merged", "closed", "open", "offline", "fork", "partial", "missing", "mixed", "recordless", "pages"):
                with self.subTest(provider=provider, case=case):
                    self.case = case
                    self.assertEqual(2 if case in ("merged", "closed", "pages") else 0, self.preview()["count"])
        (self.tree/"tracked").write_text("unique\n")
        git(self.tree, "add", ".")
        git(self.tree, "commit", "-qm", "unmerged")
        self.head = git(self.tree, "rev-parse", "HEAD")
        for case in ("merged", "closed"):
            self.case = case
            self.assertEqual(0, self.preview()["count"])

    def test_cleanup_dirty_ignored_unowned_locked_detached_preserved(self):
        for name in ("untracked", "ignored"):
            (self.tree/name).write_text("valuable")
            self.assertEqual(0, self.preview()["count"])
            (self.tree/name).unlink()
        git(self.root, "worktree", "lock", str(self.tree))
        self.assertEqual(0, self.preview()["count"])
        git(self.root, "worktree", "unlock", str(self.tree))
        self.owner["branch"] = "unowned"
        self.write_owner()
        self.assertEqual(0, self.preview()["count"])

    def test_cleanup_exact_approval_and_stale_refuse_before_mutation(self):
        preview = self.preview()
        stored = self.root/".planning/cleanup"/(preview["approval_token"]+".json")
        original = stored.read_bytes()
        for change in ("missing", "duplicate", "extra", "path", "owner", "head", "nonce", "inventory"):
            data = json.loads(original)
            if change == "missing": data["entries"].pop()
            if change == "duplicate": data["entries"].append(data["entries"][0])
            if change == "extra": data["entries"].append({"kind": "backup", "path": "/"})
            if change == "path": data["entries"][0]["path"] = "*"
            if change == "owner": data["entries"][0]["owner"]["record"]["session_id"] = "another"
            if change == "head": data["entries"][0]["head"] = "0"*40
            if change == "nonce": data["nonce"] = "changed"
            if change == "inventory": data["backup_inventory"] = [{"path": "extra"}]
            stored.write_text(json.dumps(data))
            self.refused(preview, "cleanup-preview-corrupt")
            self.assertEqual([], self.mutations)
        stored.write_bytes(original)
        with self.assertRaises(Failure): cleanup.command(Args([preview["approval_token"]]), "apply")
        (self.tree/"new work").write_text("valuable")
        self.refused(preview, "cleanup-dirty-resource")
        self.assertEqual([], self.mutations)

    def test_cleanup_apply_consumes_once_and_reports_real_removal(self):
        preview = self.preview()
        result = self.apply(preview)
        self.assertEqual(2, result["count"])
        self.assertFalse(self.tree.exists())
        self.assertIsNone(self.repair_ref_output("refs/heads/phase-owned"))
        self.assertTrue(any("--no-deref" in call and call[-1] == self.head for call in self.mutations))
        self.assertFalse(any("--force" in call for call in self.mutations))
        self.refused(preview, "cleanup-preview-missing")

    def test_cleanup_partial_failure_stops_and_reports_fresh_state(self):
        self.mutate = lambda argv, cwd: subprocess.CompletedProcess(argv, 1, "", "failure") if "update-ref" in argv else None
        self.refused(self.preview(), "command-failed", removed=1)
        self.assertFalse(self.tree.exists())
        self.assertEqual(self.head, self.repair_ref_output("refs/heads/phase-owned"))

    def test_cleanup_recorded_backup_digest_and_approval_boundary(self):
        backup = self.backup()
        preview = self.preview()
        self.assertEqual(1, len([entry for entry in preview["entries"] if entry["kind"] == "backup"]))
        (backup/"valuable").write_text("changed")
        self.refused(preview, "cleanup-backup-drift")
        self.assertTrue(backup.exists())
        self.assertEqual([], self.mutations)
        if os.name != "nt":
            preview = self.preview()
            self.refused(preview, "cleanup-backup-unsupported")
            self.assertEqual("changed", (backup/"valuable").read_text())
            self.assertTrue(self.tree.is_dir())
            self.assertEqual(self.head, self.repair_ref_output("refs/heads/phase-owned"))
            self.assertEqual([], self.mutations)
            return
        self.assertEqual(3, self.apply(self.preview())["count"])
        self.assertFalse(backup.exists())
        self.assertTrue(backup.parent.is_dir())

    def test_cleanup_cli_source_and_installed_hosts(self):
        # Invoke the standalone source CLI with a provider executable seam in a
        # separate Python process; both supported host selections use that CLI.
        driver = "import os,sys,runpy;sys.path.insert(0,sys.argv.pop(1));from lib import cleanup;cleanup.provider_evidence=lambda *a,**k:{'offline':'closed'};runpy.run_path(sys.argv.pop(1),run_name='__main__')"
        for host in ("codex", "claude"):
            environment = dict(os.environ, ENGINEER_HOST=host, ENGINEER_ROOT=str(self.root))
            result = subprocess.run([sys.executable, "-c", driver, str(ROOT/"engineer/bin"), str(ROOT/"engineer/bin/engineer.py"), "query", "cleanup.preview"], cwd=self.root, env=environment, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(2, json.loads(result.stdout)["count"])
        result = subprocess.run([sys.executable, str(ROOT/"engineer/bin/engineer.py"), "query", "cleanup.apply"], cwd=self.root, capture_output=True, text=True)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("cleanup-not-approved", result.stderr)

    def test_cleanup_apply_open_github_and_gitlab_stale_ownership_and_ref(self):
        for provider in ("github", "gitlab"):
            git(self.root, "remote", "set-url", "origin", f"https://{provider}.com/owner/repo.git")
            self.case = "merged"
            preview = self.preview()
            self.case = "open"
            self.refused(preview)
            self.assertEqual([], self.mutations)
        self.case = "merged"
        preview = self.preview()
        self.owner["session_id"] = "changed"
        self.write_owner()
        self.refused(preview, "cleanup-owner-drift")
        preview = self.preview()
        (self.tree/"tracked").write_text("new tip")
        git(self.tree, "add", ".")
        git(self.tree, "commit", "-qm", "new tip")
        self.refused(preview, "cleanup-head-drift")
        self.assertEqual([], self.mutations)

    def test_cleanup_common_dir_lock_preserves_existing_lock(self):
        preview = self.preview()
        lock = self.state/"resources.lock"
        lock.write_text("other owner")
        with patch.object(sessions.time, "monotonic", side_effect=[0, 11]):
            self.refused(preview, "resources-locked")
        self.assertEqual("other owner", lock.read_text())
        self.assertEqual([], self.mutations)

    def test_cleanup_revalidates_before_each_item_and_truthful_success_readback(self):
        def mutate(argv, cwd):
            result = core.run(argv, cwd)
            self.case = "open"
            return result
        self.mutate = mutate
        self.refused(self.preview(), removed=1)
        self.assertEqual(1, len(self.mutations))
        self.assertEqual(self.head, self.repair_ref_output("refs/heads/phase-owned"))
        self.case = "merged"
        self.mutate = lambda argv, cwd: subprocess.CompletedProcess(argv, 0, "", "")
        self.refused(self.preview(), "cleanup-removal-unconfirmed")
        self.assertEqual(self.head, self.repair_ref_output("refs/heads/phase-owned"))

    def test_cleanup_backup_approval_file_ancestor_and_junction_preserved(self):
        backup = self.backup()
        preview = self.preview()
        (backup/"approval.json").write_text(json.dumps(preview))
        self.refused(preview, "cleanup-backup-drift")
        (backup/"approval.json").unlink()
        outside = self.root.parent/"outside"
        outside.mkdir()
        (outside/"valuable").write_text("keep outside")
        alias = backup/"alias"
        self.make_alias(alias, outside)
        try:
            self.assertFalse(any(entry["kind"] == "backup" for entry in self.preview()["entries"]))
            self.assertTrue((outside/"valuable").is_file())
        finally:
            self.remove_alias(alias)

    def test_cleanup_detached_and_unrecorded_backups_are_preserved(self):
        detached = self.root/".worktrees/detached"
        git(self.root, "worktree", "add", "--detach", str(detached))
        backup = self.root/".workflow-backups/unrecorded"
        backup.mkdir(parents=True)
        (backup/"valuable").write_text("preserve")
        result = self.apply(self.preview())
        self.assertEqual(2, result["count"])
        self.assertTrue(detached.is_dir())
        self.assertTrue((backup/"valuable").is_file())

    def make_alias(self, alias, physical):
        if os.name == "nt":
            result = subprocess.run(["cmd", "/c", "mklink", "/J", str(alias), str(physical)], capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr)
        else:
            alias.symlink_to(physical, target_is_directory=True)

    def remove_alias(self, alias):
        if os.name == "nt": alias.rmdir()
        else: alias.unlink()

    def test_cleanup_raw_registered_junction_is_not_hidden_by_canonicalization(self):
        physical = self.root/".worktrees/physical"
        self.tree.rename(physical)
        self.make_alias(self.tree, physical)
        try:
            self.assertEqual(0, self.preview()["count"])
            self.assertTrue((physical/"tracked").exists())
        finally:
            self.remove_alias(self.tree)
            physical.rename(self.tree)

    def repair_branch_only(self):
        git(self.root, "worktree", "remove", str(self.tree))
        return self.head

    def repair_ref_output(self, name):
        result = subprocess.run(["git", "show-ref", "--verify", "--hash", name], cwd=self.root, capture_output=True, text=True)
        return result.stdout.strip() if not result.returncode else None

    def test_cleanup_review_existing_symbolic_candidate_is_preserved(self):
        self.repair_branch_only()
        git(self.root, "symbolic-ref", "refs/heads/phase-owned", "refs/heads/main")
        self.assertEqual(0, self.preview()["count"])
        self.assertEqual(self.head, self.repair_ref_output("refs/heads/main"))

    def test_cleanup_review_same_oid_symbolic_swap_is_stale_before_mutation(self):
        self.repair_branch_only()
        preview = self.preview()
        git(self.root, "symbolic-ref", "refs/heads/phase-owned", "refs/heads/main")
        self.refused(preview, "cleanup-symbolic-ref")
        self.assertEqual([], self.mutations)
        self.assertEqual(self.head, self.repair_ref_output("refs/heads/main"))

    def test_cleanup_review_mutation_time_symbolic_swap_never_deletes_referent(self):
        self.repair_branch_only()
        def mutate(argv, cwd):
            git(self.root, "symbolic-ref", "refs/heads/phase-owned", "refs/heads/main")
            return core.run(argv, cwd, check=False)
        self.mutate = mutate
        preview = self.preview()
        try:
            result = self.apply(preview)
            self.assertEqual(1, result["count"])
            self.assertIsNone(self.repair_ref_output("refs/heads/phase-owned"))
        except Failure:
            self.assertTrue((self.root/".git/refs/heads/phase-owned").exists())
        self.assertEqual(self.head, self.repair_ref_output("refs/heads/main"))

    def test_cleanup_review_normal_direct_ref_deletion_control(self):
        self.repair_branch_only()
        self.assertEqual(1, self.apply(self.preview())["count"])
        self.assertIsNone(self.repair_ref_output("refs/heads/phase-owned"))
        self.assertEqual(self.head, self.repair_ref_output("refs/heads/main"))

    def test_cleanup_review_dangling_symbolic_readback_is_existing(self):
        self.repair_branch_only()
        def mutate(argv, cwd):
            git(self.root, "symbolic-ref", "refs/heads/phase-owned", "refs/heads/absent")
            return subprocess.CompletedProcess(argv, 0, "", "")
        self.mutate = mutate
        self.refused(self.preview(), "cleanup-removal-unconfirmed")
        self.assertEqual("refs/heads/absent", git(self.root, "symbolic-ref", "refs/heads/phase-owned"))
        self.assertEqual(self.head, self.repair_ref_output("refs/heads/main"))

    def test_cleanup_review_mutation_time_moved_oid_is_preserved(self):
        self.repair_branch_only()
        moved = git(self.root, "commit-tree", git(self.root, "rev-parse", "HEAD^{tree}"), "-p", self.head, "-m", "moved")
        def mutate(argv, cwd):
            git(self.root, "update-ref", "refs/heads/phase-owned", moved, self.head)
            return core.run(argv, cwd, check=False)
        self.mutate = mutate
        self.refused(self.preview(), "command-failed")
        self.assertEqual(moved, self.repair_ref_output("refs/heads/phase-owned"))
        self.assertEqual(self.head, self.repair_ref_output("refs/heads/main"))

    def test_cleanup_review_git_no_deref_compare_delete_semantics_control(self):
        for name in ("phase-probe", "phase-probe-alias"):
            if name.endswith("alias"): git(self.root, "symbolic-ref", "refs/heads/"+name, "refs/heads/main")
            else: git(self.root, "branch", name, self.head)
            git(self.root, "update-ref", "--no-deref", "-d", "refs/heads/"+name, self.head)
            self.assertIsNone(self.repair_ref_output("refs/heads/"+name))
            self.assertEqual(self.head, self.repair_ref_output("refs/heads/main"))

    def repair_two_owned_fixture(self):
        self.other_tree = self.root/".worktrees/second owned tree"
        git(self.root, "worktree", "add", "-qb", "phase-z-other", str(self.other_tree))
        self.other_owner = {"branch": "phase-z-other", "worktree": str(self.other_tree), "base_branch": "main", "session_id": "second", "status": "open"}
        return self.backup()

    def test_cleanup_review_nested_backup_two_owned_five_operations_complete(self):
        backup = self.repair_two_owned_fixture()
        preview = self.preview()
        self.assertEqual(5, preview["count"])
        if os.name != "nt":
            self.assert_posix_backup_refused(preview, backup)
            return
        self.assertEqual(5, self.apply(preview)["count"])
        self.assertFalse(backup.exists())
        self.assertTrue(backup.parent.is_dir())
        self.assertFalse(self.tree.exists())
        self.assertFalse(self.other_tree.exists())
        self.assertIsNone(self.repair_ref_output("refs/heads/phase-owned"))
        self.assertIsNone(self.repair_ref_output("refs/heads/phase-z-other"))
        self.assertEqual(self.head, self.repair_ref_output("refs/heads/main"))

    def test_cleanup_review_nested_backup_real_drift_controls(self):
        for drift in ("dirty", "provider-open", "ownership"):
            case = CleanupTests()
            case.setUp()
            try:
                backup = case.repair_two_owned_fixture()
                def mutate(argv, cwd):
                    result = core.run(argv, cwd)
                    if "update-ref" in argv and "refs/heads/phase-owned" in argv:
                        if drift == "dirty": (case.other_tree/"valuable").write_text("preserve")
                        if drift == "provider-open": case.other_provider_open = True
                        if drift == "ownership":
                            case.other_owner["session_id"] = "changed"
                            case.write_owner()
                    return result
                case.mutate = mutate
                if os.name != "nt":
                    case.assert_posix_backup_refused(case.preview(), backup)
                    continue
                case.refused(case.preview(), removed=3)
                self.assertEqual(2, len(case.mutations))
                self.assertFalse(backup.exists())
                self.assertTrue(backup.parent.is_dir())
                self.assertTrue(case.other_tree.is_dir())
                self.assertEqual(case.head, case.repair_ref_output("refs/heads/phase-z-other"))
            finally:
                case.doCleanups()

    def test_cleanup_review_unowned_backup_sibling_stops_before_second_tree(self):
        backup = self.repair_two_owned_fixture()
        unowned = self.root/".workflow-backups/new-unowned"
        def mutate(argv, cwd):
            result = core.run(argv, cwd)
            if "update-ref" in argv and "refs/heads/phase-owned" in argv:
                unowned.mkdir()
                (unowned/"valuable").write_text("preserve")
            return result
        self.mutate = mutate
        if os.name != "nt":
            self.assert_posix_backup_refused(self.preview(), backup)
            self.assertFalse(unowned.exists())
            return
        self.refused(self.preview(), "cleanup-backup-drift", removed=3)
        self.assertEqual(2, len(self.mutations))
        self.assertTrue(self.other_tree.is_dir())
        self.assertEqual(self.head, self.repair_ref_output("refs/heads/phase-z-other"))
        self.assertTrue((unowned/"valuable").is_file())
        self.assertTrue(backup.parent.is_dir())

    def test_backup_overlapping_ownership_and_content_race_preserve_unapproved_nodes(self):
        backup = self.backup()
        self.owner["backups"].append(str(backup.parent))
        self.write_owner()
        self.assertFalse(any(entry["kind"] == "backup" for entry in self.preview()["entries"]))
        self.owner["backups"] = [str(backup)]
        self.write_owner()
        preview = self.preview()
        validate = cleanup.validate_backup
        calls = []
        def race(entry, *args, **options):
            result = validate(entry, *args, **options)
            calls.append(entry)
            if len(calls) == 1:
                (backup/"new valuable").write_text("new unapproved content")
            return result
        with patch.object(cleanup, "validate_backup", side_effect=race):
            with self.assertRaises(Failure): self.apply(preview)
        self.assertTrue((backup/"new valuable").is_file())
        self.assertTrue(self.tree.is_dir())

    @unittest.skipIf(os.name == "nt", "Native POSIX replacement boundary")
    def test_posix_backup_deletion_preserves_replacement_after_final_read(self):
        backup = self.backup()
        entry = next(item for item in self.preview()["entries"] if item["kind"] == "backup")
        validate = cleanup.validate_backup
        replacement = backup/"valuable"
        def replace_after_validation(value, *args, **kwargs):
            result = validate(value, *args, **kwargs)
            replacement.unlink()
            replacement.write_text("unapproved replacement", encoding="utf-8")
            return result
        with patch.object(cleanup, "validate_backup", side_effect=replace_after_validation):
            with self.assertRaises(Failure) as raised:
                cleanup.remove_backup_nodes(entry)
        self.assertEqual("cleanup-backup-unsupported", raised.exception.code)
        self.assertEqual("unapproved replacement", replacement.read_text())
        self.assertTrue(backup.is_dir())

    def test_windows_pinned_backup_handles_block_rename_write_and_report_delete_failure(self):
        backup = self.backup()
        entry = next(entry for entry in self.preview()["entries"] if entry["kind"] == "backup")
        if os.name == "nt":
            with cleanup.windows_backup_handles(entry):
                with self.assertRaises(OSError): backup.rename(backup.with_name("moved"))
                with self.assertRaises(OSError): (backup/"valuable").write_text("unapproved replacement")
            preview = self.preview()
            with patch.object(cleanup, "delete_windows_backup_handle", side_effect=Failure("cleanup-backup-removal-failed", "injected native disposition failure")):
                self.refused(preview, "cleanup-backup-removal-failed")
            self.assertEqual("approved original", (backup/"valuable").read_text())
            self.assertTrue(self.tree.is_dir())
        else:
            # Portable hosts still exercise the exact stale-content refusal;
            # they do not claim to have executed Windows handle semantics.
            preview = self.preview()
            (backup/"valuable").write_text("unapproved replacement")
            self.refused(preview, "cleanup-backup-drift")
            self.assertEqual("unapproved replacement", (backup/"valuable").read_text())


class CurrentCleanupGuards(CleanupTests):
    # Inherit the same real fixture, never a second runtime implementation.
    def test_exact_token_removes_only_integrated_owned_resource_once(self):
        preview = self.preview()
        self.assertEqual(2, preview["count"])
        self.assertEqual(2, self.apply(preview)["count"])
        self.assertFalse(self.tree.exists())
        self.refused(preview, "cleanup-preview-missing")

    def test_changed_ownership_or_ignored_content_preserves_actual_files(self):
        preview = self.preview()
        self.owner["plan"] = "changed-owner"
        self.write_owner()
        self.refused(preview, "cleanup-owner-drift")
        (self.tree/"ignored").write_text("keep")
        self.assertEqual(0, self.preview()["count"])
        self.assertTrue(self.tree.exists())

    def test_symbolic_swap_never_deletes_referent(self):
        preview = self.preview()
        git(self.root, "branch", "valuable", self.head)
        git(self.root, "symbolic-ref", "refs/heads/phase-owned", "refs/heads/valuable")
        self.refused(preview, "cleanup-symbolic-ref")
        self.assertEqual(self.head, self.repair_ref_output("refs/heads/valuable"))
        self.assertTrue(self.tree.exists())

    def test_unmerged_manifest_never_becomes_eligible_from_shared_base(self):
        (self.state/"sessions.json").write_text(json.dumps({"sessions": []}))
        manifest = self.root/".planning/worktrees/fixture.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({"workers": [{"path": str(self.tree), "branch": "phase-owned", "merged": False, "head": self.head}]}))
        self.assertEqual(0, self.preview()["count"])
        self.assertTrue(self.tree.exists())


if __name__ == "__main__":
    unittest.main()

