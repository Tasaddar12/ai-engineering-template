"""Standalone cleanup contracts using disposable repositories and offline providers."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                          text=True, encoding="utf-8", check=True).stdout.strip()


class CleanupTests(unittest.TestCase):
    """Only disposable repositories and offline provider fixtures can mutate."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cleanup cafÃ© ")
        self.addCleanup(self.temp.cleanup)
        # Establish a canonical disposable root before constructing any normal
        # fixture paths. Never resolve the alias operands in protection tests.
        self.temp_root = Path(self.temp.name).resolve()
        self.root = self.temp_root / "repo"
        self.root.mkdir()
        git(self.root, "init", "-q", "-b", "main")
        (self.root / "tracked").write_text("safe\n", encoding="utf-8")
        git(self.root, "add", "tracked")
        git(self.root, "-c", "user.name=Test", "-c", "user.email=t@example.invalid", "commit", "-qm", "fixture")
        git(self.root, "remote", "add", "origin", "https://github.com/owner/repo.git")
        self.tree = self.temp_root / "owned tree"
        git(self.root, "worktree", "add", "-qb", "phase-owned", str(self.tree))
        self.state = self.root / ".git/ai-phase"
        self.state.mkdir()
        self.owner = {"branch": "phase-owned", "worktree": str(self.tree), "base_branch": "main", "session_id": "fixture"}
        self.write_owner()
        self.provider, self.case = "github", "merged"
        spec = importlib.util.spec_from_file_location("cleanup_policy", ROOT / ".ai/runtime/lib/cleanup.py")
        self.policy = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.policy
        spec.loader.exec_module(self.policy)
        self.mutations = []

    def write_owner(self):
        (self.state / "sessions.json").write_text(json.dumps({"sessions": [self.owner]}), encoding="utf-8")

    def runner(self, argv, cwd):
        if argv[0] == "git":
            return subprocess.run(argv, cwd=cwd, text=True, encoding="utf-8", capture_output=True)
        oid = git(self.root, "rev-parse", "phase-owned")
        if self.case == "offline":
            raise OSError("fixture offline")
        if self.provider == "github":
            item = {"number": 42, "state": "open" if self.case == "open" else "closed",
                    "merged_at": "2026-01-01" if self.case == "merged" else None,
                    "head": {"ref": "phase-owned", "sha": oid, "repo": {"full_name": "owner/repo"}},
                    "base": {"repo": {"full_name": "owner/repo"}}}
            if self.case == "fork": item["head"]["repo"]["full_name"] = "fork/repo"
            if self.case == "recordless": item.pop("number")
            obj = [[item]]
            if self.case == "mixed": obj[0].append(dict(item, state="open"))
            if self.case == "partial": obj = [[item] * 100]
            if self.case == "missing": obj = [[]]
            if self.case == "pages":
                unrelated = dict(item, head=dict(item["head"], ref="unrelated"))
                obj = [[unrelated] * 100, [item]]
        elif "/merge_requests" not in argv[-1]:
            obj = {"id": 7, "path_with_namespace": "owner/repo", "web_url": "https://gitlab.com/owner/repo"}
        else:
            item = {"iid": 42, "state": "opened" if self.case == "open" else "merged" if self.case == "merged" else "closed",
                    "source_branch": "phase-owned", "sha": oid, "source_project_id": 7, "target_project_id": 7}
            if self.case == "fork": item["source_project_id"] = 8
            if self.case == "recordless": item.pop("iid")
            obj = [item]
            if self.case == "mixed": obj.append(dict(item, state="opened"))
            if self.case == "partial": obj = {"partial": True}
            if self.case == "missing": obj = []
            if self.case == "pages": obj = [dict(item, source_branch="unrelated")] * 100 + [item]
        return subprocess.CompletedProcess(argv, 0, json.dumps(obj), "")

    def preview(self):
        return self.policy.cleanup_preview(self.root, evidence_runner=self.runner)

    def envelope(self, preview=None):
        preview = preview or self.preview()
        return {"schema_version": 1, "repository": preview["repository"], "snapshot_id": preview["snapshot_id"],
                "operations": preview["operations"], "approval": {"text": "Approve exact cleanup snapshot " + preview["snapshot_id"],
                "reference": "human-message-fixture", "snapshot_id": preview["snapshot_id"]}}

    def apply(self, envelope, mutate=None):
        approval = self.temp_root / "approval.json"
        approval.write_text(json.dumps(envelope), encoding="utf-8")
        def mutation(argv, cwd):
            self.mutations.append(argv)
            if mutate: return mutate(argv, cwd)
            return subprocess.run(argv, cwd=cwd, text=True, encoding="utf-8", capture_output=True)
        return self.policy.cleanup_apply(self.root, approval, evidence_runner=self.runner, mutation_runner=mutation)

    def test_cleanup_preview_is_readonly_and_lists_distinct_operations(self):
        before = (git(self.root, "show-ref"), git(self.root, "worktree", "list", "--porcelain"), (self.state / "sessions.json").read_bytes())
        preview = self.preview()
        self.assertEqual(["worktree_remove", "branch_delete"], [x["kind"] for x in preview.get("operations", [])], preview)
        self.assertEqual(preview, self.preview())
        self.assertEqual(before, (git(self.root, "show-ref"), git(self.root, "worktree", "list", "--porcelain"), (self.state / "sessions.json").read_bytes()))
        self.assertFalse((self.state / "cleanup").exists())

    def test_cleanup_provider_matrix_preserves_open_unknown_fork_and_partial(self):
        for provider in ("github", "gitlab"):
            self.provider = provider
            git(self.root, "remote", "set-url", "origin", f"https://{provider}.com/owner/repo.git")
            for case in ("merged", "closed", "open", "offline", "fork", "partial", "missing", "mixed", "recordless", "pages"):
                with self.subTest(provider=provider, case=case):
                    self.case = case
                    preview = self.preview()
                    self.assertEqual(2 if case in ("merged", "closed", "pages") else 0, len(preview.get("operations", [])), preview)
        (self.tree / "tracked").write_text("unique\n", encoding="utf-8")
        git(self.tree, "add", "tracked")
        git(self.tree, "-c", "user.name=Test", "-c", "user.email=t@example.invalid", "commit", "-qm", "unique")
        for provider in ("github", "gitlab"):
            self.provider = provider
            git(self.root, "remote", "set-url", "origin", f"https://{provider}.com/owner/repo.git")
            for state in ("closed", "merged"):
                with self.subTest(provider=provider, unique_state=state):
                    self.case = state
                    self.assertEqual([], self.preview().get("operations", ["missing"]))

    def test_cleanup_dirty_ignored_unowned_locked_detached_preserved(self):
        for name in ("untracked", "ignored"):
            with self.subTest(name=name):
                if name == "ignored": (self.root / ".git/info/exclude").write_text("ignored\n", encoding="utf-8")
                (self.tree / name).write_text("valuable", encoding="utf-8")
                self.assertEqual([], self.preview().get("operations", ["missing"]))
                (self.tree / name).unlink()
        git(self.root, "worktree", "lock", str(self.tree))
        self.assertEqual([], self.preview().get("operations", ["missing"]))
        git(self.root, "worktree", "unlock", str(self.tree))
        self.owner["branch"] = "different"
        self.write_owner()
        self.assertEqual([], self.preview().get("operations", ["missing"]))

    def test_cleanup_exact_approval_and_stale_refuse_before_mutation(self):
        preview = self.preview()
        self.assertIn("snapshot_id", preview, preview)
        original = self.envelope(preview)
        import copy
        for variant in ("missing", "broad", "wildcard", "duplicate", "extra", "repository", "snapshot", "reference"):
            with self.subTest(variant=variant):
                envelope = copy.deepcopy(original)
                if variant == "missing": envelope["operations"].pop()
                if variant == "broad": envelope["approval"]["text"] = "yes delete everything"
                if variant == "wildcard": envelope["operations"][0]["target"] = "*"
                if variant == "duplicate": envelope["operations"].append(envelope["operations"][0])
                if variant == "extra": envelope["operations"].append({"kind": "backup_remove", "target": "/"})
                if variant == "repository": envelope["repository"]["common_dir"] += "-other"
                if variant == "snapshot": envelope["snapshot_id"] = "0" * 64
                if variant == "reference": envelope["approval"]["reference"] = ""
                self.assertEqual("refused", self.apply(envelope)["status"])
                self.assertEqual([], self.mutations)
        (self.tree / "new work").write_text("valuable", encoding="utf-8")
        self.assertEqual("refused", self.apply(original)["status"])
        self.assertEqual([], self.mutations)

    def test_cleanup_apply_consumes_once_and_reports_real_removal(self):
        preview = self.preview()
        self.assertIn("snapshot_id", preview, preview)
        envelope = self.envelope(preview)
        result = self.apply(envelope)
        self.assertEqual("complete", result["status"], result)
        self.assertEqual(2, len(result["removed"]), result)
        self.assertFalse(self.tree.exists())
        self.assertNotIn("refs/heads/phase-owned", git(self.root, "show-ref"))
        self.assertTrue(any(a[1:3] == ["update-ref", "-d"] and a[-1] == preview["operations"][1]["oid"] for a in self.mutations))
        self.assertFalse(any("--force" in a for a in self.mutations))
        self.assertEqual("refused", self.apply(envelope)["status"])

    def test_cleanup_partial_failure_stops_and_reports_fresh_state(self):
        preview = self.preview()
        self.assertIn("snapshot_id", preview, preview)
        def mutation(argv, cwd):
            if "update-ref" in argv: return subprocess.CompletedProcess(argv, 1, "", "fixture failure")
            return subprocess.run(argv, cwd=cwd, text=True, encoding="utf-8", capture_output=True)
        result = self.apply(self.envelope(preview), mutation)
        self.assertEqual("partial", result["status"], result)
        self.assertEqual(1, len(result["removed"]))
        self.assertEqual(1, len(result["failed"]))
        self.assertFalse(self.tree.exists())
        self.assertIn("refs/heads/phase-owned", git(self.root, "show-ref"))

    def test_cleanup_recorded_backup_digest_and_approval_boundary(self):
        backup = self.root / ".workflow-backups/fixture"
        backup.mkdir(parents=True)
        (backup / "valuable").write_text("original", encoding="utf-8")
        self.owner["backups"] = [str(backup)]
        self.write_owner()
        preview = self.preview()
        self.assertEqual(1, len([x for x in preview.get("operations", []) if x["kind"] == "backup_remove"]), preview)
        envelope = self.envelope(preview)
        (backup / "valuable").write_text("changed", encoding="utf-8")
        self.assertEqual("refused", self.apply(envelope)["status"])
        self.assertTrue(backup.exists())
        self.assertEqual([], self.mutations)
        result = self.apply(self.envelope())
        self.assertEqual("complete", result["status"], result)
        self.assertFalse(backup.exists())

    def test_cleanup_cli_source_and_installed_hosts(self):
        # CLI mode has no injected runner: an unsupported fixture host ensures
        # this wiring check cannot contact a real provider or need credentials.
        git(self.root, "remote", "set-url", "origin", "https://unsupported.example.invalid/owner/repo.git")
        for host in ("ai", "codex", "claude"):
            hook = ROOT / ".ai/hooks/cleanup.py"
            if host != "ai":
                shutil.copytree(ROOT / ".ai", self.root / ("." + host), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                hook = self.root / ("." + host) / "hooks/cleanup.py"
            result = subprocess.run([sys.executable, str(hook), "cleanup-preview", "--repo", str(self.root)], capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(1, json.loads(result.stdout).get("schema_version"))
            no_mode = subprocess.run([sys.executable, str(hook)], input=b"{}", capture_output=True)
            self.assertEqual(2, no_mode.returncode)
            self.assertEqual(b"", no_mode.stdout)
        invalid = subprocess.run([sys.executable, str(hook), "cleanup-apply", "--repo", str(self.root)], capture_output=True)
        self.assertNotEqual(0, invalid.returncode)


    def test_cleanup_apply_open_github_and_gitlab_stale_ownership_and_ref(self):
        for provider in ("github", "gitlab"):
            with self.subTest(provider=provider):
                self.provider = provider
                git(self.root, "remote", "set-url", "origin", f"https://{provider}.com/owner/repo.git")
                self.case = "merged"
                envelope = self.envelope()
                self.case = "open"
                self.assertEqual("refused", self.apply(envelope)["status"])
                self.assertEqual([], self.mutations)
        self.case = "merged"
        envelope = self.envelope()
        self.owner["session_id"] = "different-owner"
        self.write_owner()
        self.assertEqual("refused", self.apply(envelope)["status"])
        self.assertEqual([], self.mutations)
        envelope = self.envelope()
        (self.tree / "tracked").write_text("new tip\n", encoding="utf-8")
        git(self.tree, "add", "tracked")
        git(self.tree, "-c", "user.name=Test", "-c", "user.email=t@example.invalid", "commit", "-qm", "new tip")
        self.assertEqual("refused", self.apply(envelope)["status"])
        self.assertEqual([], self.mutations)

    def test_cleanup_common_dir_lock_preserves_existing_lock(self):
        envelope = self.envelope()
        storage = self.root / ".git/ai-cleanup"
        storage.mkdir()
        lock = storage / "lock"
        lock.write_text("other cleanup owns this", encoding="utf-8")
        self.assertEqual("refused", self.apply(envelope)["status"])
        self.assertEqual("other cleanup owns this", lock.read_text(encoding="utf-8"))
        self.assertEqual([], self.mutations)

    def test_cleanup_revalidates_before_each_item_and_truthful_success_readback(self):
        envelope = self.envelope()
        def mutation(argv, cwd):
            result = subprocess.run(argv, cwd=cwd, text=True, encoding="utf-8", capture_output=True)
            self.case = "open"
            return result
        result = self.apply(envelope, mutation)
        self.assertEqual("partial", result["status"], result)
        self.assertEqual(1, len(self.mutations))
        self.assertEqual(1, len(result["removed"]))
        self.assertTrue(result["final_state"][1]["exists"])
        self.case = "merged"
        # Fake success cannot fabricate branch removal.
        result = self.apply(self.envelope(), lambda argv, cwd: subprocess.CompletedProcess(argv, 0, "", ""))
        self.assertEqual("partial", result["status"], result)
        self.assertEqual([], result["removed"])
        self.assertTrue(result["final_state"][0]["exists"])

    def test_cleanup_backup_approval_file_ancestor_and_junction_preserved(self):
        backup = self.root / ".workflow-backups/owned"
        backup.mkdir(parents=True)
        (backup / "valuable").write_text("keep", encoding="utf-8")
        self.owner["backups"] = [str(backup)]
        self.write_owner()
        envelope = self.envelope()
        approval = backup / "approval.json"
        approval.write_text(json.dumps(envelope), encoding="utf-8")
        # Changed content is stale as well as approval-file ancestry unsafe.
        result = self.policy.cleanup_apply(self.root, approval, evidence_runner=self.runner)
        self.assertEqual("refused", result["status"])
        self.assertTrue((backup / "valuable").exists())
        approval.unlink()
        outside = self.temp_root / "outside"
        outside.mkdir()
        (outside / "valuable").write_text("keep outside", encoding="utf-8")
        link = backup / "alias"
        if os.name == "nt":
            result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr)
        else:
            link.symlink_to(outside, target_is_directory=True)
        preview = self.preview()
        self.assertFalse(any(op["kind"] == "backup_remove" for op in preview["operations"]), preview)
        self.assertTrue(any("symlink" in row["reason"] for row in preview["preserved"]), preview)
        # Remove only the temporary alias itself, never its referent.
        if os.name == "nt": link.rmdir()
        else: link.unlink()
        self.assertTrue((outside / "valuable").exists())

    def test_cleanup_detached_and_unrecorded_backups_are_preserved(self):
        detached = self.temp_root / "detached"
        git(self.root, "worktree", "add", "--detach", str(detached))
        backup = self.root / ".workflow-backups/unrecorded"
        backup.mkdir(parents=True)
        (backup / "valuable").write_text("keep", encoding="utf-8")
        preview = self.preview()
        self.assertTrue(any(row["reason"] == "detached-worktree" for row in preview["preserved"]))
        self.assertTrue(any(row["reason"] == "backup-unowned-or-ineligible" for row in preview["preserved"]))
        self.assertFalse(any(op["kind"] == "backup_remove" for op in preview["operations"]))

    def test_cleanup_raw_registered_junction_is_not_hidden_by_canonicalization(self):
        physical = self.temp_root / "physical tree"
        alias = self.tree
        # Git canonicalizes aliases supplied to worktree add. Replace an
        # already registered fixture directory to exercise the actual boundary.
        self.assertTrue(physical.is_relative_to(self.temp_root))
        self.assertTrue(alias.is_relative_to(self.temp_root))
        alias.rename(physical)
        if os.name == "nt":
            result = subprocess.run(["cmd", "/c", "mklink", "/J", str(alias), str(physical)], capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr)
        else:
            alias.symlink_to(physical, target_is_directory=True)
        try:
            with self.assertRaises(self.policy.EvidenceError):
                self.preview()
        finally:
            if os.name == "nt": alias.rmdir()
            else: alias.unlink()

    def repair_branch_only(self):
        git(self.root, "worktree", "remove", str(self.tree))
        return git(self.root, "rev-parse", "main")

    def repair_ref_output(self, name):
        result = subprocess.run(["git", "show-ref", "--verify", "--hash", name], cwd=self.root,
                                text=True, encoding="utf-8", capture_output=True)
        return result.stdout.strip() if result.returncode == 0 else None

    def test_cleanup_review_existing_symbolic_candidate_is_preserved(self):
        oid = self.repair_branch_only()
        git(self.root, "symbolic-ref", "refs/heads/phase-owned", "refs/heads/main")
        preview = self.preview()
        self.assertEqual([], preview["operations"], preview)
        self.assertTrue(any("symbolic" in row["reason"] for row in preview["preserved"]), preview)
        self.assertEqual(oid, self.repair_ref_output("refs/heads/main"))

    def test_cleanup_review_same_oid_symbolic_swap_is_stale_before_mutation(self):
        oid = self.repair_branch_only()
        preview = self.preview()
        envelope = self.envelope(preview)
        git(self.root, "symbolic-ref", "refs/heads/phase-owned", "refs/heads/main")
        result = self.apply(envelope)
        self.assertEqual("refused", result["status"], result)
        self.assertEqual([], self.mutations)
        self.assertEqual(oid, self.repair_ref_output("refs/heads/main"))

    def test_cleanup_review_mutation_time_symbolic_swap_never_deletes_referent(self):
        oid = self.repair_branch_only()
        envelope = self.envelope()
        def mutation(argv, cwd):
            if "update-ref" in argv:
                git(self.root, "symbolic-ref", "refs/heads/phase-owned", "refs/heads/main")
            return subprocess.run(argv, cwd=cwd, text=True, encoding="utf-8", capture_output=True)
        result = self.apply(envelope, mutation)
        self.assertEqual(oid, self.repair_ref_output("refs/heads/main"), result)
        if result["status"] == "complete":
            self.assertIsNone(self.repair_ref_output("refs/heads/phase-owned"), result)
        else:
            self.assertEqual("partial", result["status"], result)

    def test_cleanup_review_normal_direct_ref_deletion_control(self):
        oid = self.repair_branch_only()
        result = self.apply(self.envelope())
        self.assertEqual("complete", result["status"], result)
        self.assertEqual(1, len(result["removed"]), result)
        self.assertIsNone(self.repair_ref_output("refs/heads/phase-owned"))
        self.assertEqual(oid, self.repair_ref_output("refs/heads/main"))

    def test_cleanup_review_dangling_symbolic_readback_is_existing(self):
        oid = self.repair_branch_only()
        envelope = self.envelope()
        def mutation(argv, cwd):
            git(self.root, "symbolic-ref", "refs/heads/phase-owned", "refs/heads/absent-referent")
            return subprocess.CompletedProcess(argv, 0, "", "")
        result = self.apply(envelope, mutation)
        self.assertEqual("partial", result["status"], result)
        self.assertTrue(result["final_state"][0]["exists"], result)
        self.assertEqual("refs/heads/absent-referent", result["final_state"][0]["identity"]["target"])
        self.assertEqual(oid, self.repair_ref_output("refs/heads/main"))

    def test_cleanup_review_mutation_time_moved_oid_is_preserved(self):
        oid = self.repair_branch_only()
        tree = git(self.root, "rev-parse", "HEAD^{tree}")
        moved = git(self.root, "-c", "user.name=Test", "-c", "user.email=t@example.invalid",
                    "commit-tree", tree, "-p", oid, "-m", "moved fixture tip")
        envelope = self.envelope()
        def mutation(argv, cwd):
            if "update-ref" in argv:
                git(self.root, "update-ref", "refs/heads/phase-owned", moved, oid)
            return subprocess.run(argv, cwd=cwd, text=True, encoding="utf-8", capture_output=True)
        result = self.apply(envelope, mutation)
        self.assertEqual("partial", result["status"], result)
        self.assertEqual([], result["removed"])
        self.assertEqual(moved, self.repair_ref_output("refs/heads/phase-owned"))
        self.assertEqual(oid, self.repair_ref_output("refs/heads/main"))

    def test_cleanup_review_git_no_deref_compare_delete_semantics_control(self):
        oid = git(self.root, "rev-parse", "main")
        git(self.root, "branch", "phase-probe", oid)
        git(self.root, "update-ref", "--no-deref", "-d", "refs/heads/phase-probe", oid)
        self.assertIsNone(self.repair_ref_output("refs/heads/phase-probe"))
        git(self.root, "symbolic-ref", "refs/heads/phase-probe-alias", "refs/heads/main")
        git(self.root, "update-ref", "--no-deref", "-d", "refs/heads/phase-probe-alias", oid)
        self.assertIsNone(self.repair_ref_output("refs/heads/phase-probe-alias"))
        self.assertEqual(oid, self.repair_ref_output("refs/heads/main"))

    def repair_two_owned_fixture(self):
        self.other_tree = self.temp_root / "second owned tree"
        git(self.root, "worktree", "add", "-qb", "phase-z-other", str(self.other_tree))
        self.other_owner = {"branch": "phase-z-other", "worktree": str(self.other_tree),
                            "base_branch": "main", "session_id": "second-fixture"}
        backup = self.root / ".workflow-backups/group/owned"
        backup.mkdir(parents=True)
        (backup / "payload").write_text("approved backup", encoding="utf-8")
        self.owner["backups"] = [str(backup)]
        self.repair_write_two_owners()
        oid = git(self.root, "rev-parse", "main")
        self.other_provider_open = False
        def runner(argv, cwd):
            if argv[0] == "git":
                return subprocess.run(argv, cwd=cwd, text=True, encoding="utf-8", capture_output=True)
            # Provider records outlive local refs; pin both original heads.
            rows = [{"number": number, "state": "open" if branch == "phase-z-other" and self.other_provider_open else "closed",
                     "merged_at": "2026-01-01", "head": {"ref": branch, "sha": oid, "repo": {"full_name": "owner/repo"}},
                     "base": {"repo": {"full_name": "owner/repo"}}}
                    for number, branch in ((42, "phase-owned"), (43, "phase-z-other"))]
            return subprocess.CompletedProcess(argv, 0, json.dumps([rows]), "")
        self.runner = runner
        return backup

    def repair_write_two_owners(self):
        (self.state / "sessions.json").write_text(json.dumps({"sessions": [self.owner, self.other_owner]}), encoding="utf-8")

    def test_cleanup_review_nested_backup_two_owned_five_operations_complete(self):
        backup = self.repair_two_owned_fixture()
        preview = self.preview()
        self.assertEqual(5, len(preview["operations"]), preview)
        self.assertTrue(any(row["target"] == str(backup.parent) for row in preview["preserved"]), preview)
        result = self.apply(self.envelope(preview))
        self.assertEqual("complete", result["status"], result)
        self.assertEqual(5, len(result["removed"]), result)
        self.assertFalse(backup.exists())
        self.assertTrue(backup.parent.is_dir())
        self.assertTrue(any(row["target"] == str(backup.parent) and row["exists"]
                            for row in result["final_preserved"]), result)
        self.assertFalse(self.tree.exists())
        self.assertFalse(self.other_tree.exists())
        self.assertIsNone(self.repair_ref_output("refs/heads/phase-owned"))
        self.assertIsNone(self.repair_ref_output("refs/heads/phase-z-other"))
        self.assertTrue(self.repair_ref_output("refs/heads/main"))

    def test_cleanup_review_nested_backup_real_drift_controls(self):
        for drift in ("dirty", "provider-open", "ownership"):
            with self.subTest(drift=drift):
                # Each subcase owns an independent disposable repository.
                case = CleanupTests(methodName="test_cleanup_review_nested_backup_two_owned_five_operations_complete")
                case.setUp()
                try:
                    backup = case.repair_two_owned_fixture()
                    preview = case.preview()
                    def mutation(argv, cwd):
                        result = subprocess.run(argv, cwd=cwd, text=True, encoding="utf-8", capture_output=True)
                        if "update-ref" in argv and "refs/heads/phase-owned" in argv:
                            if drift == "dirty": (case.other_tree / "valuable").write_text("preserve", encoding="utf-8")
                            if drift == "provider-open": case.other_provider_open = True
                            if drift == "ownership":
                                case.other_owner["session_id"] = "changed-owner"
                                case.repair_write_two_owners()
                        return result
                    result = case.apply(case.envelope(preview), mutation)
                    self.assertEqual("partial", result["status"], result)
                    self.assertEqual(3, len(result["removed"]), result)
                    self.assertEqual(1, len(result["failed"]), result)
                    self.assertEqual("cleanup-state-stale", result["failed"][0]["reason"], result)
                    self.assertEqual(2, len(case.mutations), case.mutations)
                    self.assertFalse(backup.exists())
                    self.assertTrue(backup.parent.is_dir())
                    self.assertTrue(case.other_tree.is_dir())
                    self.assertTrue(case.repair_ref_output("refs/heads/phase-z-other"))
                finally:
                    case.doCleanups()

    def test_cleanup_review_unowned_backup_sibling_stops_before_second_tree(self):
        backup = self.repair_two_owned_fixture()
        envelope = self.envelope()
        unowned = self.root / ".workflow-backups/new-unowned"
        def mutation(argv, cwd):
            result = subprocess.run(argv, cwd=cwd, text=True, encoding="utf-8", capture_output=True)
            if "update-ref" in argv and "refs/heads/phase-owned" in argv:
                unowned.mkdir()
                (unowned / "valuable").write_text("preserve sibling", encoding="utf-8")
            return result
        result = self.apply(envelope, mutation)
        self.assertEqual("partial", result["status"], result)
        self.assertEqual(3, len(result["removed"]), result)
        self.assertEqual("cleanup-state-stale", result["failed"][0]["reason"], result)
        self.assertEqual(2, len(self.mutations), self.mutations)
        self.assertTrue(self.other_tree.is_dir())
        self.assertTrue(self.repair_ref_output("refs/heads/phase-z-other"))
        self.assertTrue((unowned / "valuable").is_file())
        self.assertTrue(backup.parent.is_dir())


if __name__ == "__main__":
    unittest.main()
