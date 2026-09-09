---
role: implementation
subject: FEATURE-005
review: .ai/reviews/FEATURE-005-critical-2.md
iteration: 2
issues:
- id: REVIEW-001
  category: security
  files:
  - src/ai_engineering/runner.py
  - src/ai_engineering/delivery.py
  - tests/test_orchestration.py
  explanation: The repaired destination binding remains lossy for SCP-style SSH paths.
    runner._remote_identity at lines 39-42 converts both git@example.invalid:owner/repo.git
    and git@example.invalid:/owner/repo.git into ssh://example.invalid/owner/repo.git.
    Git treats the first repository path as home-relative and the second as absolute.
    A real Git invocation routed exclusively through a local non-network SSH stub
    confirmed receive-pack arguments owner/repo.git and /owner/repo.git respectively.
    In a separate temporary-project controlled-delivery probe, an uncertain push using
    the first URL was followed by a real local origin URL change to the second; the
    same receipt then returned confirmed and accepted a PR at the newly selected target.
    Both stored identities and fingerprints were identical, so check_destination did
    not reject the change. This is a remaining case of iteration-1 REVIEW-001.
  required_change: Preserve destination-relevant path semantics when producing the
    safe identity used for binding and reconciliation. At minimum, distinguish SCP
    home-relative paths from absolute paths and from SSH URL paths; reject unsupported
    ambiguous representations instead of mapping them to an accepted identity. Keep
    raw authentication credentials out of durable logs and receipts. Ensure fetch/push
    compatibility checks compare the corrected identities and cannot reintroduce the
    collision.
  validation_required: Add controlled delivery-resume tests that change origin and
    pushurl between home-relative SCP, absolute SCP and SSH URL forms after uncertain
    push/PR effects. Changed effective repositories must block before any new write
    or false confirmation; an unchanged repository must still reconcile. Verify distinct
    receive-pack paths with a local SSH stub, without network access, and retain credential-redaction
    regressions.
required_changes:
- Preserve destination-relevant path semantics when producing the safe identity used
  for binding and reconciliation. At minimum, distinguish SCP home-relative paths
  from absolute paths and from SSH URL paths; reject unsupported ambiguous representations
  instead of mapping them to an accepted identity. Keep raw authentication credentials
  out of durable logs and receipts. Ensure fetch/push compatibility checks compare
  the corrected identities and cannot reintroduce the collision.
validation:
- Add controlled delivery-resume tests that change origin and pushurl between home-relative
  SCP, absolute SCP and SSH URL forms after uncertain push/PR effects. Changed effective
  repositories must block before any new write or false confirmation; an unchanged
  repository must still reconcile. Verify distinct receive-pack paths with a local
  SSH stub, without network access, and retain credential-redaction regressions.
context_refs:
- .ai/reviews/FEATURE-005-critical-2.md
- .ai/plans/active/PLAN-002.md
- .ai/handoffs/FEATURE-005-implementation-2.md
- .ai/constraints.yaml
- .ai/models.yaml
- .ai/project/commands.yaml
dispatch_status: Prepared only; further implementation held pending user direction
  between PLAN-002 continuation and newer PLAN-003 planning.
implementer_session: native-execution-orchestration
constraints: .ai/constraints.yaml
coding_standards: .ai/constraints.yaml#coding
command_policy: .ai/constraints.yaml#commands
commands: .ai/project/commands.yaml
---
# Review To Implementation

## Subject

FEATURE-005

## Review

.ai/reviews/FEATURE-005-critical-2.md

## Iteration

2

## Issues

- id: REVIEW-001
  category: security
  files:
  - src/ai_engineering/runner.py
  - src/ai_engineering/delivery.py
  - tests/test_orchestration.py
  explanation: The repaired destination binding remains lossy for SCP-style SSH paths.
    runner._remote_identity at lines 39-42 converts both git@example.invalid:owner/repo.git
    and git@example.invalid:/owner/repo.git into ssh://example.invalid/owner/repo.git.
    Git treats the first repository path as home-relative and the second as absolute.
    A real Git invocation routed exclusively through a local non-network SSH stub
    confirmed receive-pack arguments owner/repo.git and /owner/repo.git respectively.
    In a separate temporary-project controlled-delivery probe, an uncertain push using
    the first URL was followed by a real local origin URL change to the second; the
    same receipt then returned confirmed and accepted a PR at the newly selected target.
    Both stored identities and fingerprints were identical, so check_destination did
    not reject the change. This is a remaining case of iteration-1 REVIEW-001.
  required_change: Preserve destination-relevant path semantics when producing the
    safe identity used for binding and reconciliation. At minimum, distinguish SCP
    home-relative paths from absolute paths and from SSH URL paths; reject unsupported
    ambiguous representations instead of mapping them to an accepted identity. Keep
    raw authentication credentials out of durable logs and receipts. Ensure fetch/push
    compatibility checks compare the corrected identities and cannot reintroduce the
    collision.
  validation_required: Add controlled delivery-resume tests that change origin and
    pushurl between home-relative SCP, absolute SCP and SSH URL forms after uncertain
    push/PR effects. Changed effective repositories must block before any new write
    or false confirmation; an unchanged repository must still reconcile. Verify distinct
    receive-pack paths with a local SSH stub, without network access, and retain credential-redaction
    regressions.

## Required Changes

- Preserve destination-relevant path semantics when producing the safe identity used
  for binding and reconciliation. At minimum, distinguish SCP home-relative paths
  from absolute paths and from SSH URL paths; reject unsupported ambiguous representations
  instead of mapping them to an accepted identity. Keep raw authentication credentials
  out of durable logs and receipts. Ensure fetch/push compatibility checks compare
  the corrected identities and cannot reintroduce the collision.

## Validation

- Add controlled delivery-resume tests that change origin and pushurl between home-relative
  SCP, absolute SCP and SSH URL forms after uncertain push/PR effects. Changed effective
  repositories must block before any new write or false confirmation; an unchanged
  repository must still reconcile. Verify distinct receive-pack paths with a local
  SSH stub, without network access, and retain credential-redaction regressions.

## Context Refs

- .ai/reviews/FEATURE-005-critical-2.md
- .ai/plans/active/PLAN-002.md
- .ai/handoffs/FEATURE-005-implementation-2.md
- .ai/constraints.yaml
- .ai/models.yaml
- .ai/project/commands.yaml

## Constraints

.ai/constraints.yaml

