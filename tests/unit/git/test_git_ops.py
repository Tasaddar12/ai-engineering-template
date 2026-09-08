from __future__ import annotations

import dataclasses
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from commands import FileCommandLogStore, LocalCommandRunner
from config import RunSettings, load_installation_record, load_project_settings
from domain_values import CommandStatus, EntityId, ErrorCategory, PlanId, ResultStatus
from git_ops import (
    FileContentReader,
    GitRuntimeBinding,
    LocalGitRepository,
    ManagedIntegrationBinding,
)
from local_ports import (
    AncestryQuery,
    AncestryStatus,
    BranchRequest,
    CommandEvidence,
    GitHeadStatus,
    GitInspectRequest,
    GitRefExpectation,
    GitRefQuery,
    GitRefStatus,
    LocalProjectBinding,
    LocalWorktreeBinding,
    MergeRequest,
    PermissionClass,
)


GIT = shutil.which("git")
if GIT is None:
    raise RuntimeError("actual Git is required for TASK-007 tests")


class _Clock:
    def __init__(self) -> None:
        self._value = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self._lock = threading.Lock()

    def now(self) -> datetime:
        with self._lock:
            self._value += timedelta(microseconds=1)
            return self._value


class _Ids:
    def __init__(self) -> None:
        self._value = 0
        self._lock = threading.Lock()

    def new(self, kind: str, plan_id: PlanId | None = None) -> EntityId:
        with self._lock:
            self._value += 1
            return EntityId(f"git-test-evidence-{self._value}")


class _FailingReader:
    def read(self, reference):
        raise OSError("injected digest mismatch")


class _InterceptRunner:
    def __init__(self, runner: LocalCommandRunner, mode: str, worktree: Path | None = None, before_publish=None) -> None:
        self.runner = runner
        self.mode = mode
        self.worktree = worktree
        self.last: CommandEvidence | None = None
        self.publish_calls = 0
        self.read_tree_calls = 0
        self.before_publish = before_publish

    def execute(self, request):
        argv = request.definition.argv
        is_helper = "--git-ops-helper-v1" in argv
        is_publish = is_helper and _payload_action(argv[-1]).startswith("publish_")
        is_read_tree = "read-tree" in argv
        if is_publish:
            self.publish_calls += 1
            if self.before_publish is not None:
                callback, self.before_publish = self.before_publish, None
                callback()
            if self.mode == "unknown-before-publish":
                assert self.last is not None
                return dataclasses.replace(
                    self.last,
                    command_id=request.definition.id,
                    argv_redacted=request.definition.argv,
                    status=CommandStatus.UNKNOWN,
                    exit_code=None,
                    error_category=ErrorCategory.AMBIGUOUS_SIDE_EFFECT.value,
                )
            result = self.runner.execute(request)
            self.last = result
            if self.mode == "unknown-after-publish":
                return dataclasses.replace(
                    result,
                    status=CommandStatus.UNKNOWN,
                    exit_code=None,
                    error_category=ErrorCategory.AMBIGUOUS_SIDE_EFFECT.value,
                )
            if self.mode == "dirty-after-publish":
                assert self.worktree is not None
                (self.worktree / "base.txt").write_text("developer change\n", encoding="utf-8")
            if self.mode == "index-after-publish":
                assert self.worktree is not None
                (self.worktree / "base.txt").write_text("staged concurrent change\n", encoding="utf-8")
                subprocess.run((GIT, "add", "--", "base.txt"), cwd=self.worktree, shell=False, check=True)
            return result
        if is_read_tree:
            self.read_tree_calls += 1
            if self.mode == "unknown-before-read-tree":
                assert self.last is not None
                return dataclasses.replace(
                    self.last,
                    command_id=request.definition.id,
                    argv_redacted=request.definition.argv,
                    status=CommandStatus.UNKNOWN,
                    exit_code=None,
                    error_category=ErrorCategory.AMBIGUOUS_SIDE_EFFECT.value,
                )
        result = self.runner.execute(request)
        self.last = result
        return result


def _payload_action(encoded: str) -> str:
    import base64
    import json

    return json.loads(base64.urlsafe_b64decode(encoded).decode("utf-8"))["action"]


class GitFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="task-007-")
        self.repo = Path(self.temporary.name).resolve()
        self.empty_config = self.repo / ".git" / "empty-git-config"
        self.environment = {
            "PATH": os.pathsep.join((str(Path(sys.executable).parent), str(Path(GIT).parent))),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(self.empty_config),
            "GIT_AUTHOR_NAME": "TASK-007 Fixture",
            "GIT_AUTHOR_EMAIL": "task-007@example.invalid",
            "GIT_COMMITTER_NAME": "TASK-007 Fixture",
            "GIT_COMMITTER_EMAIL": "task-007@example.invalid",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        if os.name == "nt":
            self.environment["SystemRoot"] = os.environ["SystemRoot"]
        self.git("init", "-b", "main")
        self.empty_config.write_text("", encoding="utf-8")
        (self.repo / "base.txt").write_text("base\n", encoding="utf-8")
        self.git("add", "--", "base.txt")
        self.git("commit", "-m", "base")
        self.base = self.git("rev-parse", "HEAD").strip()
        self.project = LocalProjectBinding(EntityId("project-test"), self.repo)
        self.clock = _Clock()
        self.runner = self.make_runner()
        self.repository = self.make_repository(self.runner)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *args: str, cwd: Path | None = None, check: bool = True) -> str:
        completed = subprocess.run(
            (GIT, *args), cwd=cwd or self.repo, env=self.environment,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, check=False,
        )
        if check and completed.returncode != 0:
            self.fail(f"git {args!r} failed: {completed.stderr.decode(errors='replace')}")
        return completed.stdout.decode("utf-8", "surrogateescape")

    def make_runner(self) -> LocalCommandRunner:
        settings = dataclasses.replace(
            load_project_settings(ROOT, load_installation_record(ROOT)),
            project_root=self.repo,
        )
        return LocalCommandRunner(
            project_settings=settings,
            run_settings=RunSettings(),
            allowed_permissions=(PermissionClass.LOCAL_READ, PermissionClass.LOCAL_EXECUTE),
            id_factory=_Ids(), clock=self.clock,
            log_store=FileCommandLogStore(self.repo, ".git/task-007-logs"),
            base_environment=self.environment,
        )

    def make_repository(self, runner, managed=()):
        return LocalGitRepository(
            project=self.project,
            command_runner=runner,
            clock=self.clock,
            content_reader=FileContentReader(self.repo),
            runtime=GitRuntimeBinding(sys.executable, GIT, ROOT / "src"),
            managed_integrations=tuple(managed),
        )

    def inspect(self, **changes):
        values = dict(
            project_id=self.project.project_id,
            run_id=EntityId("run-inspect"),
            target=self.project,
        )
        values.update(changes)
        return self.repository.inspect(GitInspectRequest(**values))

    def branch_request(self, *, operation="op-branch", source="refs/heads/main", source_oid=None, branch="topic", expected=None):
        return BranchRequest(
            project_id=self.project.project_id, plan_id=None,
            run_id=EntityId("run-branch"), operation_id=EntityId(operation),
            idempotency_key="branch-key", repository=self.project,
            branch=branch, source_ref=source,
            expected_base_oid=source_oid or self.base,
            expected_branch=expected or GitRefExpectation(f"refs/heads/{branch}", GitRefStatus.MISSING),
        )

    def merge_request(self, *, operation="op-merge", candidate="refs/heads/candidate", candidate_oid=None, integration="integration", expected=None):
        return MergeRequest(
            project_id=self.project.project_id, plan_id=PlanId("PLAN-001"),
            run_id=EntityId("run-merge"), operation_id=EntityId(operation),
            idempotency_key="merge-key", repository=self.project,
            integration_branch=integration,
            expected_integration_head_oid=expected or self.base,
            candidate_ref=candidate,
            candidate_oid=candidate_oid or self.git("rev-parse", candidate).strip(),
        )

    def candidate_commit(self, *, branch="candidate", content="candidate\n") -> str:
        self.git("checkout", "-b", branch, "main")
        (self.repo / "candidate.txt").write_text(content, encoding="utf-8")
        self.git("add", "--", "candidate.txt")
        self.git("commit", "-m", branch)
        oid = self.git("rev-parse", "HEAD").strip()
        self.git("checkout", "main")
        return oid

    def managed_integration(self):
        self.git("branch", "integration", self.base)
        path = self.repo / ".worktrees" / "integration"
        path.parent.mkdir()
        self.git("worktree", "add", str(path), "integration")
        binding = LocalWorktreeBinding(self.project.project_id, EntityId("integration-worktree"), path)
        admission = ManagedIntegrationBinding("integration", binding)
        return path, binding, admission


class InspectTests(GitFixture):
    def test_inspects_attached_head_exact_refs_ancestry_and_worktrees(self) -> None:
        snapshot = self.inspect(
            refs=(GitRefQuery("refs/heads/main", GitRefExpectation("refs/heads/main", GitRefStatus.PRESENT, self.base)),),
            ancestry=(AncestryQuery(self.base, self.base),),
        )
        self.assertEqual(snapshot.status, ResultStatus.SUCCEEDED)
        self.assertEqual(snapshot.head.status, GitHeadStatus.ATTACHED)
        self.assertEqual(snapshot.head.branch, "main")
        self.assertEqual(snapshot.refs[0].oid, self.base)
        self.assertEqual(snapshot.ancestry[0].status, AncestryStatus.ANCESTOR)
        self.assertFalse(snapshot.working_tree.is_dirty)
        self.assertEqual(snapshot.worktrees[0].head_oid, self.base)
        self.assertTrue(snapshot.evidence_refs)

    def test_inspects_tracked_untracked_and_space_paths(self) -> None:
        (self.repo / "base.txt").write_text("changed\n", encoding="utf-8")
        (self.repo / "new file.txt").write_text("new\n", encoding="utf-8")
        snapshot = self.inspect(include_worktrees=False)
        self.assertEqual(snapshot.status, ResultStatus.SUCCEEDED)
        self.assertEqual([str(item) for item in snapshot.working_tree.tracked_changes], ["base.txt"])
        self.assertEqual([str(item) for item in snapshot.working_tree.untracked_paths], ["new file.txt"])

    def test_inspects_detached_and_unborn_heads(self) -> None:
        self.git("checkout", "--detach", self.base)
        detached = self.inspect(include_status=False, include_worktrees=False)
        self.assertEqual(detached.head.status, GitHeadStatus.DETACHED)
        self.git("checkout", "main")
        unborn_root = Path(self.temporary.name) / "unborn"
        unborn_root.mkdir()
        subprocess.run((GIT, "init", "-b", "newborn"), cwd=unborn_root, env=self.environment, check=True, stdout=subprocess.PIPE)
        project = LocalProjectBinding(self.project.project_id, unborn_root)
        settings = dataclasses.replace(load_project_settings(ROOT, load_installation_record(ROOT)), project_root=unborn_root)
        runner = LocalCommandRunner(
            project_settings=settings, run_settings=RunSettings(),
            allowed_permissions=(PermissionClass.LOCAL_READ, PermissionClass.LOCAL_EXECUTE),
            id_factory=_Ids(), clock=self.clock,
            log_store=FileCommandLogStore(unborn_root, ".git/logs"), base_environment=self.environment,
        )
        repository = LocalGitRepository(
            project=project, command_runner=runner, clock=self.clock,
            content_reader=FileContentReader(unborn_root),
            runtime=GitRuntimeBinding(sys.executable, GIT, ROOT / "src"),
        )
        request = GitInspectRequest(project.project_id, EntityId("run-unborn"), project, refs=(GitRefQuery("refs/heads/newborn"),), include_status=False, include_worktrees=False)
        snapshot = repository.inspect(request)
        self.assertEqual(snapshot.head.status, GitHeadStatus.UNBORN)
        self.assertEqual(snapshot.refs[0].status, GitRefStatus.UNBORN)

    def test_inspects_missing_head_explicitly(self) -> None:
        (self.repo / ".git" / "HEAD").unlink()
        snapshot = self.inspect(refs=(GitRefQuery("HEAD"),), include_status=False, include_worktrees=False)
        self.assertEqual(snapshot.status, ResultStatus.SUCCEEDED)
        self.assertEqual(snapshot.head.status, GitHeadStatus.MISSING)
        self.assertEqual(snapshot.refs[0].status, GitRefStatus.MISSING)
        self.assertTrue(snapshot.evidence_refs)

    def test_reports_missing_ancestry_object(self) -> None:
        missing = "f" * 40
        snapshot = self.inspect(ancestry=(AncestryQuery(missing, self.base),), include_head=False, include_status=False, include_worktrees=False)
        self.assertEqual(snapshot.status, ResultStatus.SUCCEEDED)
        self.assertEqual(snapshot.ancestry[0].status, AncestryStatus.MISSING)

    def test_reports_conflicted_path(self) -> None:
        self.git("checkout", "-b", "left")
        (self.repo / "base.txt").write_text("left\n", encoding="utf-8")
        self.git("commit", "-am", "left")
        self.git("checkout", "-b", "right", "main")
        (self.repo / "base.txt").write_text("right\n", encoding="utf-8")
        self.git("commit", "-am", "right")
        self.git("merge", "left", check=False)
        snapshot = self.inspect(include_worktrees=False)
        self.assertEqual(snapshot.status, ResultStatus.SUCCEEDED)
        self.assertEqual([str(item) for item in snapshot.working_tree.conflicted_paths], ["base.txt"])

    def test_registered_linked_worktree_is_observed(self) -> None:
        self.git("branch", "other", self.base)
        linked = self.repo / ".worktrees" / "other"
        linked.parent.mkdir()
        self.git("worktree", "add", str(linked), "other")
        snapshot = self.inspect(include_status=False)
        fact = next(item for item in snapshot.worktrees if item.branch == "refs/heads/other")
        self.assertEqual(fact.path.resolve(), linked.resolve())
        self.assertEqual(fact.head_oid, self.base)

        binding = LocalWorktreeBinding(self.project.project_id, EntityId("other-worktree"), linked)
        request = GitInspectRequest(
            self.project.project_id, EntityId("run-linked"), binding,
            include_worktrees=False,
        )
        linked_snapshot = self.repository.inspect(request)
        self.assertEqual(linked_snapshot.status, ResultStatus.SUCCEEDED)
        self.assertEqual(linked_snapshot.head.branch, "other")

    def test_non_repository_is_not_misreported_as_missing_head(self) -> None:
        directory = self.repo / "plain-directory"
        directory.mkdir()
        binding = LocalWorktreeBinding(self.project.project_id, EntityId("plain-directory"), directory)
        snapshot = self.repository.inspect(GitInspectRequest(
            self.project.project_id, EntityId("run-plain"), binding,
            include_status=False, include_worktrees=False,
        ))
        self.assertEqual(snapshot.status, ResultStatus.FAILED)
        self.assertIsNone(snapshot.head)

    def test_unavailable_command_log_digest_is_explicit_unknown(self) -> None:
        repository = LocalGitRepository(
            project=self.project, command_runner=self.runner, clock=self.clock,
            content_reader=_FailingReader(),
            runtime=GitRuntimeBinding(sys.executable, GIT, ROOT / "src"),
        )
        snapshot = repository.inspect(GitInspectRequest(
            self.project.project_id, EntityId("run-bad-log"), self.project,
            include_status=False, include_worktrees=False,
        ))
        self.assertEqual(snapshot.status, ResultStatus.UNKNOWN)
        self.assertEqual(snapshot.error.category, ErrorCategory.AMBIGUOUS_SIDE_EFFECT)
        self.assertIsNone(snapshot.head)

    def test_unrepresentable_status_path_is_not_reported_as_clean(self) -> None:
        path = self.repo / "line\nbreak.txt"
        try:
            path.write_text("unsafe portable name\n", encoding="utf-8")
        except OSError:
            self.skipTest("host filesystem cannot create a newline pathname")
        snapshot = self.inspect(include_worktrees=False)
        self.assertEqual(snapshot.status, ResultStatus.FAILED)
        self.assertIsNone(snapshot.working_tree)
        self.assertEqual(snapshot.error.category, ErrorCategory.UNSUPPORTED_CAPABILITY)


class BranchTests(GitFixture):
    def test_create_branch_is_conditional_and_idempotent(self) -> None:
        request = self.branch_request()
        first = self.repository.create_branch(request)
        second = self.repository.create_branch(request)
        self.assertEqual(first.status, ResultStatus.SUCCEEDED, first)
        self.assertTrue(first.changed)
        self.assertEqual(second.status, ResultStatus.SUCCEEDED)
        self.assertTrue(second.changed)
        self.assertEqual(self.git("rev-parse", "refs/heads/topic").strip(), self.base)
        self.assertGreater(len(first.evidence_refs), 0)

    def test_stale_source_does_not_create_branch(self) -> None:
        request = self.branch_request(source_oid="f" * 40)
        result = self.repository.create_branch(request)
        self.assertEqual(result.status, ResultStatus.FAILED)
        self.assertFalse(result.changed)
        self.assertEqual(result.error.category, ErrorCategory.GIT_CONFLICT)
        self.assertEqual(self.git("show-ref", "--verify", "--quiet", "refs/heads/topic", check=False), "")

    def test_stale_target_is_preserved(self) -> None:
        self.git("branch", "topic", self.base)
        request = self.branch_request(expected=GitRefExpectation("refs/heads/topic", GitRefStatus.MISSING))
        result = self.repository.create_branch(request)
        self.assertEqual(result.status, ResultStatus.FAILED)
        self.assertEqual(self.git("rev-parse", "refs/heads/topic").strip(), self.base)

    def test_head_source_is_resolved_and_verified(self) -> None:
        result = self.repository.create_branch(self.branch_request(source="HEAD"))
        self.assertEqual(result.status, ResultStatus.SUCCEEDED)
        self.assertEqual(self.git("rev-parse", "topic").strip(), self.base)

    def test_checked_out_unborn_branch_is_preserved(self) -> None:
        unborn_root = Path(self.temporary.name) / "unborn-branch"
        unborn_root.mkdir()
        subprocess.run((GIT, "init", "-b", "topic"), cwd=unborn_root, env=self.environment, shell=False, check=True, stdout=subprocess.PIPE)
        # A source ref can live in an unborn repository only after a detached
        # commit object and named source are created.
        empty_tree = subprocess.run((GIT, "mktree"), cwd=unborn_root, env=self.environment, input=b"", stdout=subprocess.PIPE, shell=False, check=True).stdout.decode().strip()
        commit = subprocess.run((GIT, "commit-tree", empty_tree, "-m", "source"), cwd=unborn_root, env=self.environment, stdout=subprocess.PIPE, shell=False, check=True).stdout.decode().strip()
        subprocess.run((GIT, "update-ref", "refs/heads/source", commit), cwd=unborn_root, env=self.environment, shell=False, check=True)
        project = LocalProjectBinding(self.project.project_id, unborn_root)
        settings = dataclasses.replace(load_project_settings(ROOT, load_installation_record(ROOT)), project_root=unborn_root)
        runner = LocalCommandRunner(
            project_settings=settings, run_settings=RunSettings(), allowed_permissions=(PermissionClass.LOCAL_READ, PermissionClass.LOCAL_EXECUTE),
            id_factory=_Ids(), clock=self.clock, log_store=FileCommandLogStore(unborn_root, ".git/logs"), base_environment=self.environment,
        )
        repository = LocalGitRepository(
            project=project, command_runner=runner, clock=self.clock, content_reader=FileContentReader(unborn_root),
            runtime=GitRuntimeBinding(sys.executable, GIT, ROOT / "src"),
        )
        request = BranchRequest(
            project.project_id, None, EntityId("run-unborn-branch"), EntityId("op-unborn-branch"), "key",
            project, "topic", "refs/heads/source", commit,
            GitRefExpectation("refs/heads/topic", GitRefStatus.UNBORN),
        )
        result = repository.create_branch(request)
        self.assertEqual(result.status, ResultStatus.FAILED, result)
        self.assertEqual(result.error.category, ErrorCategory.POLICY_DENIED)
        missing = subprocess.run((GIT, "show-ref", "--verify", "--quiet", "refs/heads/topic"), cwd=unborn_root, env=self.environment, shell=False, check=False)
        self.assertEqual(missing.returncode, 1)

    def test_changed_request_cannot_reuse_operation_identity(self) -> None:
        first = self.repository.create_branch(self.branch_request())
        changed = self.repository.create_branch(self.branch_request(branch="different"))
        self.assertEqual(first.status, ResultStatus.SUCCEEDED)
        self.assertEqual(changed.status, ResultStatus.FAILED)
        self.assertEqual(changed.error.category, ErrorCategory.GIT_CONFLICT)
        self.assertEqual(self.git("show-ref", "--verify", "--quiet", "refs/heads/different", check=False), "")

    def test_uncertain_publication_is_reconciled_without_duplicate_effect(self) -> None:
        intercepted = _InterceptRunner(self.runner, "unknown-after-publish")
        repository = self.make_repository(intercepted)
        result = repository.create_branch(self.branch_request())
        self.assertEqual(result.status, ResultStatus.SUCCEEDED)
        self.assertEqual(intercepted.publish_calls, 1)
        again = repository.create_branch(self.branch_request())
        self.assertEqual(again.status, ResultStatus.SUCCEEDED)
        self.assertEqual(intercepted.publish_calls, 1)

    def test_source_race_aborts_the_guarded_transaction(self) -> None:
        movement = self.candidate_commit(branch="movement", content="movement\n")
        self.git("branch", "source", self.base)
        intercepted = _InterceptRunner(
            self.runner, "race-source",
            before_publish=lambda: self.git("update-ref", "refs/heads/source", movement, self.base),
        )
        repository = self.make_repository(intercepted)
        result = repository.create_branch(self.branch_request(operation="op-source-race", source="refs/heads/source"))
        self.assertEqual(result.status, ResultStatus.FAILED)
        self.assertEqual(result.error.category, ErrorCategory.GIT_CONFLICT)
        self.assertEqual(self.git("rev-parse", "source").strip(), movement)
        self.assertEqual(subprocess.run((GIT, "show-ref", "--verify", "--quiet", "refs/heads/topic"), cwd=self.repo, env=self.environment, shell=False).returncode, 1)

    def test_target_race_preserves_the_concurrent_ref(self) -> None:
        intercepted = _InterceptRunner(
            self.runner, "race-target",
            before_publish=lambda: self.git("update-ref", "refs/heads/topic", self.base),
        )
        repository = self.make_repository(intercepted)
        result = repository.create_branch(self.branch_request(operation="op-target-race"))
        self.assertEqual(result.status, ResultStatus.FAILED)
        self.assertEqual(result.error.category, ErrorCategory.GIT_CONFLICT)
        self.assertEqual(self.git("rev-parse", "topic").strip(), self.base)

    def test_completed_receipt_does_not_override_a_later_target_move(self) -> None:
        request = self.branch_request(operation="op-later-move")
        completed = self.repository.create_branch(request)
        self.assertEqual(completed.status, ResultStatus.SUCCEEDED)
        movement = self.candidate_commit(branch="later-movement", content="later\n")
        self.git("update-ref", "refs/heads/topic", movement, self.base)
        reconciled = self.repository.create_branch(request)
        self.assertEqual(reconciled.status, ResultStatus.UNKNOWN)
        self.assertIsNone(reconciled.changed)
        self.assertEqual(self.git("rev-parse", "topic").strip(), movement)

    def test_unexecuted_uncertain_publication_stays_unknown_and_is_not_retried(self) -> None:
        intercepted = _InterceptRunner(self.runner, "unknown-before-publish")
        repository = self.make_repository(intercepted)
        first = repository.create_branch(self.branch_request())
        second = repository.create_branch(self.branch_request())
        self.assertEqual(first.status, ResultStatus.UNKNOWN)
        self.assertIsNone(first.changed)
        self.assertEqual(second.status, ResultStatus.UNKNOWN)
        self.assertEqual(intercepted.publish_calls, 1)
        self.assertEqual(self.git("show-ref", "--verify", "--quiet", "refs/heads/topic", check=False), "")


class MergeTests(GitFixture):
    def test_checked_out_developer_target_is_refused_and_preserved(self) -> None:
        candidate = self.candidate_commit()
        before_files = self.git("status", "--porcelain=v2", "-z")
        before_index = self.git("write-tree").strip()
        result = self.repository.merge(self.merge_request(candidate_oid=candidate, integration="main"))
        self.assertEqual(result.status, ResultStatus.FAILED)
        self.assertEqual(result.error.category, ErrorCategory.POLICY_DENIED)
        self.assertEqual(self.git("rev-parse", "main").strip(), self.base)
        self.assertEqual(self.git("write-tree").strip(), before_index)
        self.assertEqual(self.git("status", "--porcelain=v2", "-z"), before_files)
        repeated = self.repository.merge(self.merge_request(candidate_oid=candidate, integration="main"))
        self.assertEqual(repeated.status, ResultStatus.FAILED)
        self.assertEqual(repeated.error.category, ErrorCategory.POLICY_DENIED)

    def test_admitted_managed_integration_is_advanced_and_developer_tree_preserved(self) -> None:
        candidate = self.candidate_commit()
        path, binding, admission = self.managed_integration()
        repository = self.make_repository(self.runner, (admission,))
        root_index = self.git("write-tree").strip()
        root_status = self.git("status", "--porcelain=v2", "-z")
        result = repository.merge(self.merge_request(candidate_oid=candidate))
        self.assertEqual(result.status, ResultStatus.SUCCEEDED)
        self.assertTrue(result.changed)
        merged = self.git("rev-parse", "integration").strip()
        parents = self.git("rev-list", "--parents", "-n", "1", merged).split()
        self.assertEqual(parents[1:], [self.base, candidate])
        self.assertEqual(self.git("status", "--porcelain", cwd=path), "")
        self.assertEqual((path / "candidate.txt").read_text(encoding="utf-8"), "candidate\n")
        self.assertEqual(self.git("write-tree").strip(), root_index)
        self.assertEqual(self.git("status", "--porcelain=v2", "-z"), root_status)

    def test_ref_published_but_checkout_not_advanced_stays_unknown_without_retry(self) -> None:
        candidate = self.candidate_commit()
        path, binding, admission = self.managed_integration()
        intercepted = _InterceptRunner(self.runner, "unknown-before-read-tree", path)
        repository = self.make_repository(intercepted, (admission,))
        first = repository.merge(self.merge_request(candidate_oid=candidate))
        merged = self.git("rev-parse", "integration").strip()
        self.assertNotEqual(merged, self.base)
        self.assertEqual(first.status, ResultStatus.UNKNOWN)
        self.assertIsNone(first.changed)
        self.assertFalse((path / "candidate.txt").exists())
        second = repository.merge(self.merge_request(candidate_oid=candidate))
        self.assertEqual(second.status, ResultStatus.UNKNOWN)
        self.assertEqual(intercepted.read_tree_calls, 1)
        self.assertFalse((path / "candidate.txt").exists())

    def test_concurrent_dirty_change_after_ref_publication_is_preserved(self) -> None:
        candidate = self.candidate_commit()
        path, binding, admission = self.managed_integration()
        intercepted = _InterceptRunner(self.runner, "dirty-after-publish", path)
        repository = self.make_repository(intercepted, (admission,))
        result = repository.merge(self.merge_request(candidate_oid=candidate))
        self.assertEqual(result.status, ResultStatus.UNKNOWN)
        self.assertEqual((path / "base.txt").read_text(encoding="utf-8"), "developer change\n")
        self.assertEqual(intercepted.read_tree_calls, 0)

    def test_concurrent_index_change_after_ref_publication_is_preserved(self) -> None:
        candidate = self.candidate_commit()
        path, binding, admission = self.managed_integration()
        intercepted = _InterceptRunner(self.runner, "index-after-publish", path)
        repository = self.make_repository(intercepted, (admission,))
        result = repository.merge(self.merge_request(operation="op-index-race", candidate_oid=candidate))
        self.assertEqual(result.status, ResultStatus.UNKNOWN)
        self.assertEqual((path / "base.txt").read_text(encoding="utf-8"), "staged concurrent change\n")
        self.assertNotEqual(self.git("status", "--porcelain", cwd=path), "")
        self.assertEqual(intercepted.read_tree_calls, 0)

    def test_candidate_ref_movement_is_rejected(self) -> None:
        candidate = self.candidate_commit()
        self.git("branch", "integration", self.base)
        result = self.repository.merge(self.merge_request(candidate_oid=self.base))
        self.assertEqual(result.status, ResultStatus.FAILED)
        self.assertEqual(result.error.category, ErrorCategory.GIT_CONFLICT)
        self.assertEqual(self.git("rev-parse", "integration").strip(), self.base)

    def test_unadmitted_managed_looking_path_is_refused(self) -> None:
        candidate = self.candidate_commit()
        path, binding, admission = self.managed_integration()
        result = self.repository.merge(self.merge_request(candidate_oid=candidate))
        self.assertEqual(result.status, ResultStatus.FAILED)
        self.assertEqual(result.error.category, ErrorCategory.POLICY_DENIED)
        self.assertEqual(self.git("rev-parse", "integration").strip(), self.base)
        self.assertFalse((path / "candidate.txt").exists())

    def test_merge_conflict_does_not_publish(self) -> None:
        self.git("checkout", "-b", "candidate", "main")
        (self.repo / "base.txt").write_text("candidate\n", encoding="utf-8")
        self.git("commit", "-am", "candidate")
        candidate = self.git("rev-parse", "HEAD").strip()
        self.git("checkout", "main")
        (self.repo / "base.txt").write_text("integration\n", encoding="utf-8")
        self.git("commit", "-am", "integration")
        integration = self.git("rev-parse", "HEAD").strip()
        self.git("branch", "integration", integration)
        result = self.repository.merge(self.merge_request(candidate_oid=candidate, expected=integration))
        self.assertEqual(result.status, ResultStatus.FAILED)
        self.assertEqual(result.error.category, ErrorCategory.GIT_CONFLICT)
        self.assertEqual(self.git("rev-parse", "integration").strip(), integration)


if __name__ == "__main__":
    unittest.main()
