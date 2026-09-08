"""Observed, conditional Git operations backed by ``CommandRunner`` evidence.

The adapter keeps host paths and the optional managed integration checkout in
local bindings.  Git mutations use a small helper in this module because the
frozen command request has no stdin field.  The helper accepts only validated
Git refs/OIDs and invokes child processes with ``shell=False``.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from domain_values import (
    CommandStatus,
    DomainError,
    EntityId,
    ErrorCategory,
    EvidenceRef,
    FrozenJsonObject,
    ResultStatus,
    ScopePath,
)
from local_ports import (
    AncestryObservation,
    AncestryQuery,
    AncestryStatus,
    BranchRequest,
    Clock,
    CommandCwdRule,
    CommandDefinition,
    CommandEvidence,
    CommandPlatform,
    CommandRequest,
    CommandRootBindings,
    CommandRunner,
    CommandSuccessRule,
    ContentRef,
    EnvironmentBinding,
    GitHead,
    GitHeadStatus,
    GitInspectRequest,
    GitOperationResult,
    GitRefObservation,
    GitRefStatus,
    GitSnapshot,
    GitStatus,
    GitTarget,
    GitWorktreeFact,
    LocalControlBinding,
    LocalProjectBinding,
    LocalWorktreeBinding,
    MergeRequest,
    PermissionClass,
)


_OID = re.compile(r"(?:[a-f0-9]{40}|[a-f0-9]{64})\Z")
_FULL_REF = re.compile(r"refs/(?![./])[^\x00-\x20\x7f ~^:?*\\[]+\Z")
_ZERO_40 = "0" * 40
_ZERO_64 = "0" * 64
_RECEIPT_VERSION = 1
_HELPER_MARKER = "--git-ops-helper-v1"
_MAX_OUTPUT_BYTES = 1024 * 1024


class ContentReader(Protocol):
    """Read a command log after checking its content-addressed reference."""

    def read(self, reference: ContentRef) -> bytes: ...


class FileContentReader:
    """Digest-check command output stored beneath one project root."""

    def __init__(self, project_root: Path) -> None:
        root = Path(project_root)
        if not root.is_absolute():
            raise ValueError("content reader project root must be absolute")
        absolute = Path(os.path.abspath(root))
        resolved = absolute.resolve(strict=True)
        if absolute != resolved or absolute.is_symlink() or not resolved.is_dir():
            raise ValueError("content reader project root must be a real directory")
        self._root = resolved

    def read(self, reference: ContentRef) -> bytes:
        if not isinstance(reference, ContentRef):
            raise TypeError("reference must be a ContentRef")
        path = self._root.joinpath(*reference.path.split("/"))
        resolved = path.resolve(strict=True)
        if not resolved.is_file() or not resolved.is_relative_to(self._root):
            raise OSError("command content reference escapes the project root")
        current = self._root
        for part in path.relative_to(self._root).parts:
            current = current / part
            if current.is_symlink():
                raise OSError("command content reference traverses a symbolic link")
        content = resolved.read_bytes()
        if hashlib.sha256(content).hexdigest() != reference.sha256.value:
            raise OSError("command content does not match its recorded digest")
        return content


@dataclass(frozen=True, slots=True)
class GitRuntimeBinding:
    """Trusted local executables/module root used by the finite helper."""

    python_executable: str
    git_executable: str
    module_root: Path

    def __post_init__(self) -> None:
        for name in ("python_executable", "git_executable"):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(f"{name} must be a string")
            if not value or "\x00" in value:
                raise ValueError(f"{name} must be a non-empty process executable")
        root = Path(self.module_root)
        if not root.is_absolute():
            raise ValueError("module_root must be absolute")
        root = Path(os.path.abspath(root)).resolve(strict=True)
        module = root / "git_ops.py"
        if not root.is_dir() or not module.is_file():
            raise ValueError("module_root must contain git_ops.py")
        object.__setattr__(self, "module_root", root)


@dataclass(frozen=True, slots=True)
class ManagedIntegrationBinding:
    """Explicit local admission for one coordinator-managed checkout."""

    branch: str
    worktree: LocalWorktreeBinding

    def __post_init__(self) -> None:
        object.__setattr__(self, "branch", _branch_ref(self.branch))
        if not isinstance(self.worktree, LocalWorktreeBinding):
            raise TypeError("worktree must be a LocalWorktreeBinding")


@dataclass(frozen=True, slots=True)
class _CommandOutcome:
    evidence: CommandEvidence | None
    stdout: bytes
    stderr: bytes
    evidence_refs: tuple[EvidenceRef, ...]
    usable: bool
    ambiguous: bool
    reason: str | None = None

    @property
    def exit_code(self) -> int | None:
        return None if self.evidence is None else self.evidence.exit_code


@dataclass(frozen=True, slots=True)
class _Receipt:
    fingerprint: str
    kind: str
    phase: str
    target_ref: str
    before_oid: str | None
    result_oid: str | None
    source_ref: str
    source_oid: str
    changed: bool | None
    error_category: str | None


class LocalGitRepository:
    """Concrete ``GitRepository`` using actual Git observations."""

    def __init__(
        self,
        *,
        project: LocalProjectBinding,
        command_runner: CommandRunner,
        clock: Clock,
        content_reader: ContentReader,
        runtime: GitRuntimeBinding | None = None,
        managed_integrations: tuple[ManagedIntegrationBinding, ...] = (),
        command_timeout_seconds: int = 30,
    ) -> None:
        if not isinstance(project, LocalProjectBinding):
            raise TypeError("project must be a LocalProjectBinding")
        if not callable(getattr(command_runner, "execute", None)):
            raise TypeError("command_runner must implement execute")
        if not callable(getattr(clock, "now", None)):
            raise TypeError("clock must implement now")
        if not callable(getattr(content_reader, "read", None)):
            raise TypeError("content_reader must implement read")
        if isinstance(command_timeout_seconds, bool) or not isinstance(command_timeout_seconds, int):
            raise TypeError("command_timeout_seconds must be an integer")
        if command_timeout_seconds < 1:
            raise ValueError("command_timeout_seconds must be positive")
        selected_runtime = runtime or GitRuntimeBinding(
            python_executable=sys.executable,
            git_executable="git",
            module_root=Path(__file__).resolve().parent,
        )
        if not isinstance(selected_runtime, GitRuntimeBinding):
            raise TypeError("runtime must be a GitRuntimeBinding")
        integrations = tuple(managed_integrations)
        if not all(isinstance(item, ManagedIntegrationBinding) for item in integrations):
            raise TypeError("managed_integrations must contain ManagedIntegrationBinding values")
        if len({item.branch for item in integrations}) != len(integrations):
            raise ValueError("managed integration branches must be unique")
        project_root = Path(os.path.abspath(project.root)).resolve(strict=True)
        for item in integrations:
            if item.worktree.project_id != project.project_id:
                raise ValueError("managed integration binding belongs to another project")
            root = Path(os.path.abspath(item.worktree.root)).resolve(strict=True)
            if root == project_root or not root.is_relative_to(project_root):
                raise ValueError("managed integration worktree must be distinct and inside the project root")

        self._project = project
        self._runner = command_runner
        self._clock = clock
        self._reader = content_reader
        self._runtime = selected_runtime
        self._managed = {item.branch: item.worktree for item in integrations}
        self._timeout = command_timeout_seconds

    def inspect(self, request: GitInspectRequest) -> GitSnapshot:
        if not isinstance(request, GitInspectRequest):
            raise TypeError("request must be a GitInspectRequest")
        self._check_project(request.project_id, request.target)
        evidence: list[EvidenceRef] = []
        observed_at = self._clock.now()

        missing_head = self._head_file_missing(request.target.root)
        repository_probe = self._git(request, evidence, "inspect-repository", "rev-parse", "--show-prefix")
        if not repository_probe.usable:
            return self._snapshot_command_failure(request, observed_at, evidence, repository_probe, None)
        if repository_probe.exit_code == 0:
            if repository_probe.stdout not in {b"", b"\n", b"\r\n"}:
                return self._snapshot_failure(request, observed_at, evidence, None, ErrorCategory.INVALID_INPUT, "Git target is not the root of the observed worktree")
        elif missing_head is not True or repository_probe.exit_code != 128:
            return self._snapshot_command_failure(request, observed_at, evidence, repository_probe, None)
        head: GitHead | None = None
        symbolic_branch: str | None = None
        if request.include_head or request.refs:
            if missing_head is True:
                probe = self._git(request, evidence, "inspect-missing-head", "rev-parse", "--verify", "HEAD")
                if not probe.usable:
                    return self._snapshot_command_failure(request, observed_at, evidence, probe, None)
                if probe.exit_code == 0:
                    return self._snapshot_failure(
                        request, observed_at, evidence, None,
                        ErrorCategory.INVALID_INPUT,
                        "Git resolved HEAD outside the exact metadata root that has no HEAD",
                    )
                head = GitHead(GitHeadStatus.MISSING, None, None)
                if request.include_status or request.include_worktrees or request.ancestry:
                    return self._snapshot_failure(
                        request, observed_at, evidence, head,
                        ErrorCategory.UNSUPPORTED_CAPABILITY,
                        "Git metadata has no HEAD, so the requested remaining facts cannot be observed",
                    )
            else:
                head_result = self._observe_head(request, evidence)
                if isinstance(head_result, DomainError):
                    return self._snapshot_error(request, observed_at, evidence, head_result)
                head, symbolic_branch = head_result

        refs: list[GitRefObservation] = []
        for query in request.refs:
            if query.ref == "HEAD":
                assert head is not None
                status = {
                    GitHeadStatus.ATTACHED: GitRefStatus.PRESENT,
                    GitHeadStatus.DETACHED: GitRefStatus.PRESENT,
                    GitHeadStatus.UNBORN: GitRefStatus.UNBORN,
                    GitHeadStatus.MISSING: GitRefStatus.MISSING,
                }[head.status]
                refs.append(GitRefObservation("HEAD", status, head.oid))
                continue
            observed = self._exact_ref(request, query.ref, evidence)
            if isinstance(observed, DomainError):
                return self._snapshot_error(request, observed_at, evidence, observed, head, refs=refs)
            if observed[0] is GitRefStatus.PRESENT:
                oid = observed[1]
                assert oid is not None
                refs.append(GitRefObservation(query.ref, GitRefStatus.PRESENT, oid))
            else:
                ref_status = GitRefStatus.UNBORN if head is not None and head.status is GitHeadStatus.UNBORN and query.ref == symbolic_branch else GitRefStatus.MISSING
                refs.append(GitRefObservation(query.ref, ref_status, None))

        ancestry: list[AncestryObservation] = []
        for query in request.ancestry:
            observation = self._observe_ancestry(request, query, evidence)
            if isinstance(observation, DomainError):
                return self._snapshot_error(request, observed_at, evidence, observation, head, refs, ancestry)
            ancestry.append(observation)

        working_tree: GitStatus | None = None
        if request.include_status:
            outcome = self._git(request, evidence, "inspect-status", "status", "--porcelain=v2", "-z", "--untracked-files=all")
            if not outcome.usable or outcome.exit_code != 0:
                return self._snapshot_command_failure(request, observed_at, evidence, outcome, head, refs, ancestry)
            try:
                working_tree = _parse_status(outcome.stdout)
            except (TypeError, ValueError, UnicodeError) as exc:
                return self._snapshot_failure(request, observed_at, evidence, head, ErrorCategory.UNSUPPORTED_CAPABILITY, f"Git status contains an unrepresentable path: {exc}", refs, ancestry)

        worktrees: tuple[GitWorktreeFact, ...] = ()
        if request.include_worktrees:
            outcome = self._git(request, evidence, "inspect-worktrees", "worktree", "list", "--porcelain", "-z")
            if not outcome.usable or outcome.exit_code != 0:
                return self._snapshot_command_failure(request, observed_at, evidence, outcome, head, refs, ancestry, working_tree)
            try:
                worktrees = _parse_worktrees(outcome.stdout)
            except (TypeError, ValueError, UnicodeError) as exc:
                return self._snapshot_failure(request, observed_at, evidence, head, ErrorCategory.UNSUPPORTED_CAPABILITY, f"Git worktree output is not representable: {exc}", refs, ancestry, working_tree)

        return GitSnapshot(
            status=ResultStatus.SUCCEEDED,
            project_id=request.project_id,
            run_id=request.run_id,
            target=request.target,
            head=head if request.include_head else None,
            refs=tuple(refs),
            ancestry=tuple(ancestry),
            worktrees=worktrees,
            working_tree=working_tree,
            observed_at=observed_at,
            evidence_refs=tuple(evidence),
        )

    def create_branch(self, request: BranchRequest) -> GitOperationResult:
        if not isinstance(request, BranchRequest):
            raise TypeError("request must be a BranchRequest")
        self._check_project(request.project_id, request.repository)
        target_ref = _branch_ref(request.branch)
        fingerprint = _fingerprint("branch", request, target_ref)
        context = _MutationContext.from_branch(request, target_ref, fingerprint)
        return self._mutate(context)

    def merge(self, request: MergeRequest) -> GitOperationResult:
        if not isinstance(request, MergeRequest):
            raise TypeError("request must be a MergeRequest")
        self._check_project(request.project_id, request.repository)
        target_ref = _branch_ref(request.integration_branch)
        fingerprint = _fingerprint("merge", request, target_ref)
        context = _MutationContext.from_merge(request, target_ref, fingerprint)
        return self._mutate(context)

    def _mutate(self, context: "_MutationContext") -> GitOperationResult:
        evidence: list[EvidenceRef] = []
        repository_probe = self._git(context, evidence, "mutation-repository", "rev-parse", "--show-prefix")
        if not repository_probe.usable:
            return self._unknown(context, evidence, "repository root could not be observed")
        if repository_probe.exit_code != 0 or repository_probe.stdout not in {b"", b"\n", b"\r\n"}:
            return self._operation_error(context, evidence, _error(ErrorCategory.INVALID_INPUT, "configured project is not the observed Git worktree root", evidence), False)
        receipt_ref = _receipt_ref(context.project_id, context.operation_id)
        receipt_state = self._read_receipt(context, receipt_ref, evidence)
        if isinstance(receipt_state, DomainError):
            return self._operation_error(context, evidence, receipt_state, None)
        receipt, receipt_oid = receipt_state
        created_intent = False
        if receipt is not None:
            return self._reconcile_existing(context, receipt_ref, receipt, receipt_oid, evidence)

        intent = _Receipt(
            context.fingerprint, context.kind, "intent", context.target_ref,
            context.expected_target_oid, None, context.source_ref,
            context.source_oid, None, None,
        )
        intent_payload = _receipt_bytes(intent)
        outcome = self._helper(context, evidence, "write-intent", {
            "action": "write_intent",
            "receipt_ref": receipt_ref,
            "receipt": _b64(intent_payload),
        })
        if not outcome.usable or outcome.exit_code != 0:
            observed = self._read_receipt(context, receipt_ref, evidence)
            if isinstance(observed, tuple) and observed[0] is not None:
                return self._reconcile_existing(context, receipt_ref, observed[0], observed[1], evidence)
            return self._unknown(context, evidence, "Git operation intent outcome is unresolved")
        created_intent = True
        intent_oid = _git_blob_oid(intent_payload, context.source_oid)
        observed_intent = self._read_receipt(context, receipt_ref, evidence)
        if isinstance(observed_intent, DomainError):
            return self._unknown(context, evidence, "Git operation intent could not be verified")
        if observed_intent[0] != intent:
            return self._unknown(context, evidence, "Git operation intent does not match its requested identity")
        if observed_intent[1] is not None:
            intent_oid = observed_intent[1]

        preflight = self._preflight_mutation(context, evidence)
        if isinstance(preflight, DomainError):
            if created_intent and preflight.category is not ErrorCategory.AMBIGUOUS_SIDE_EFFECT:
                self._record_failed(context, receipt_ref, intent_oid, preflight, evidence)
            return self._operation_error(context, evidence, preflight, False)
        managed = preflight

        phase = "ref_published" if managed is not None and context.kind == "merge" else "completed"
        outcome = self._helper(context, evidence, "publish", context.helper_payload(receipt_ref, intent_oid, phase))
        if not outcome.usable:
            return self._reconcile_after_uncertain(context, receipt_ref, managed, evidence)
        if outcome.exit_code != 0:
            reconciled = self._reconcile_after_known_failure(context, receipt_ref, managed, evidence, outcome)
            return reconciled

        return self._reconcile_after_publish(context, receipt_ref, managed, evidence, allow_refresh=True)

    def _preflight_mutation(
        self, context: "_MutationContext", evidence: list[EvidenceRef]
    ) -> LocalWorktreeBinding | None | DomainError:
        source = self._resolve_named_commit(context, context.source_ref, evidence)
        if isinstance(source, DomainError):
            return source
        source_ref, source_oid = source
        if source_ref != context.source_ref or source_oid != context.source_oid:
            return _error(ErrorCategory.GIT_CONFLICT, "source ref does not match the expected commit", evidence)

        symbolic_target = self._symbolic_ref(context, context.target_ref, evidence)
        if isinstance(symbolic_target, DomainError):
            return symbolic_target
        if symbolic_target is not None:
            return _error(ErrorCategory.POLICY_DENIED, "symbolic mutation targets are not supported", evidence)

        target = self._exact_ref(context, context.target_ref, evidence)
        if isinstance(target, DomainError):
            return target
        target_status, target_oid = target
        if context.expected_target_oid is None:
            expected_status = context.expected_target_status
            observed_status = target_status
            if target_status is GitRefStatus.MISSING and expected_status in {GitRefStatus.MISSING, GitRefStatus.UNBORN}:
                head = self._observe_head(_InspectLike(context, self._project), evidence)
                if isinstance(head, DomainError):
                    return head
                if head[0].status is GitHeadStatus.UNBORN and head[1] == context.target_ref:
                    observed_status = GitRefStatus.UNBORN
            if observed_status is not expected_status:
                return _error(ErrorCategory.GIT_CONFLICT, "target ref does not match the expected missing/unborn state", evidence)
        elif target_status is not GitRefStatus.PRESENT or target_oid != context.expected_target_oid:
            return _error(ErrorCategory.GIT_CONFLICT, "target ref does not match the expected commit", evidence)

        checked = self._checked_out_paths(context, evidence)
        if isinstance(checked, DomainError):
            return checked
        if not checked:
            return None
        if context.kind == "branch" and context.expected_target_oid == context.source_oid:
            return None
        admitted = self._managed.get(context.target_ref)
        if context.kind != "merge" or admitted is None:
            return _error(ErrorCategory.POLICY_DENIED, "ref mutation would move a checked-out branch without an admitted managed integration binding", evidence)
        admitted_path = Path(os.path.abspath(admitted.root)).resolve(strict=True)
        if checked != (admitted_path,):
            return _error(ErrorCategory.POLICY_DENIED, "checked-out integration branch does not match its admitted managed worktree", evidence)
        clean = self._managed_before_state(context, admitted, evidence)
        if isinstance(clean, DomainError):
            return clean
        return admitted

    def _reconcile_existing(
        self,
        context: "_MutationContext",
        receipt_ref: str,
        receipt: _Receipt,
        receipt_oid: str | None,
        evidence: list[EvidenceRef],
    ) -> GitOperationResult:
        if receipt.fingerprint != context.fingerprint or receipt.kind != context.kind:
            return self._operation_error(context, evidence, _error(ErrorCategory.GIT_CONFLICT, "operation identity was already used by a different request", evidence), False)
        if receipt.phase == "intent":
            return self._unknown(context, evidence, "a prior matching Git mutation may have been interrupted")
        if receipt.phase == "failed":
            category = ErrorCategory(receipt.error_category or ErrorCategory.GIT_CONFLICT.value)
            return self._operation_error(context, evidence, _error(category, "the recorded Git operation failed before publication", evidence), False)
        if receipt.phase == "checkout_failed":
            target = self._exact_ref(context, context.target_ref, evidence)
            if receipt.result_oid is None or isinstance(target, DomainError) or target != (GitRefStatus.PRESENT, receipt.result_oid):
                return self._unknown(context, evidence, "recorded checkout failure no longer matches the current target")
            category = ErrorCategory(receipt.error_category or ErrorCategory.GIT_CONFLICT.value)
            return self._operation_error(context, evidence, _error(category, "the published ref could not be applied to its managed checkout", evidence), bool(receipt.changed))
        if receipt.phase not in {"ref_published", "completed"}:
            return self._unknown(context, evidence, "Git operation receipt has an unsupported phase")
        managed = self._managed.get(context.target_ref) if context.kind == "merge" and receipt.phase == "ref_published" else None
        return self._reconcile_after_publish(context, receipt_ref, managed, evidence, allow_refresh=False)

    def _reconcile_after_uncertain(
        self,
        context: "_MutationContext",
        receipt_ref: str,
        managed: LocalWorktreeBinding | None,
        evidence: list[EvidenceRef],
    ) -> GitOperationResult:
        state = self._read_receipt(context, receipt_ref, evidence)
        if isinstance(state, DomainError) or state[0] is None:
            return self._unknown(context, evidence, "Git mutation outcome cannot be reconciled")
        receipt = state[0]
        if receipt.fingerprint != context.fingerprint:
            return self._unknown(context, evidence, "Git receipt conflicts with the attempted request")
        if receipt.phase in {"ref_published", "completed"}:
            return self._reconcile_after_publish(context, receipt_ref, managed, evidence, allow_refresh=False)
        return self._unknown(context, evidence, "Git mutation remained at intent after an uncertain command result")

    def _reconcile_after_known_failure(
        self,
        context: "_MutationContext",
        receipt_ref: str,
        managed: LocalWorktreeBinding | None,
        evidence: list[EvidenceRef],
        outcome: _CommandOutcome,
    ) -> GitOperationResult:
        state = self._read_receipt(context, receipt_ref, evidence)
        if not isinstance(state, DomainError) and state[0] is not None and state[0].phase in {"ref_published", "completed"}:
            return self._reconcile_after_publish(context, receipt_ref, managed, evidence, allow_refresh=False)
        category = ErrorCategory.GIT_CONFLICT if outcome.exit_code in {20, 21, 22} else ErrorCategory.INTERNAL_ERROR
        failure = _error(category, "Git conditional publication failed", evidence)
        self._record_failed(context, receipt_ref, state[1] if not isinstance(state, DomainError) else None, failure, evidence)
        return self._operation_error(context, evidence, failure, False)

    def _reconcile_after_publish(
        self,
        context: "_MutationContext",
        receipt_ref: str,
        managed: LocalWorktreeBinding | None,
        evidence: list[EvidenceRef],
        *,
        allow_refresh: bool,
    ) -> GitOperationResult:
        state = self._read_receipt(context, receipt_ref, evidence)
        if isinstance(state, DomainError) or state[0] is None:
            return self._unknown(context, evidence, "published Git result has no verifiable receipt")
        receipt, receipt_oid = state
        if receipt.fingerprint != context.fingerprint or receipt.result_oid is None:
            return self._unknown(context, evidence, "published Git receipt is inconsistent with the request")
        target = self._exact_ref(context, context.target_ref, evidence)
        if isinstance(target, DomainError) or target != (GitRefStatus.PRESENT, receipt.result_oid):
            return self._unknown(context, evidence, "receipt and current target ref do not establish one result")
        source = self._resolve_named_commit(context, context.source_ref, evidence)
        if isinstance(source, DomainError) or source != (context.source_ref, context.source_oid):
            return self._unknown(context, evidence, "source ref changed while the Git result was being reconciled")
        if context.kind == "merge" and receipt.changed:
            parents = self._commit_parents(context, receipt.result_oid, evidence)
            if parents != (context.expected_target_oid, context.source_oid):
                return self._unknown(context, evidence, "integration commit parents do not match the guarded request")

        if managed is not None and receipt.changed:
            checkout = self._managed_after_state(context, managed, receipt.result_oid, evidence)
            if checkout == "clean":
                pass
            elif checkout == "before" and allow_refresh and receipt.phase == "ref_published":
                refresh = self._git_binding(
                    context, managed, evidence, "advance-integration", PermissionClass.LOCAL_EXECUTE,
                    "read-tree", "-u", "-m", context.expected_target_oid or "", receipt.result_oid,
                )
                if not refresh.usable:
                    return self._unknown(context, evidence, "managed integration checkout advancement is unresolved")
                if refresh.exit_code != 0:
                    failure = _error(ErrorCategory.GIT_CONFLICT, "managed integration checkout could not be advanced without overwriting local state", evidence)
                    if receipt_oid is not None:
                        self._record_checkout_failed(context, receipt_ref, receipt_oid, receipt, failure, evidence)
                    return self._operation_error(context, evidence, failure, True)
                checkout = self._managed_after_state(context, managed, receipt.result_oid, evidence)
                if checkout != "clean":
                    return self._unknown(context, evidence, "managed integration checkout did not reach the published ref")
                if receipt_oid is not None:
                    self._finish_receipt(context, receipt_ref, receipt_oid, receipt, evidence)
            else:
                return self._unknown(context, evidence, "published integration ref and managed checkout are not reconciled")

        refs = (GitRefObservation(context.target_ref, GitRefStatus.PRESENT, receipt.result_oid),)
        ancestry: tuple[AncestryObservation, ...] = ()
        if context.kind == "merge":
            query = AncestryQuery(context.source_oid, receipt.result_oid)
            ancestry = (AncestryObservation(query, AncestryStatus.ANCESTOR),)
        head = self._head_for_project(context, evidence)
        return GitOperationResult(
            ResultStatus.SUCCEEDED,
            context.operation_id,
            context.idempotency_key,
            bool(receipt.changed),
            head,
            refs,
            ancestry,
            tuple(evidence),
        )

    def _managed_before_state(self, context: "_MutationContext", binding: LocalWorktreeBinding, evidence: list[EvidenceRef]) -> DomainError | None:
        expected = context.expected_target_oid
        assert expected is not None
        head = self._git_binding(context, binding, evidence, "managed-head", PermissionClass.LOCAL_READ, "rev-parse", "--verify", "HEAD")
        index = self._git_binding(context, binding, evidence, "managed-index", PermissionClass.LOCAL_EXECUTE, "write-tree")
        tree = self._git(context, evidence, "expected-tree", "rev-parse", "--verify", f"{expected}^{{tree}}")
        diff = self._git_binding(context, binding, evidence, "managed-diff", PermissionClass.LOCAL_READ, "diff", "--quiet", "--no-ext-diff")
        untracked = self._git_binding(context, binding, evidence, "managed-untracked", PermissionClass.LOCAL_READ, "ls-files", "--others", "--exclude-standard", "-z")
        for outcome in (head, index, tree, diff, untracked):
            if not outcome.usable:
                return _error(ErrorCategory.AMBIGUOUS_SIDE_EFFECT, "managed integration state could not be observed", evidence)
        if _single_oid(head.stdout) != expected or _single_oid(index.stdout) != _single_oid(tree.stdout) or diff.exit_code != 0 or untracked.stdout:
            return _error(ErrorCategory.GIT_CONFLICT, "managed integration worktree/index is not clean at the expected head", evidence)
        return None

    def _managed_after_state(self, context: "_MutationContext", binding: LocalWorktreeBinding, result_oid: str, evidence: list[EvidenceRef]) -> str:
        expected = context.expected_target_oid
        branch = self._git_binding(context, binding, evidence, "managed-result-branch", PermissionClass.LOCAL_READ, "symbolic-ref", "-q", "HEAD")
        head = self._git_binding(context, binding, evidence, "managed-result-head", PermissionClass.LOCAL_READ, "rev-parse", "--verify", "HEAD")
        index = self._git_binding(context, binding, evidence, "managed-result-index", PermissionClass.LOCAL_EXECUTE, "write-tree")
        new_tree = self._git(context, evidence, "result-tree", "rev-parse", "--verify", f"{result_oid}^{{tree}}")
        old_tree = self._git(context, evidence, "before-tree", "rev-parse", "--verify", f"{expected}^{{tree}}") if expected is not None else None
        diff = self._git_binding(context, binding, evidence, "managed-result-diff", PermissionClass.LOCAL_READ, "diff", "--quiet", "--no-ext-diff")
        untracked = self._git_binding(context, binding, evidence, "managed-result-untracked", PermissionClass.LOCAL_READ, "ls-files", "--others", "--exclude-standard", "-z")
        outcomes = (branch, head, index, new_tree, diff, untracked) + (() if old_tree is None else (old_tree,))
        if any(not item.usable for item in outcomes):
            return "unknown"
        try:
            branch_ref = branch.stdout.decode("ascii").strip()
            admitted_path = Path(os.path.abspath(binding.root)).resolve(strict=True)
        except (OSError, UnicodeError, ValueError):
            return "unknown"
        checked = self._checked_out_paths(context, evidence)
        if (
            branch.exit_code != 0
            or branch_ref != context.target_ref
            or isinstance(checked, DomainError)
            or checked != (admitted_path,)
            or _single_oid(head.stdout) != result_oid
        ):
            return "unknown"
        index_oid = _single_oid(index.stdout)
        if index_oid == _single_oid(new_tree.stdout) and diff.exit_code == 0 and not untracked.stdout:
            return "clean"
        if old_tree is not None and index_oid == _single_oid(old_tree.stdout) and diff.exit_code == 0 and not untracked.stdout:
            return "before"
        return "dirty"

    def _finish_receipt(self, context: "_MutationContext", receipt_ref: str, old_oid: str, receipt: _Receipt, evidence: list[EvidenceRef]) -> None:
        completed = _Receipt(receipt.fingerprint, receipt.kind, "completed", receipt.target_ref, receipt.before_oid, receipt.result_oid, receipt.source_ref, receipt.source_oid, receipt.changed, None)
        self._helper(context, evidence, "finish-receipt", {
            "action": "replace_receipt", "receipt_ref": receipt_ref,
            "old_receipt_oid": old_oid, "receipt": _b64(_receipt_bytes(completed)),
        })

    def _record_failed(self, context: "_MutationContext", receipt_ref: str, old_oid: str | None, error: DomainError, evidence: list[EvidenceRef]) -> None:
        if old_oid is None:
            return
        failed = _Receipt(context.fingerprint, context.kind, "failed", context.target_ref, context.expected_target_oid, None, context.source_ref, context.source_oid, False, error.category.value)
        self._helper(context, evidence, "fail-receipt", {
            "action": "replace_receipt", "receipt_ref": receipt_ref,
            "old_receipt_oid": old_oid, "receipt": _b64(_receipt_bytes(failed)),
        })

    def _record_checkout_failed(self, context: "_MutationContext", receipt_ref: str, old_oid: str, receipt: _Receipt, error: DomainError, evidence: list[EvidenceRef]) -> None:
        failed = _Receipt(receipt.fingerprint, receipt.kind, "checkout_failed", receipt.target_ref, receipt.before_oid, receipt.result_oid, receipt.source_ref, receipt.source_oid, receipt.changed, error.category.value)
        self._helper(context, evidence, "fail-checkout-receipt", {
            "action": "replace_receipt", "receipt_ref": receipt_ref,
            "old_receipt_oid": old_oid, "receipt": _b64(_receipt_bytes(failed)),
        })

    def _read_receipt(self, context: "_MutationContext", receipt_ref: str, evidence: list[EvidenceRef]) -> tuple[_Receipt | None, str | None] | DomainError:
        ref = self._exact_ref(context, receipt_ref, evidence)
        if isinstance(ref, DomainError):
            return ref
        if ref[0] is GitRefStatus.MISSING:
            return None, None
        assert ref[1] is not None
        outcome = self._git(context, evidence, "read-receipt", "cat-file", "blob", ref[1])
        if not outcome.usable or outcome.exit_code != 0:
            return _error(ErrorCategory.AMBIGUOUS_SIDE_EFFECT, "Git operation receipt content is unavailable", evidence)
        try:
            return _parse_receipt(outcome.stdout), ref[1]
        except (KeyError, TypeError, ValueError, UnicodeError, json.JSONDecodeError):
            return _error(ErrorCategory.AMBIGUOUS_SIDE_EFFECT, "Git operation receipt content is invalid", evidence)

    def _exact_ref(self, context: object, ref: str, evidence: list[EvidenceRef]) -> tuple[GitRefStatus, str | None] | DomainError:
        exists = self._git(context, evidence, "observe-ref-exists", "show-ref", "--verify", "--quiet", ref)
        if not exists.usable:
            return _error(ErrorCategory.AMBIGUOUS_SIDE_EFFECT if exists.ambiguous else ErrorCategory.INTERNAL_ERROR, "Git ref observation is unavailable", evidence)
        if exists.exit_code == 1:
            return GitRefStatus.MISSING, None
        if exists.exit_code != 0:
            return _error(ErrorCategory.INTERNAL_ERROR, "Git could not inspect an exact ref", evidence)
        outcome = self._git(context, evidence, "observe-ref-oid", "show-ref", "--verify", "--hash", ref)
        if not outcome.usable:
            return _error(ErrorCategory.AMBIGUOUS_SIDE_EFFECT if outcome.ambiguous else ErrorCategory.INTERNAL_ERROR, "Git ref observation is unavailable", evidence)
        if outcome.exit_code != 0:
            return _error(ErrorCategory.INTERNAL_ERROR, "Git could not inspect an exact ref", evidence)
        oid = _single_oid(outcome.stdout)
        if oid is None:
            return _error(ErrorCategory.INTERNAL_ERROR, "Git returned an invalid ref OID", evidence)
        return GitRefStatus.PRESENT, oid

    def _symbolic_ref(self, context: object, ref: str, evidence: list[EvidenceRef]) -> str | None | DomainError:
        outcome = self._git(context, evidence, "observe-symbolic-ref", "symbolic-ref", "-q", ref)
        if not outcome.usable:
            return _error(ErrorCategory.AMBIGUOUS_SIDE_EFFECT if outcome.ambiguous else ErrorCategory.INTERNAL_ERROR, "Git symbolic ref observation is unavailable", evidence)
        if outcome.exit_code == 1:
            return None
        if outcome.exit_code != 0:
            return _error(ErrorCategory.INTERNAL_ERROR, "Git could not inspect symbolic ref identity", evidence)
        try:
            target = outcome.stdout.decode("ascii").strip()
        except UnicodeDecodeError:
            return _error(ErrorCategory.UNSUPPORTED_CAPABILITY, "symbolic ref target is not ASCII", evidence)
        if target == "HEAD" or not _valid_ref(target):
            return _error(ErrorCategory.INTERNAL_ERROR, "Git returned an invalid symbolic ref target", evidence)
        return target

    def _resolve_named_commit(self, context: object, requested: str, evidence: list[EvidenceRef]) -> tuple[str, str] | DomainError:
        if requested == "HEAD":
            oid_result = self._git(context, evidence, "resolve-head-oid", "rev-parse", "--verify", "HEAD^{commit}")
            if not oid_result.usable:
                return _error(ErrorCategory.AMBIGUOUS_SIDE_EFFECT, "source HEAD resolution is unavailable", evidence)
            oid = _single_oid(oid_result.stdout)
            if oid_result.exit_code != 0 or oid is None:
                return _error(ErrorCategory.GIT_CONFLICT, "source HEAD is missing or is not a commit", evidence)
            return requested, oid
        observed = self._exact_ref(context, requested, evidence)
        if isinstance(observed, DomainError):
            return observed
        if observed[0] is not GitRefStatus.PRESENT or observed[1] is None:
            return _error(ErrorCategory.GIT_CONFLICT, "source ref is missing", evidence)
        object_type = self._git(context, evidence, "resolve-ref-type", "cat-file", "-t", observed[1])
        if not object_type.usable:
            return _error(ErrorCategory.AMBIGUOUS_SIDE_EFFECT, "source object type is unavailable", evidence)
        if object_type.exit_code != 0 or object_type.stdout != b"commit\n":
            return _error(ErrorCategory.GIT_CONFLICT, "source ref does not point directly to a commit", evidence)
        return requested, observed[1]

    def _checked_out_paths(self, context: "_MutationContext", evidence: list[EvidenceRef]) -> tuple[Path, ...] | DomainError:
        outcome = self._git(context, evidence, "checked-out-refs", "worktree", "list", "--porcelain", "-z")
        if not outcome.usable or outcome.exit_code != 0:
            return _error(ErrorCategory.AMBIGUOUS_SIDE_EFFECT, "registered worktrees could not be inspected", evidence)
        try:
            facts = _parse_worktrees(outcome.stdout)
        except (TypeError, ValueError, UnicodeError):
            return _error(ErrorCategory.UNSUPPORTED_CAPABILITY, "registered worktrees include an unrepresentable path", evidence)
        try:
            return tuple(Path(os.path.abspath(fact.path)).resolve(strict=True) for fact in facts if fact.branch == context.target_ref)
        except (OSError, ValueError):
            return _error(ErrorCategory.AMBIGUOUS_SIDE_EFFECT, "a checked-out target path cannot be resolved", evidence)

    def _commit_parents(self, context: object, oid: str, evidence: list[EvidenceRef]) -> tuple[str, ...] | None:
        outcome = self._git(context, evidence, "commit-parents", "rev-list", "--parents", "-n", "1", oid)
        if not outcome.usable or outcome.exit_code != 0:
            return None
        fields = outcome.stdout.decode("ascii", "strict").strip().split()
        if not fields or fields[0] != oid or any(_OID.fullmatch(item) is None for item in fields):
            return None
        return tuple(fields[1:])

    def _head_for_project(self, context: "_MutationContext", evidence: list[EvidenceRef]) -> GitHead | None:
        request = _InspectLike(context, self._project)
        result = self._observe_head(request, evidence)
        return None if isinstance(result, DomainError) else result[0]

    def _observe_head(self, request: object, evidence: list[EvidenceRef]) -> tuple[GitHead, str | None] | DomainError:
        symbolic = self._git(request, evidence, "inspect-head-symbolic", "symbolic-ref", "-q", "HEAD")
        oid_result = self._git(request, evidence, "inspect-head-oid", "rev-parse", "--verify", "--quiet", "HEAD^{commit}")
        if not symbolic.usable or not oid_result.usable:
            return _error(ErrorCategory.AMBIGUOUS_SIDE_EFFECT, "HEAD observation is unavailable", evidence)
        branch: str | None = None
        if symbolic.exit_code == 0:
            try:
                branch = symbolic.stdout.decode("ascii").strip()
            except UnicodeDecodeError:
                return _error(ErrorCategory.UNSUPPORTED_CAPABILITY, "HEAD branch is not ASCII", evidence)
            if not _valid_ref(branch):
                return _error(ErrorCategory.INTERNAL_ERROR, "Git returned an invalid symbolic HEAD", evidence)
            if not branch.startswith("refs/heads/"):
                return _error(ErrorCategory.UNSUPPORTED_CAPABILITY, "symbolic HEAD does not name a local branch", evidence)
        elif symbolic.exit_code not in {1, 128}:
            return _error(ErrorCategory.INTERNAL_ERROR, "Git symbolic HEAD query failed", evidence)
        oid = _single_oid(oid_result.stdout) if oid_result.exit_code == 0 else None
        if oid_result.exit_code not in {0, 1, 128}:
            return _error(ErrorCategory.INTERNAL_ERROR, "Git HEAD OID query failed", evidence)
        if branch is not None and oid is not None:
            return GitHead(GitHeadStatus.ATTACHED, _short_branch(branch), oid), branch
        if branch is not None:
            return GitHead(GitHeadStatus.UNBORN, _short_branch(branch), None), branch
        if oid is not None:
            return GitHead(GitHeadStatus.DETACHED, None, oid), None
        return GitHead(GitHeadStatus.MISSING, None, None), None

    def _observe_ancestry(self, request: object, query: AncestryQuery, evidence: list[EvidenceRef]) -> AncestryObservation | DomainError:
        for oid in (query.ancestor_oid, query.descendant_oid):
            exists = self._git(request, evidence, "inspect-object", "cat-file", "-e", f"{oid}^{{commit}}")
            if not exists.usable:
                return _error(ErrorCategory.AMBIGUOUS_SIDE_EFFECT, "ancestry object observation is unavailable", evidence)
            if exists.exit_code != 0:
                return AncestryObservation(query, AncestryStatus.MISSING)
        result = self._git(request, evidence, "inspect-ancestry", "merge-base", "--is-ancestor", query.ancestor_oid, query.descendant_oid)
        if not result.usable:
            return _error(ErrorCategory.AMBIGUOUS_SIDE_EFFECT, "ancestry query is unavailable", evidence)
        if result.exit_code == 0:
            return AncestryObservation(query, AncestryStatus.ANCESTOR)
        if result.exit_code == 1:
            return AncestryObservation(query, AncestryStatus.NOT_ANCESTOR)
        return AncestryObservation(query, AncestryStatus.UNKNOWN)

    def _helper(self, context: object, evidence: list[EvidenceRef], label: str, payload: dict[str, object]) -> _CommandOutcome:
        encoded = _b64(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        environment = (EnvironmentBinding("PYTHONPATH", str(self._runtime.module_root), sensitive=False),)
        return self._run(
            context, evidence, label, PermissionClass.LOCAL_EXECUTE,
            self._runtime.python_executable, "-P", "-B", "-m", "git_ops",
            _HELPER_MARKER, self._runtime.git_executable, encoded,
            environment=environment,
        )

    def _git(self, context: object, evidence: list[EvidenceRef], label: str, *args: str) -> _CommandOutcome:
        return self._run(context, evidence, label, PermissionClass.LOCAL_READ, self._runtime.git_executable, "--no-optional-locks", *args)

    def _git_binding(self, context: object, binding: LocalWorktreeBinding, evidence: list[EvidenceRef], label: str, permission: PermissionClass, *args: str) -> _CommandOutcome:
        return self._run(context, evidence, label, permission, self._runtime.git_executable, "--no-optional-locks", *args, binding=binding)

    def _run(
        self,
        context: object,
        evidence: list[EvidenceRef],
        label: str,
        permission: PermissionClass,
        *argv: str,
        environment: tuple[EnvironmentBinding, ...] = (),
        binding: LocalWorktreeBinding | LocalControlBinding | None = None,
    ) -> _CommandOutcome:
        plan_id = getattr(context, "plan_id", None)
        run_id = getattr(context, "run_id")
        operation_id = getattr(context, "operation_id", EntityId(f"git-inspect-{run_id.value}"))
        if binding is None:
            target = getattr(context, "target", self._project)
            binding = target if isinstance(target, (LocalWorktreeBinding, LocalControlBinding)) else None
        rule = CommandCwdRule.PROJECT
        roots = CommandRootBindings(self._project)
        if isinstance(binding, LocalWorktreeBinding):
            rule = CommandCwdRule.WORKTREE
            roots = CommandRootBindings(self._project, worktree=binding)
        elif isinstance(binding, LocalControlBinding):
            rule = CommandCwdRule.CONTROL
            roots = CommandRootBindings(self._project, control=binding)
        definition = CommandDefinition(
            id=EntityId(f"git-{label}"), argv=tuple(argv), cwd_rule=rule,
            timeout_seconds=self._timeout, max_output_bytes=_MAX_OUTPUT_BYTES,
            permission_class=permission,
            environment_bindings=tuple(item.name for item in environment),
            platforms=(CommandPlatform.WINDOWS, CommandPlatform.LINUX),
            success_rule=CommandSuccessRule.EXIT_ZERO,
        )
        request = CommandRequest(
            project_id=self._project.project_id, plan_id=plan_id, run_id=run_id,
            operation_id=operation_id, definition=definition, roots=roots,
            cwd_relative=".", environment=environment,
        )
        try:
            result = self._runner.execute(request)
        except Exception:
            return _CommandOutcome(None, b"", b"", (), False, True, "runner raised")
        if not isinstance(result, CommandEvidence):
            return _CommandOutcome(None, b"", b"", (), False, True, "runner returned another type")
        references: list[EvidenceRef] = []
        outputs: list[bytes] = []
        for stream, reference in (("stdout", result.stdout_ref), ("stderr", result.stderr_ref)):
            if reference is None:
                return _CommandOutcome(result, b"", b"", tuple(references), False, True, "command output reference is missing")
            try:
                content = self._reader.read(reference)
            except Exception:
                return _CommandOutcome(result, b"", b"", tuple(references), False, True, "command output digest could not be verified")
            outputs.append(content)
            references.append(EvidenceRef(reference.path, reference.sha256, FrozenJsonObject({"command_evidence_id": result.id.value, "stream": stream})))
        evidence.extend(references)
        identity_ok = (
            result.command_id == definition.id
            and result.argv_redacted == definition.argv
            and result.cwd_relative == "."
            and result.cwd_worktree_id == (
                binding.worktree_id if isinstance(binding, (LocalWorktreeBinding, LocalControlBinding))
                else self._project.project_id
            )
            and result.environment_binding_names == tuple(item.name for item in environment)
            and not result.redactions_applied
            and not result.output_truncated
        )
        status_ok = result.status is CommandStatus.EXITED and result.exit_code is not None
        usable = identity_ok and status_ok
        ambiguous = result.status in {CommandStatus.RUNNING, CommandStatus.TIMED_OUT, CommandStatus.CANCELLED, CommandStatus.UNKNOWN} or not identity_ok
        return _CommandOutcome(result, outputs[0], outputs[1], tuple(references), usable, ambiguous, None if usable else "command evidence is incomplete")

    def _check_project(self, project_id: EntityId, target: GitTarget) -> None:
        if project_id != self._project.project_id or target.project_id != project_id:
            raise ValueError("Git request belongs to another project")
        if isinstance(target, LocalProjectBinding):
            root = target.root
        else:
            root = target.root
        configured = Path(os.path.abspath(self._project.root)).resolve(strict=True)
        selected = Path(os.path.abspath(root)).resolve(strict=True)
        if isinstance(target, LocalProjectBinding) and selected != configured:
            raise ValueError("repository binding does not match the configured project")
        if not selected.is_relative_to(configured):
            raise ValueError("Git target is outside the configured project")

    @staticmethod
    def _head_file_missing(root: Path) -> bool | None:
        root = Path(root)
        marker = root / ".git"
        try:
            if marker.is_dir():
                git_dir = marker.resolve(strict=True)
            elif marker.is_file():
                data = marker.read_text(encoding="utf-8", errors="strict")
                if not data.startswith("gitdir: "):
                    return None
                git_dir = Path(data[8:].strip())
                if not git_dir.is_absolute():
                    git_dir = marker.parent / git_dir
                git_dir = git_dir.resolve(strict=True)
            elif (root / "objects").is_dir() and (root / "refs").is_dir():
                git_dir = root.resolve(strict=True)
            else:
                return None

            common_dir = git_dir
            common_marker = git_dir / "commondir"
            if common_marker.is_file():
                common_value = common_marker.read_text(encoding="utf-8", errors="strict").strip()
                if not common_value:
                    return None
                common_dir = Path(common_value)
                if not common_dir.is_absolute():
                    common_dir = git_dir / common_dir
                common_dir = common_dir.resolve(strict=True)
                backlink = git_dir / "gitdir"
                if not backlink.is_file():
                    return None
                backlink_path = Path(backlink.read_text(encoding="utf-8", errors="strict").strip())
                if not backlink_path.is_absolute():
                    backlink_path = git_dir / backlink_path
                if backlink_path.resolve(strict=True) != marker.resolve(strict=True):
                    return None
            if not (common_dir / "objects").is_dir() or not (common_dir / "refs").is_dir():
                return None
            return not (git_dir / "HEAD").is_file()
        except (OSError, UnicodeError, ValueError):
            return None

    def _snapshot_command_failure(self, request: GitInspectRequest, observed_at: object, evidence: list[EvidenceRef], outcome: _CommandOutcome, head: GitHead | None, refs: list[GitRefObservation] | None = None, ancestry: list[AncestryObservation] | None = None, working_tree: GitStatus | None = None) -> GitSnapshot:
        category = ErrorCategory.AMBIGUOUS_SIDE_EFFECT if outcome.ambiguous else ErrorCategory.INTERNAL_ERROR
        return self._snapshot_failure(request, observed_at, evidence, head, category, "required Git command evidence is unavailable", refs, ancestry, working_tree)

    def _snapshot_error(self, request: GitInspectRequest, observed_at: object, evidence: list[EvidenceRef], error: DomainError, head: GitHead | None = None, refs: list[GitRefObservation] | None = None, ancestry: list[AncestryObservation] | None = None) -> GitSnapshot:
        status = ResultStatus.UNKNOWN if error.category is ErrorCategory.AMBIGUOUS_SIDE_EFFECT else ResultStatus.FAILED
        return GitSnapshot(status, request.project_id, request.run_id, request.target, head, tuple(refs or ()), tuple(ancestry or ()), (), None, observed_at, tuple(evidence), error)

    def _snapshot_failure(self, request: GitInspectRequest, observed_at: object, evidence: list[EvidenceRef], head: GitHead | None, category: ErrorCategory, message: str, refs: list[GitRefObservation] | None = None, ancestry: list[AncestryObservation] | None = None, working_tree: GitStatus | None = None) -> GitSnapshot:
        error = _error(category, message, evidence)
        status = ResultStatus.UNKNOWN if category is ErrorCategory.AMBIGUOUS_SIDE_EFFECT else ResultStatus.FAILED
        return GitSnapshot(status, request.project_id, request.run_id, request.target, head, tuple(refs or ()), tuple(ancestry or ()), (), working_tree, observed_at, tuple(evidence), error)

    def _operation_error(self, context: "_MutationContext", evidence: list[EvidenceRef], error: DomainError, changed: bool | None) -> GitOperationResult:
        status = ResultStatus.UNKNOWN if error.category is ErrorCategory.AMBIGUOUS_SIDE_EFFECT else ResultStatus.FAILED
        head: GitHead | None = None
        refs: tuple[GitRefObservation, ...] = ()
        ancestry: tuple[AncestryObservation, ...] = ()
        if status is not ResultStatus.UNKNOWN and error.category is not ErrorCategory.INVALID_INPUT:
            observed = self._exact_ref(context, context.target_ref, evidence)
            if not isinstance(observed, DomainError):
                refs = (GitRefObservation(context.target_ref, observed[0], observed[1]),)
                head = self._head_for_project(context, evidence)
                if context.kind == "merge" and observed[1] is not None:
                    query = AncestryQuery(context.source_oid, observed[1])
                    relationship = self._observe_ancestry(context, query, evidence)
                    if isinstance(relationship, AncestryObservation):
                        ancestry = (relationship,)
        return GitOperationResult(status, context.operation_id, context.idempotency_key, None if status is ResultStatus.UNKNOWN else changed, head, refs, ancestry, tuple(evidence), error)

    def _unknown(self, context: "_MutationContext", evidence: list[EvidenceRef], message: str) -> GitOperationResult:
        return self._operation_error(context, evidence, _error(ErrorCategory.AMBIGUOUS_SIDE_EFFECT, message, evidence), None)


@dataclass(frozen=True, slots=True)
class _InspectLike:
    source: object
    target: GitTarget

    @property
    def project_id(self) -> EntityId:
        return getattr(self.source, "project_id")

    @property
    def plan_id(self) -> object:
        return getattr(self.source, "plan_id", None)

    @property
    def run_id(self) -> EntityId:
        return getattr(self.source, "run_id")

    @property
    def operation_id(self) -> EntityId:
        return getattr(self.source, "operation_id")


@dataclass(frozen=True, slots=True)
class _MutationContext:
    kind: str
    project_id: EntityId
    plan_id: object
    run_id: EntityId
    operation_id: EntityId
    idempotency_key: str
    source_ref: str
    source_oid: str
    target_ref: str
    expected_target_status: GitRefStatus
    expected_target_oid: str | None
    fingerprint: str

    @classmethod
    def from_branch(cls, request: BranchRequest, target_ref: str, fingerprint: str) -> "_MutationContext":
        source_ref = _requested_ref(request.source_ref)
        return cls("branch", request.project_id, request.plan_id, request.run_id, request.operation_id, request.idempotency_key, source_ref, request.expected_base_oid, target_ref, request.expected_branch.status, request.expected_branch.oid, fingerprint)

    @classmethod
    def from_merge(cls, request: MergeRequest, target_ref: str, fingerprint: str) -> "_MutationContext":
        source_ref = _requested_ref(request.candidate_ref)
        return cls("merge", request.project_id, request.plan_id, request.run_id, request.operation_id, request.idempotency_key, source_ref, request.candidate_oid, target_ref, GitRefStatus.PRESENT, request.expected_integration_head_oid, fingerprint)

    def helper_payload(self, receipt_ref: str, intent_oid: str, phase: str) -> dict[str, object]:
        return {
            "action": "publish_branch" if self.kind == "branch" else "publish_merge",
            "source_ref": self.source_ref,
            "source_oid": self.source_oid,
            "target_ref": self.target_ref,
            "target_status": self.expected_target_status.value,
            "target_oid": self.expected_target_oid,
            "receipt_ref": receipt_ref,
            "intent_oid": intent_oid,
            "fingerprint": self.fingerprint,
            "phase": phase,
            "message": f"Integrate {self.source_oid} ({self.operation_id.value})",
        }


def _error(category: ErrorCategory, message: str, evidence: list[EvidenceRef]) -> DomainError:
    return DomainError(category, message, retryable=False, evidence_refs=tuple(evidence))


def _branch_ref(value: str) -> str:
    candidate = value[11:] if value.startswith("refs/heads/") else value
    result = f"refs/heads/{candidate}"
    if not _valid_ref(result):
        raise ValueError("branch is not a safe local ref")
    return result


def _short_branch(value: str) -> str:
    return value[11:] if value.startswith("refs/heads/") else value


def _requested_ref(value: str) -> str:
    if value == "HEAD" or value.startswith("refs/"):
        return value
    return f"refs/heads/{value}"


def _valid_ref(value: str) -> bool:
    if value == "HEAD":
        return True
    if not isinstance(value, str) or not _FULL_REF.fullmatch(value):
        return False
    parts = value.split("/")
    return (
        not any(token in value for token in ("..", "@{", "//"))
        and not value.endswith(("/", "."))
        and all(part and not part.startswith(".") and not part.endswith((".", ".lock")) for part in parts[1:])
    )


def _single_oid(content: bytes) -> str | None:
    try:
        value = content.decode("ascii").strip()
    except UnicodeDecodeError:
        return None
    return value if _OID.fullmatch(value) else None


def _decode_path(value: bytes) -> str:
    result = os.fsdecode(value)
    if not result or result.startswith(("/", "\\")) or result.endswith(("/", "\\")):
        raise ValueError("path is not an exact repository-relative file")
    if "\\" in result:
        raise ValueError("path contains an unrepresentable backslash")
    return result


def _parse_status(content: bytes) -> GitStatus:
    records = content.split(b"\0")
    if records and records[-1] == b"":
        records.pop()
    tracked: list[ScopePath] = []
    untracked: list[ScopePath] = []
    conflicted: list[ScopePath] = []
    index = 0
    while index < len(records):
        record = records[index]
        if record.startswith(b"1 "):
            fields = record.split(b" ", 8)
            if len(fields) != 9:
                raise ValueError("invalid ordinary status record")
            tracked.append(ScopePath.exact_file(_decode_path(fields[8])))
        elif record.startswith(b"2 "):
            fields = record.split(b" ", 9)
            if len(fields) != 10 or index + 1 >= len(records):
                raise ValueError("invalid rename/copy status record")
            tracked.append(ScopePath.exact_file(_decode_path(fields[9])))
            index += 1
            tracked.append(ScopePath.exact_file(_decode_path(records[index])))
        elif record.startswith(b"u "):
            fields = record.split(b" ", 10)
            if len(fields) != 11:
                raise ValueError("invalid unmerged status record")
            conflicted.append(ScopePath.exact_file(_decode_path(fields[10])))
        elif record.startswith(b"? "):
            untracked.append(ScopePath.exact_file(_decode_path(record[2:])))
        elif record.startswith(b"! "):
            pass
        elif record.startswith(b"# "):
            pass
        else:
            raise ValueError("unknown porcelain v2 status record")
        index += 1
    return GitStatus(tuple(tracked), tuple(untracked), tuple(conflicted))


def _parse_worktrees(content: bytes) -> tuple[GitWorktreeFact, ...]:
    records: list[dict[bytes, bytes]] = []
    current: dict[bytes, bytes] = {}
    for field in content.split(b"\0"):
        if not field:
            if current:
                records.append(current)
                current = {}
            continue
        key, separator, value = field.partition(b" ")
        if key == b"worktree" and current:
            records.append(current)
            current = {}
        if key in current:
            raise ValueError("duplicate worktree field")
        current[key] = value if separator else b""
    if current:
        records.append(current)
    facts: list[GitWorktreeFact] = []
    for record in records:
        if b"worktree" not in record:
            raise ValueError("worktree record has no path")
        path = Path(os.fsdecode(record[b"worktree"]))
        if not path.is_absolute():
            raise ValueError("worktree path is not absolute")
        raw_oid = record.get(b"HEAD", b"").decode("ascii", "strict")
        oid = None if raw_oid in {"", _ZERO_40, _ZERO_64} else raw_oid
        if oid is not None and _OID.fullmatch(oid) is None:
            raise ValueError("worktree HEAD is not a full OID")
        branch_raw = record.get(b"branch")
        branch = None if branch_raw is None else branch_raw.decode("ascii", "strict")
        if branch is not None and not _valid_ref(branch):
            raise ValueError("worktree branch is not an exact ref")
        facts.append(GitWorktreeFact(path, oid, branch, b"locked" in record, b"prunable" in record))
    return tuple(facts)


def _fingerprint(kind: str, request: BranchRequest | MergeRequest, target_ref: str) -> str:
    if isinstance(request, BranchRequest):
        value: dict[str, object] = {
            "kind": kind, "project_id": request.project_id.value,
            "plan_id": None if request.plan_id is None else request.plan_id.value,
            "run_id": request.run_id.value, "operation_id": request.operation_id.value,
            "idempotency_key": request.idempotency_key,
            "repository": os.path.normcase(os.path.abspath(request.repository.root)),
            "target_ref": target_ref, "source_ref": request.source_ref,
            "source_oid": request.expected_base_oid,
            "expected_status": request.expected_branch.status.value,
            "expected_target_oid": request.expected_branch.oid,
        }
    else:
        value = {
            "kind": kind, "project_id": request.project_id.value,
            "plan_id": request.plan_id.value, "run_id": request.run_id.value,
            "operation_id": request.operation_id.value,
            "idempotency_key": request.idempotency_key,
            "repository": os.path.normcase(os.path.abspath(request.repository.root)),
            "target_ref": target_ref, "source_ref": request.candidate_ref,
            "source_oid": request.candidate_oid,
            "expected_target_oid": request.expected_integration_head_oid,
        }
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _receipt_ref(project_id: EntityId, operation_id: EntityId) -> str:
    key = hashlib.sha256(f"{project_id.value}\0{operation_id.value}".encode("utf-8")).hexdigest()
    return f"refs/ai-toolkit/git-operations/{key}"


def _receipt_bytes(receipt: _Receipt) -> bytes:
    return (json.dumps({
        "version": _RECEIPT_VERSION, "fingerprint": receipt.fingerprint,
        "kind": receipt.kind, "phase": receipt.phase,
        "target_ref": receipt.target_ref, "before_oid": receipt.before_oid,
        "result_oid": receipt.result_oid, "source_ref": receipt.source_ref,
        "source_oid": receipt.source_oid, "changed": receipt.changed,
        "error_category": receipt.error_category,
    }, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _parse_receipt(content: bytes) -> _Receipt:
    raw = json.loads(content.decode("utf-8"))
    expected = {"version", "fingerprint", "kind", "phase", "target_ref", "before_oid", "result_oid", "source_ref", "source_oid", "changed", "error_category"}
    if not isinstance(raw, dict) or set(raw) != expected or raw["version"] != _RECEIPT_VERSION:
        raise ValueError("invalid receipt fields")
    receipt = _Receipt(raw["fingerprint"], raw["kind"], raw["phase"], raw["target_ref"], raw["before_oid"], raw["result_oid"], raw["source_ref"], raw["source_oid"], raw["changed"], raw["error_category"])
    if (
        not isinstance(receipt.fingerprint, str) or re.fullmatch(r"[a-f0-9]{64}", receipt.fingerprint) is None
        or receipt.kind not in {"branch", "merge"}
        or receipt.phase not in {"intent", "ref_published", "completed", "failed", "checkout_failed"}
        or receipt.target_ref == "HEAD" or not _valid_ref(receipt.target_ref) or not _valid_ref(receipt.source_ref)
        or _OID.fullmatch(receipt.source_oid) is None
        or receipt.before_oid is not None and _OID.fullmatch(receipt.before_oid) is None
        or receipt.result_oid is not None and _OID.fullmatch(receipt.result_oid) is None
        or receipt.changed is not None and not isinstance(receipt.changed, bool)
        or receipt.error_category is not None and receipt.error_category not in {item.value for item in ErrorCategory}
    ):
        raise ValueError("invalid receipt value")
    if receipt.phase in {"ref_published", "completed"} and (receipt.result_oid is None or receipt.changed is None):
        raise ValueError("published receipt has no result")
    if receipt.phase == "checkout_failed" and (receipt.result_oid is None or receipt.changed is None or receipt.error_category is None):
        raise ValueError("checkout failure receipt has no published result or error")
    if receipt.phase == "failed" and receipt.error_category is None:
        raise ValueError("failed receipt has no error category")
    if receipt.phase in {"intent", "ref_published", "completed"} and receipt.error_category is not None:
        raise ValueError("non-failure receipt cannot carry an error")
    return receipt


def _b64(content: bytes) -> str:
    return base64.urlsafe_b64encode(content).decode("ascii")


def _unb64(value: object) -> bytes:
    if not isinstance(value, str):
        raise ValueError("encoded content must be a string")
    return base64.b64decode(value.encode("ascii"), altchars=b"-_", validate=True)


def _git_blob_oid(content: bytes, reference_oid: str) -> str:
    algorithm = "sha256" if len(reference_oid) == 64 else "sha1"
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.new(algorithm, header + content).hexdigest()


def _helper_main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[0] != _HELPER_MARKER:
        return 64
    git_executable, encoded = argv[1], argv[2]
    if not git_executable or "\x00" in git_executable:
        return 64
    try:
        payload = json.loads(_unb64(encoded).decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")
        action = payload.get("action")
        if action == "write_intent":
            return _helper_write_intent(git_executable, payload)
        if action == "replace_receipt":
            return _helper_replace_receipt(git_executable, payload)
        if action in {"publish_branch", "publish_merge"}:
            return _helper_publish(git_executable, payload)
    except (KeyError, TypeError, ValueError, UnicodeError, json.JSONDecodeError):
        return 64
    return 64


def _child(git_executable: str, *args: str, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run((git_executable, *args), input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, check=False)


def _hash_receipt(git_executable: str, content: bytes) -> str:
    result = _child(git_executable, "hash-object", "-w", "--stdin", input_bytes=content)
    if result.returncode != 0:
        raise ValueError("could not store receipt")
    oid = _single_oid(result.stdout)
    if oid is None:
        raise ValueError("invalid receipt blob oid")
    return oid


def _helper_write_intent(git_executable: str, payload: dict[str, object]) -> int:
    if set(payload) != {"action", "receipt_ref", "receipt"}:
        return 64
    ref = _helper_ref(payload["receipt_ref"])
    content = _unb64(payload["receipt"])
    _parse_receipt(content)
    oid = _hash_receipt(git_executable, content)
    return _update_transaction(git_executable, (("create", ref, oid, None),))


def _helper_replace_receipt(git_executable: str, payload: dict[str, object]) -> int:
    if set(payload) != {"action", "receipt_ref", "old_receipt_oid", "receipt"}:
        return 64
    ref = _helper_ref(payload["receipt_ref"])
    old = _helper_oid(payload["old_receipt_oid"])
    content = _unb64(payload["receipt"])
    _parse_receipt(content)
    oid = _hash_receipt(git_executable, content)
    return _update_transaction(git_executable, (("update", ref, oid, old),))


def _helper_publish(git_executable: str, payload: dict[str, object]) -> int:
    required = {"action", "source_ref", "source_oid", "target_ref", "target_status", "target_oid", "receipt_ref", "intent_oid", "fingerprint", "phase", "message"}
    if set(payload) != required:
        return 64
    action = payload["action"]
    source_ref = _helper_ref(payload["source_ref"], allow_head=True)
    source_oid = _helper_oid(payload["source_oid"])
    target_ref = _helper_ref(payload["target_ref"])
    receipt_ref = _helper_ref(payload["receipt_ref"])
    intent_oid = _helper_oid(payload["intent_oid"])
    target_status = payload["target_status"]
    target_oid = None if payload["target_oid"] is None else _helper_oid(payload["target_oid"])
    fingerprint = payload["fingerprint"]
    phase = payload["phase"]
    message = payload["message"]
    if not isinstance(fingerprint, str) or re.fullmatch(r"[a-f0-9]{64}", fingerprint) is None or phase not in {"completed", "ref_published"} or not isinstance(message, str) or not message or "\x00" in message:
        return 64
    current_source = _child(git_executable, "show-ref", "--verify", "--hash", source_ref)
    if current_source.returncode != 0 or _single_oid(current_source.stdout) != source_oid:
        return 20
    changed = target_oid != source_oid
    result_oid = source_oid
    if action == "publish_merge" and changed:
        if target_oid is None:
            return 64
        merged_tree = _child(git_executable, "merge-tree", "--write-tree", target_oid, source_oid)
        if merged_tree.returncode == 1:
            return 21
        tree_oid = _single_oid(merged_tree.stdout.splitlines()[0] + b"\n") if merged_tree.stdout else None
        if merged_tree.returncode != 0 or tree_oid is None:
            return 22
        commit = _child(git_executable, "commit-tree", tree_oid, "-p", target_oid, "-p", source_oid, "-m", message)
        result_oid = _single_oid(commit.stdout)
        if commit.returncode != 0 or result_oid is None:
            return 22
        changed = True
    elif action == "publish_merge":
        changed = False
    receipt = _Receipt(fingerprint, "branch" if action == "publish_branch" else "merge", phase, target_ref, target_oid, result_oid, source_ref, source_oid, changed, None)
    receipt_oid = _hash_receipt(git_executable, _receipt_bytes(receipt))
    transaction_source_ref = source_ref
    if source_ref == "HEAD":
        symbolic = _child(git_executable, "symbolic-ref", "-q", "HEAD")
        if symbolic.returncode == 0:
            try:
                transaction_source_ref = _helper_ref(symbolic.stdout.decode("ascii").strip())
            except (UnicodeError, ValueError):
                return 20
        elif symbolic.returncode != 1:
            return 20
    operations: list[tuple[str, str, str, str | None]] = [("verify", transaction_source_ref, source_oid, None)]
    if target_ref == transaction_source_ref:
        if target_oid != source_oid:
            return 20
    elif target_status == GitRefStatus.PRESENT.value:
        if target_oid is None:
            return 64
        if result_oid != target_oid:
            operations.append(("update", target_ref, result_oid, target_oid))
        else:
            operations.append(("verify", target_ref, target_oid, None))
    elif target_status in {GitRefStatus.MISSING.value, GitRefStatus.UNBORN.value}:
        if target_oid is not None:
            return 64
        operations.append(("create", target_ref, result_oid, None))
    else:
        return 64
    operations.append(("update", receipt_ref, receipt_oid, intent_oid))
    published = _update_transaction(git_executable, tuple(operations))
    return 0 if published == 0 else 20


def _helper_ref(value: object, *, allow_head: bool = False) -> str:
    if not isinstance(value, str) or not _valid_ref(value) or value == "HEAD" and not allow_head:
        raise ValueError("invalid helper ref")
    return value


def _helper_oid(value: object) -> str:
    if not isinstance(value, str) or _OID.fullmatch(value) is None:
        raise ValueError("invalid helper oid")
    return value


def _update_transaction(git_executable: str, operations: tuple[tuple[str, str, str, str | None], ...]) -> int:
    lines = ["start"]
    seen: set[str] = set()
    for action, ref, new_or_old, old in operations:
        if ref in seen:
            return 64
        seen.add(ref)
        if action == "verify":
            lines.append(f"verify {ref} {new_or_old}")
        elif action == "create":
            lines.append(f"create {ref} {new_or_old}")
        elif action == "update" and old is not None:
            lines.append(f"update {ref} {new_or_old} {old}")
        else:
            return 64
    lines.extend(("prepare", "commit", ""))
    result = _child(git_executable, "update-ref", "--no-deref", "--stdin", input_bytes="\n".join(lines).encode("ascii"))
    sys.stdout.buffer.write(result.stdout)
    sys.stderr.buffer.write(result.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(_helper_main(sys.argv[1:]))


__all__ = [
    "ContentReader",
    "FileContentReader",
    "GitRuntimeBinding",
    "LocalGitRepository",
    "ManagedIntegrationBinding",
]
