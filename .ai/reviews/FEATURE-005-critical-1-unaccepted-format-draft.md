---
subject: FEATURE-005
iteration: 1
status: CHANGES_REQUIRED
base: 90ab58b39f1a84ab1827ef0b72a25c72159447eb
head: 9eef3fc1b2d23fcfb42d5034a9a784c707e852a2
reviewer_session: critical-review-feature005-20260909-1
implementer_session: native-execution-orchestration
summary: Four blocking issues remain in destination binding, uncertain-delivery recovery,
  safe recovery resume, and durable requirements binding.
issues:
- id: REVIEW-001
  category: security
  files:
  - src/ai_engineering/delivery.py:112
  - src/ai_engineering/delivery.py:149
  - src/ai_engineering/delivery.py:190
  - tests/test_orchestration.py
  explanation: The delivery receipt binds only the remote nickname, and gh operations
    use implicit repository context. A local remote URL or gh destination change between
    attempts therefore does not invalidate the receipt. In a temporary Git repository,
    an uncertain controlled push went to repository A; after changing the real remote.origin.url
    to repository B, the same receipt accepted B branch evidence and created/confirmed
    a PR in B. It combined two repositories into one supposedly reconciled delivery
    without a new destination binding.
  required_change: Resolve and bind the selected push destination and explicit PR
    repository identity before external intent. Verify those identities on every resumed
    observation/write, refuse a destination change, and issue PR observations/creation
    against the bound repository. Keep credentials out of persisted identities and
    preserve pending-authority PR-body preparation. Document how intentional fork/base
    repository pairs are selected; do not infer that a matching commit proves the
    same repository.
  validation_required: Use controlled adapters with real local Git remote configuration
    to interrupt a push/PR and then change origin URL, push URL, or gh repository
    context. Each changed destination must block without a new external write or false
    confirmation. Unchanged destinations must still reconcile without duplicate pushes
    or PRs.
- id: REVIEW-002
  category: security
  files:
  - src/ai_engineering/orchestrator.py:980
  - src/ai_engineering/orchestrator.py:703
  - src/ai_engineering/delivery.py:173
  - tests/test_orchestration.py
  explanation: Recovery checks only journal.delivery.status. The subject journal receives
    delivery evidence only after deliver returns. If delivery raises after persisting
    push/PR intent, the durable delivery receipt can be pending while journal.delivery
    is absent or stale. A two-feature probe made FEATURE-001 structural and interrupted
    FEATURE-002 after accepted push intent with an OSError. Recovery nevertheless
    invoked its hook with status quiescent and both features stopped, although FEATURE-002
    had an on-disk delivery receipt with status pending and push pending. This permits
    superseding work whose external effects remain unknown.
  required_change: Before authorizing recovery, inspect and bind durable delivery
    intents/receipts as well as invocation results for every affected subject. Pending
    or uncertain effect fields must prevent recovery until reconciled, including cases
    where the worker journal never received the receipt. Treat not_started authority-pending
    delivery separately from a started but unconfirmed effect. Include sufficient
    durable delivery evidence in the quiescence contract for recovery to verify it.
  validation_required: Interrupt after persisted push intent and after persisted PR-create
    intent, both before and after effects, while another feature requests structural
    recovery. Verify recovery is not called and no artifacts are superseded until
    the exact delivery is reconciled. Also cover an absent/stale journal.delivery
    and a harmless not_started receipt.
- id: REVIEW-003
  category: correctness
  files:
  - src/ai_engineering/orchestrator.py:1031
  - src/ai_engineering/orchestrator.py:1048
  - src/ai_engineering/orchestrator.py:1088
  - tests/test_orchestration.py
  explanation: 'The coordinator marks recovery pending before invoking the hook, then
    unconditionally refuses every pending recovery on resume. A recover hook that
    fails during provider preflight with no invocation, external delivery, or graph
    mutation is therefore permanently classified as uncertain application. A single
    structural-feature probe reproduced this: the first call returned the preflight
    blocker, fixing the hook and resuming still raised Uncertain recovery application,
    and the hook remained called once. This prevents autonomous recovery from a recoverable
    setup failure or a proven synchronous rollback. The receipt generation is also
    captured before blocking/index updates: the observed receipt generation was 9
    while STATE was 11 when the hook received it, leaving downstream verification
    ambiguous.'
  required_change: Define durable recovery phases and a coordinator/hook protocol
    that distinguishes safe preflight or proven rejected/rolled-back work from applying
    or genuinely uncertain effects. Permit a verified safe retry of the same recovery
    attempt without charging the plan budget again; never blindly replay uncertain
    provider/application effects. Give the quiescence generation an explicit verification
    contract, preferably capturing the post-blocking state passed to the hook, and
    keep receipts immutable.
  validation_required: Test a preflight failure followed by repaired configuration,
    a synchronously rejected proposal, proven application rollback, and a genuine
    interrupted mutation/invocation. Safe cases must resume automatically with bounded
    unchanged attempt accounting; uncertain cases must remain blocked. Assert the
    receipt generation relationship at hook entry rather than accepting an undocumented
    offset.
- id: REVIEW-004
  category: correctness
  files:
  - src/ai_engineering/orchestrator.py:152
  - src/ai_engineering/orchestrator.py:175
  - src/ai_engineering/orchestrator.py:308
  - tests/test_orchestration.py
  explanation: The approved decomposition binding includes task/feature metadata but
    excludes their Markdown bodies unless another context entry happens to point to
    them; it also omits the contents of feature-only context references. In a temporary
    project, after a feature reached independent PASS, editing the TASK body to require
    a different value left the binding identical. implement then resumed with zero
    new agent calls and retained the old approved head. Markdown is the durable task/feature
    specification, so changed requirements can inherit an approval for older requirements.
  required_change: Bind the substantive Markdown body and relevant context content
    of every included plan/task/feature to approved decomposition and execution evidence,
    while excluding routine lifecycle metadata that the coordinator updates. Cover
    feature-only references and the standalone subject execution path where applicable.
    A material context change must invalidate the old approval and route to the defined
    revalidation/recovery path before dispatch, delivery, or completion.
  validation_required: Change only task prose, only feature prose, and only the contents
    of a feature-only referenced document after decomposition and after review. Verify
    the old binding/approval is rejected before further delivery or completion. Retain
    a regression proving that lifecycle folder moves and ordinary status/evidence
    updates do not spuriously invalidate unchanged requirements.
security_findings:
- 'REVIEW-001: delivery evidence is not bound to repository identity.'
- 'REVIEW-002: recovery can supersede work with unconfirmed external delivery intent.'
documentation_findings:
- Recovery phase/generation and destination identity contracts must describe the repaired
  behavior.
- 'Integration clarification: TASK-060 requires plan decompose, but there is no public
  semantic decomposition-only coordinator entry point. The current PLAN lists only
  implement/execute_subject, so this is an interface clarification for the coordinator,
  not an invented violation of an existing signature.'
validation:
- Independently inspected the complete six-file base..head diff and selected PLAN/FEATURE/TASK
  contracts.
- Independent temporary-Git probes reproduced all four blocking issues with controlled
  providers/delivery; no actual remote/provider service was used.
- 'Changed TASK prose: binding unchanged, resumed waiting, zero new agent calls, old
  head retained.'
- 'Real local remote.origin.url changed A to B after an uncertain simulated push:
  same receipt confirmed a PR at B.'
- 'Concurrent structural feature plus interrupted delivery: recovery hook received
  quiescent despite durable pending/pending push receipt and absent journal.delivery.'
- 'Separate one-feature recovery preflight probe: no delivery receipt or graph mutation;
  fixing hook did not permit retry, hook calls remained one.'
- Observed recovery receipt generation 9 versus current STATE generation 11 at hook
  entry.
- git diff --check passed; reviewed worktree remains clean at the exact assigned head.
- 'Implementer/coordinator supplied evidence, not rerun here: Windows orchestration
  17 passed, baseline 129 passed/2 symlink-privilege skips; independent Linux orchestration
  17 passed; lint/format/native 15-module and Linux affected-module type checks passed.'
---
# Critical Change Review

## Summary

CHANGES_REQUIRED. The complete updated feature diff was reviewed in the single independent critical stage. The batching, merge-based dependency gate, stable implementation repairs, serialized independent reviews, and scoped command paths are useful compatible work. Four concrete failure paths require repair before this feature is approved.

## Blocking issues

| Category | Location | Exact issue | Required fix |
| --- | --- | --- | --- |
| Security | delivery.py:112,149,190 | One receipt combines a push to repository A with a PR at repository B after destination changes. | Bind and verify resolved push and explicit PR repository identities. |
| Security | orchestrator.py:980 | Durable pending external effects are invisible to recovery when delivery never returned to the worker. | Verify authoritative delivery receipts before declaring quiescence. |
| Correctness | orchestrator.py:1031,1088 | A safe recovery preflight failure cannot resume because every pending attempt is treated as uncertain mutation. | Persist explicit recovery phases, safely retry the same attempt, and define generation verification. |
| Correctness | orchestrator.py:152,175 | Task/feature prose and feature-only context contents are omitted from approval bindings. | Bind all substantive durable requirements and invalidate stale approval. |

### REVIEW-001

Category: security

Files:
- src/ai_engineering/delivery.py:112
- src/ai_engineering/delivery.py:149
- src/ai_engineering/delivery.py:190
- tests/test_orchestration.py

Issue:
The delivery receipt binds only the remote nickname, and gh operations use implicit repository context. A local remote URL or gh destination change between attempts therefore does not invalidate the receipt. In a temporary Git repository, an uncertain controlled push went to repository A; after changing the real remote.origin.url to repository B, the same receipt accepted B branch evidence and created/confirmed a PR in B. It combined two repositories into one supposedly reconciled delivery without a new destination binding.

Required change:
Resolve and bind the selected push destination and explicit PR repository identity before external intent. Verify those identities on every resumed observation/write, refuse a destination change, and issue PR observations/creation against the bound repository. Keep credentials out of persisted identities and preserve pending-authority PR-body preparation. Document how intentional fork/base repository pairs are selected; do not infer that a matching commit proves the same repository.

Validation required:
Use controlled adapters with real local Git remote configuration to interrupt a push/PR and then change origin URL, push URL, or gh repository context. Each changed destination must block without a new external write or false confirmation. Unchanged destinations must still reconcile without duplicate pushes or PRs.

### REVIEW-002

Category: security

Files:
- src/ai_engineering/orchestrator.py:980
- src/ai_engineering/orchestrator.py:703
- src/ai_engineering/delivery.py:173
- tests/test_orchestration.py

Issue:
Recovery checks only journal.delivery.status. The subject journal receives delivery evidence only after deliver returns. If delivery raises after persisting push/PR intent, the durable delivery receipt can be pending while journal.delivery is absent or stale. A two-feature probe made FEATURE-001 structural and interrupted FEATURE-002 after accepted push intent with an OSError. Recovery nevertheless invoked its hook with status quiescent and both features stopped, although FEATURE-002 had an on-disk delivery receipt with status pending and push pending. This permits superseding work whose external effects remain unknown.

Required change:
Before authorizing recovery, inspect and bind durable delivery intents/receipts as well as invocation results for every affected subject. Pending or uncertain effect fields must prevent recovery until reconciled, including cases where the worker journal never received the receipt. Treat not_started authority-pending delivery separately from a started but unconfirmed effect. Include sufficient durable delivery evidence in the quiescence contract for recovery to verify it.

Validation required:
Interrupt after persisted push intent and after persisted PR-create intent, both before and after effects, while another feature requests structural recovery. Verify recovery is not called and no artifacts are superseded until the exact delivery is reconciled. Also cover an absent/stale journal.delivery and a harmless not_started receipt.

### REVIEW-003

Category: correctness

Files:
- src/ai_engineering/orchestrator.py:1031
- src/ai_engineering/orchestrator.py:1048
- src/ai_engineering/orchestrator.py:1088
- tests/test_orchestration.py

Issue:
The coordinator marks recovery pending before invoking the hook, then unconditionally refuses every pending recovery on resume. A recover hook that fails during provider preflight with no invocation, external delivery, or graph mutation is therefore permanently classified as uncertain application. A single structural-feature probe reproduced this: the first call returned the preflight blocker, fixing the hook and resuming still raised Uncertain recovery application, and the hook remained called once. This prevents autonomous recovery from a recoverable setup failure or a proven synchronous rollback. The receipt generation is also captured before blocking/index updates: the observed receipt generation was 9 while STATE was 11 when the hook received it, leaving downstream verification ambiguous.

Required change:
Define durable recovery phases and a coordinator/hook protocol that distinguishes safe preflight or proven rejected/rolled-back work from applying or genuinely uncertain effects. Permit a verified safe retry of the same recovery attempt without charging the plan budget again; never blindly replay uncertain provider/application effects. Give the quiescence generation an explicit verification contract, preferably capturing the post-blocking state passed to the hook, and keep receipts immutable.

Validation required:
Test a preflight failure followed by repaired configuration, a synchronously rejected proposal, proven application rollback, and a genuine interrupted mutation/invocation. Safe cases must resume automatically with bounded unchanged attempt accounting; uncertain cases must remain blocked. Assert the receipt generation relationship at hook entry rather than accepting an undocumented offset.

### REVIEW-004

Category: correctness

Files:
- src/ai_engineering/orchestrator.py:152
- src/ai_engineering/orchestrator.py:175
- src/ai_engineering/orchestrator.py:308
- tests/test_orchestration.py

Issue:
The approved decomposition binding includes task/feature metadata but excludes their Markdown bodies unless another context entry happens to point to them; it also omits the contents of feature-only context references. In a temporary project, after a feature reached independent PASS, editing the TASK body to require a different value left the binding identical. implement then resumed with zero new agent calls and retained the old approved head. Markdown is the durable task/feature specification, so changed requirements can inherit an approval for older requirements.

Required change:
Bind the substantive Markdown body and relevant context content of every included plan/task/feature to approved decomposition and execution evidence, while excluding routine lifecycle metadata that the coordinator updates. Cover feature-only references and the standalone subject execution path where applicable. A material context change must invalidate the old approval and route to the defined revalidation/recovery path before dispatch, delivery, or completion.

Validation required:
Change only task prose, only feature prose, and only the contents of a feature-only referenced document after decomposition and after review. Verify the old binding/approval is rejected before further delivery or completion. Retain a regression proving that lifecycle folder moves and ordinary status/evidence updates do not spuriously invalidate unchanged requirements.

## Security findings

The two security findings concern actual external-action evidence and the authority to replace work after a possibly completed external write. All reproductions intercepted external commands through local adapters. No credentials or live remote access were used. The existing exact ls-remote argv guard and seven protected control directories were inspected and remain appropriate within their approved scope.

## Documentation findings

The reusable decomposition output template and protected-directory seed match the approved planning contract. Repair the documented destination and recovery-phase/generation semantics alongside the code. Public CLI/config manuals remain FEATURE-007 scope.

The plan-decompose integration boundary needs an explicit coordinator entry point or supported mode that performs semantic decomposition and persistence without creating worktrees or starting implementation. Only implement and execute_subject are public today; planning.decompose is deterministic and cannot substitute for semantic approval. This is recorded for contract clarification, separately from the four reproduced blockers.

## Validation inspected and limits

- Independently inspected the complete six-file base..head diff and selected PLAN/FEATURE/TASK contracts.
- Independent temporary-Git probes reproduced all four blocking issues with controlled providers/delivery; no actual remote/provider service was used.
- Changed TASK prose: binding unchanged, resumed waiting, zero new agent calls, old head retained.
- Real local remote.origin.url changed A to B after an uncertain simulated push: same receipt confirmed a PR at B.
- Concurrent structural feature plus interrupted delivery: recovery hook received quiescent despite durable pending/pending push receipt and absent journal.delivery.
- Separate one-feature recovery preflight probe: no delivery receipt or graph mutation; fixing hook did not permit retry, hook calls remained one.
- Observed recovery receipt generation 9 versus current STATE generation 11 at hook entry.
- git diff --check passed; reviewed worktree remains clean at the exact assigned head.
- Implementer/coordinator supplied evidence, not rerun here: Windows orchestration 17 passed, baseline 129 passed/2 symlink-privilege skips; independent Linux orchestration 17 passed; lint/format/native 15-module and Linux affected-module type checks passed.
