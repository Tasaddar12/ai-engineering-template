---
subject: FEATURE-005
iteration: 2
status: CHANGES_REQUIRED
base: 90ab58b39f1a84ab1827ef0b72a25c72159447eb
head: 29303075b01d33328d1830307404689080428eef
reviewer_session: critical-review-feature005-20260909-2
implementer_session: native-execution-orchestration
summary: One blocking destination-identity collision remains for relative versus absolute
  SCP repository paths. The other three iteration-1 findings are repaired in the reviewed
  implementation.
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
security_findings:
- 'REVIEW-001: distinct effective SSH repository paths still share a delivery identity
  and can reuse uncertain-write evidence.'
- Durable delivery inventory, explicit PR repository/head selection, exact remote-query
  guards, control-directory scope protections and credential-safe query output were
  inspected. The reproduced blocker is limited to destination normalization.
documentation_findings:
- The new public decomposition-only API and explicit recovery protocol/generation
  contract match the reviewed implementation. Update destination-normalization semantics
  alongside the remaining repair.
- No plan-specific artifacts were added outside .ai by this diff. Generic end-user
  CLI/provider documentation remains the approved later feature scope.
validation:
- 'Independent complete-diff review: all seven changed paths at base 90ab58b39f1a84ab1827ef0b72a25c72159447eb
  through head 29303075b01d33328d1830307404689080428eef, with current FEATURE-005,
  TASK-052..055, PLAN-002 and durable assignment/completion evidence.'
- 'Independent focused pytest run: 11 passed, 21 deselected in 109.19 seconds. Cases
  cover safe/uncertain recovery phases, durable delivery receipts absent from journal
  copies, decomposition before Git, remote command policy and credential-safe diagnostics.'
- 'Independent controlled-delivery probe: uncertain push to home-relative SCP URL,
  followed by real local origin change to absolute SCP URL, returned confirmed using
  the same destination identity and fingerprint.'
- 'Independent real-Git/local-SSH-stub probe: receive-pack received owner/repo.git
  versus /owner/repo.git. Stub exited locally; no network, hosting-service, credential,
  paid-service or live AI-provider call occurred.'
- Independent git diff --check passed; assigned worktree remains clean at the exact
  reviewed head.
- 'Supplied implementer/coordinator evidence: Windows and Linux each passed 29 unchanged
  orchestration cases, plus all 3 isolated replacement cases after correcting the
  stale-path fixture, covering the final 32 cases; this was not presented as a fresh
  single 32-case run.'
- 'Supplied Windows baseline: 129 passed and 2 symlink-privilege skips. Supplied lint/format,
  native 15-module type checks and affected Linux-target type checks passed.'
- All automated and custom tests above are Python runtime and controlled-provider
  validation. They do not establish actual AI instruction-following or live provider/hosting-service
  reliability.
---
# Critical Change Review

## Summary

CHANGES_REQUIRED. The complete updated feature diff was reviewed in the same single independent critical stage. One reproduced destination-binding case remains.

Iteration-1 REVIEW-002 is repaired by authoritative durable delivery inventories; REVIEW-003 is repaired by explicit recovery checkpoints, immutable entry receipts and safe attempt resumption; REVIEW-004 is repaired by substantive Markdown/context bindings and recovery routing. The public semantic decomposition-only boundary is present. The original destination finding is substantially repaired for changed HTTPS repositories and explicit PR ownership, but the SCP normalization collision below still permits false reconciliation.

## Blocking issues

| Category | Location | Exact issue | Required fix |
| --- | --- | --- | --- |
| Security | runner.py:39-42; delivery.py destination/check_destination | Home-relative and absolute SCP paths collapse to one binding, allowing an old uncertain delivery receipt to confirm against a different repository. | Preserve effective path semantics or reject ambiguous representations; test resume against each form. |

### REVIEW-001 - SCP path semantics are lost from delivery identity

Category: security

Files:
- src/ai_engineering/runner.py
- src/ai_engineering/delivery.py
- tests/test_orchestration.py

Issue:
The repaired destination binding remains lossy for SCP-style SSH paths. runner._remote_identity at lines 39-42 converts both git@example.invalid:owner/repo.git and git@example.invalid:/owner/repo.git into ssh://example.invalid/owner/repo.git. Git treats the first repository path as home-relative and the second as absolute. A real Git invocation routed exclusively through a local non-network SSH stub confirmed receive-pack arguments owner/repo.git and /owner/repo.git respectively. In a separate temporary-project controlled-delivery probe, an uncertain push using the first URL was followed by a real local origin URL change to the second; the same receipt then returned confirmed and accepted a PR at the newly selected target. Both stored identities and fingerprints were identical, so check_destination did not reject the change. This is a remaining case of iteration-1 REVIEW-001.

Required change:
Preserve destination-relevant path semantics when producing the safe identity used for binding and reconciliation. At minimum, distinguish SCP home-relative paths from absolute paths and from SSH URL paths; reject unsupported ambiguous representations instead of mapping them to an accepted identity. Keep raw authentication credentials out of durable logs and receipts. Ensure fetch/push compatibility checks compare the corrected identities and cannot reintroduce the collision.

Validation required:
Add controlled delivery-resume tests that change origin and pushurl between home-relative SCP, absolute SCP and SSH URL forms after uncertain push/PR effects. Changed effective repositories must block before any new write or false confirmation; an unchanged repository must still reconcile. Verify distinct receive-pack paths with a local SSH stub, without network access, and retain credential-redaction regressions.

Each issue must specify ID, category (correctness/security/documentation), affected files,
exact explanation, required change, and validation required. Include a concise table:
Category | Location | Exact issue | Required fix. PASS requires no blocking issues.
CHANGES_REQUIRED requires at least one actionable issue. Review the complete updated diff.

## Security findings

- REVIEW-001: distinct effective SSH repository paths still share a delivery identity and can reuse uncertain-write evidence.
- Durable delivery inventory, explicit PR repository/head selection, exact remote-query guards, control-directory scope protections and credential-safe query output were inspected. The reproduced blocker is limited to destination normalization.

## Documentation findings

- The new public decomposition-only API and explicit recovery protocol/generation contract match the reviewed implementation. Update destination-normalization semantics alongside the remaining repair.
- No plan-specific artifacts were added outside .ai by this diff. Generic end-user CLI/provider documentation remains the approved later feature scope.

## Validation inspected and limits

- Independent complete-diff review: all seven changed paths at base 90ab58b39f1a84ab1827ef0b72a25c72159447eb through head 29303075b01d33328d1830307404689080428eef, with current FEATURE-005, TASK-052..055, PLAN-002 and durable assignment/completion evidence.
- Independent focused pytest run: 11 passed, 21 deselected in 109.19 seconds. Cases cover safe/uncertain recovery phases, durable delivery receipts absent from journal copies, decomposition before Git, remote command policy and credential-safe diagnostics.
- Independent controlled-delivery probe: uncertain push to home-relative SCP URL, followed by real local origin change to absolute SCP URL, returned confirmed using the same destination identity and fingerprint.
- Independent real-Git/local-SSH-stub probe: receive-pack received owner/repo.git versus /owner/repo.git. Stub exited locally; no network, hosting-service, credential, paid-service or live AI-provider call occurred.
- Independent git diff --check passed; assigned worktree remains clean at the exact reviewed head.
- Supplied implementer/coordinator evidence: Windows and Linux each passed 29 unchanged orchestration cases, plus all 3 isolated replacement cases after correcting the stale-path fixture, covering the final 32 cases; this was not presented as a fresh single 32-case run.
- Supplied Windows baseline: 129 passed and 2 symlink-privilege skips. Supplied lint/format, native 15-module type checks and affected Linux-target type checks passed.
- All automated and custom tests above are Python runtime and controlled-provider validation. They do not establish actual AI instruction-following or live provider/hosting-service reliability.
