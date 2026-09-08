# TASK-007 coordination reminders

Dispatch only after TASK-006 acceptance. Consume the accepted local_ports Git
DTOs and CommandRunner evidence rather than defining replacement request/result
shapes. Own only git_ops.py, the Git test leaf and TASK-007 handoff.

Inspect actual refs, attached/detached/unborn/missing HEAD, tracked/untracked/
conflicted paths, registered worktrees and queried ancestry. Use unambiguous Git
output such as NUL-delimited status/worktree records where supported. Do not split
paths on spaces or silently omit a pathname the portable DTO cannot represent.
An unsupported/unknown observation must remain explicit, not become clean/success.

Create branches and integration commits only under exact expected ref/head
conditions. Compare-and-update and re-observe mutation outcomes. A before/after
check alone must not silently turn a concurrent ref movement into successful
integration. Reused operation identities must not perform duplicate effects;
different requests under the same identity conflict. A lost outcome becomes
ambiguous until observation resolves it; changed=None means genuinely unknown.

Use fixed argv without a shell and defend option/ref interpretation. Record
observed command evidence and preserve no-plan branch setup where supported by
BranchRequest. Do not infer a desired ref from the caller's branch string when
actual Git contradicts it. Do not reset, stash or discard developer changes.

Test disposable actual repositories for missing/unborn/detached states, dirty
files, conflicts, registered worktrees, ancestry, stale expected heads, source or
target movement, successful conditional mutation and ambiguous command outcomes.
Later009 needs these observed facts for state checkpoints;011 owns managed task
worktrees and023 owns review-gated integration policy. Do not implement those
services or expand another task's source surface.

Local platform tools are available: Windows Git2.49.0.windows.1 and WSL Ubuntu
Git2.43.0. Linux Python with the declared dependency is at the workspace's
.ai/local/full-plan-linux-venv/bin/python. Use WSL --exec and candidate-local cwd
to preserve argv; avoid the default WSL shell. Verify platform-sensitive Git
behavior on both where applicable rather than claiming Linux from Windows tests.

Observed test-harness boundary: Windows-created linked worktrees contain a .git
pointer with a D:/ path. Native Linux Git does not resolve that pointer automatically.
Use native disposable Linux repositories for behavior tests; for read-only identity
inspection of the current Windows-created candidate, use Windows Git or correctly
mapped explicit --git-dir and --work-tree arguments. Do not alter .git pointers or
other worktree metadata to make a harness pass. The TASK-006 c2 R1 harness note
retains this setup diagnostic; it was not a product failure.

## Readiness advisory before implementation

Read ROOT/.ai/plans/current/PLAN-001/evidence/coordination/git-port-readiness.md.txt as bounded independent planning evidence,
not accepted source or a mandatory design. Actual disposable Windows/Linux probes
each passed8 feasibility checks through40 calls to the pending command runner.
Direct update-ref --stdin receives EOF because CommandRequest has no stdin.
A trusted finite Git-specific helper inside owned git_ops.py can transport validated
data in fixed argv and construct child Git stdin with shell=False. No port/schema
change is demonstrated necessary. Keep static imports and explicit trusted runtime
bindings so installed closure remains discoverable; do not hide imports in strings.
An outer CommandEvidence observes the helper; don't fabricate separate child evidence.
Required log bytes must be read through a bound digest-checking collaborator.

Conditional source verification and target CAS can share a guarded Git transaction;
merge-tree/commit-tree can construct integration objects without touching developer
index/files. A private request-hash receipt may support idempotent reconciliation,
but receipt existence alone cannot prove current target or crash atomicity. Reobserve
actual refs/parents/current target, preserve unknown changed=None when unresolved.
Same operation/different request conflicts; don't repeat an uncertain mutation.
Checked-out target policy must preserve developer work. The advisory does not prove
full idempotency, crash safety, installed execution or Python3.11 behavior; owned
implementation tests and fresh R1/R2 remain required. Do not expand scope to009.

## Integration-worktree compatibility to resolve during implementation

Read accepted local_ports.MergeRequest/GitRepository.merge alongside this
coordinator-verified consumer requirement: TASK-023 serially integrates into the
plan branch, and its frozen IntegrationRequest includes integration_worktree_id.
This is planning context, not a new import/dependency on orchestration_ports.
Do not freeze a blanket checked-out-target refusal without proving
how the existing managed integration workflow can still use the adapter. The
required boundary is preservation of developer files/index and exact expected
heads. An explicit trusted local binding/policy or supported plumbing route may
be possible within git_ops.py; choose from actual evidence, not this note. No new
port field, WorktreeManager implementation, unchecked reset, or contract waiver
is authorized. If a real required case is unrepresentable, return its minimal
typed/observed reproduction before crossing ownership. This is a consumer
compatibility question, not a demonstrated prerequisite gap or mandatory design.
