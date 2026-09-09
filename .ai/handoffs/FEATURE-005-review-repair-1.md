---
role: implementation
subject: FEATURE-005
review: .ai/reviews/FEATURE-005-critical-1.md
iteration: 1
issues:
- id: REVIEW-001
  category: security
  files:
  - src/ai_engineering/delivery.py
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
  - src/ai_engineering/orchestrator.py
  - src/ai_engineering/delivery.py
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
  - src/ai_engineering/orchestrator.py
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
  - src/ai_engineering/orchestrator.py
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
required_changes:
- Resolve and bind the selected push destination and explicit PR repository identity
  before external intent. Verify those identities on every resumed observation/write,
  refuse a destination change, and issue PR observations/creation against the bound
  repository. Keep credentials out of persisted identities and preserve pending-authority
  PR-body preparation. Document how intentional fork/base repository pairs are selected;
  do not infer that a matching commit proves the same repository.
- Before authorizing recovery, inspect and bind durable delivery intents/receipts
  as well as invocation results for every affected subject. Pending or uncertain effect
  fields must prevent recovery until reconciled, including cases where the worker
  journal never received the receipt. Treat not_started authority-pending delivery
  separately from a started but unconfirmed effect. Include sufficient durable delivery
  evidence in the quiescence contract for recovery to verify it.
- Define durable recovery phases and a coordinator/hook protocol that distinguishes
  safe preflight or proven rejected/rolled-back work from applying or genuinely uncertain
  effects. Permit a verified safe retry of the same recovery attempt without charging
  the plan budget again; never blindly replay uncertain provider/application effects.
  Give the quiescence generation an explicit verification contract, preferably capturing
  the post-blocking state passed to the hook, and keep receipts immutable.
- Bind the substantive Markdown body and relevant context content of every included
  plan/task/feature to approved decomposition and execution evidence, while excluding
  routine lifecycle metadata that the coordinator updates. Cover feature-only references
  and the standalone subject execution path where applicable. A material context change
  must invalidate the old approval and route to the defined revalidation/recovery
  path before dispatch, delivery, or completion.
validation:
- Use controlled adapters with real local Git remote configuration to interrupt a
  push/PR and then change origin URL, push URL, or gh repository context. Each changed
  destination must block without a new external write or false confirmation. Unchanged
  destinations must still reconcile without duplicate pushes or PRs.
- Interrupt after persisted push intent and after persisted PR-create intent, both
  before and after effects, while another feature requests structural recovery. Verify
  recovery is not called and no artifacts are superseded until the exact delivery
  is reconciled. Also cover an absent/stale journal.delivery and a harmless not_started
  receipt.
- Test a preflight failure followed by repaired configuration, a synchronously rejected
  proposal, proven application rollback, and a genuine interrupted mutation/invocation.
  Safe cases must resume automatically with bounded unchanged attempt accounting;
  uncertain cases must remain blocked. Assert the receipt generation relationship
  at hook entry rather than accepting an undocumented offset.
- Change only task prose, only feature prose, and only the contents of a feature-only
  referenced document after decomposition and after review. Verify the old binding/approval
  is rejected before further delivery or completion. Retain a regression proving that
  lifecycle folder moves and ordinary status/evidence updates do not spuriously invalidate
  unchanged requirements.
context_refs:
- .ai/reviews/FEATURE-005-critical-1.md
- .ai/plans/active/PLAN-002.md
- .ai/constraints.yaml
- .ai/models.yaml
- .ai/project/commands.yaml
allowed_scope:
- src/ai_engineering/delivery.py
- src/ai_engineering/orchestrator.py
- tests/test_orchestration.py
- src/ai_engineering/templates/handoffs/agent-decomposition.md
- src/ai_engineering/templates/project/constraints.yaml
- src/ai_engineering/constraints.py
session_id: native-execution-orchestration
constraints: .ai/constraints.yaml
coding_standards: .ai/constraints.yaml#coding
command_policy: .ai/constraints.yaml#commands
commands: .ai/project/commands.yaml
---
# Review To Implementation

## Subject

FEATURE-005

## Review

.ai/reviews/FEATURE-005-critical-1.md

## Iteration

1

## Issues

- id: REVIEW-001
  category: security
  files:
  - src/ai_engineering/delivery.py
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
  - src/ai_engineering/orchestrator.py
  - src/ai_engineering/delivery.py
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
  - src/ai_engineering/orchestrator.py
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
  - src/ai_engineering/orchestrator.py
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

## Required Changes

- Resolve and bind the selected push destination and explicit PR repository identity
  before external intent. Verify those identities on every resumed observation/write,
  refuse a destination change, and issue PR observations/creation against the bound
  repository. Keep credentials out of persisted identities and preserve pending-authority
  PR-body preparation. Document how intentional fork/base repository pairs are selected;
  do not infer that a matching commit proves the same repository.
- Before authorizing recovery, inspect and bind durable delivery intents/receipts
  as well as invocation results for every affected subject. Pending or uncertain effect
  fields must prevent recovery until reconciled, including cases where the worker
  journal never received the receipt. Treat not_started authority-pending delivery
  separately from a started but unconfirmed effect. Include sufficient durable delivery
  evidence in the quiescence contract for recovery to verify it.
- Define durable recovery phases and a coordinator/hook protocol that distinguishes
  safe preflight or proven rejected/rolled-back work from applying or genuinely uncertain
  effects. Permit a verified safe retry of the same recovery attempt without charging
  the plan budget again; never blindly replay uncertain provider/application effects.
  Give the quiescence generation an explicit verification contract, preferably capturing
  the post-blocking state passed to the hook, and keep receipts immutable.
- Bind the substantive Markdown body and relevant context content of every included
  plan/task/feature to approved decomposition and execution evidence, while excluding
  routine lifecycle metadata that the coordinator updates. Cover feature-only references
  and the standalone subject execution path where applicable. A material context change
  must invalidate the old approval and route to the defined revalidation/recovery
  path before dispatch, delivery, or completion.

## Validation

- Use controlled adapters with real local Git remote configuration to interrupt a
  push/PR and then change origin URL, push URL, or gh repository context. Each changed
  destination must block without a new external write or false confirmation. Unchanged
  destinations must still reconcile without duplicate pushes or PRs.
- Interrupt after persisted push intent and after persisted PR-create intent, both
  before and after effects, while another feature requests structural recovery. Verify
  recovery is not called and no artifacts are superseded until the exact delivery
  is reconciled. Also cover an absent/stale journal.delivery and a harmless not_started
  receipt.
- Test a preflight failure followed by repaired configuration, a synchronously rejected
  proposal, proven application rollback, and a genuine interrupted mutation/invocation.
  Safe cases must resume automatically with bounded unchanged attempt accounting;
  uncertain cases must remain blocked. Assert the receipt generation relationship
  at hook entry rather than accepting an undocumented offset.
- Change only task prose, only feature prose, and only the contents of a feature-only
  referenced document after decomposition and after review. Verify the old binding/approval
  is rejected before further delivery or completion. Retain a regression proving that
  lifecycle folder moves and ordinary status/evidence updates do not spuriously invalidate
  unchanged requirements.

## Context Refs

- .ai/reviews/FEATURE-005-critical-1.md
- .ai/plans/active/PLAN-002.md
- .ai/constraints.yaml
- .ai/models.yaml
- .ai/project/commands.yaml

## Constraints

.ai/constraints.yaml

