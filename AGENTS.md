# Agent entry point

This repository is being prepared as a reusable template. Do not create
repo-specific plans, specs, decisions, amendments or journal entries for
template cleanup unless the user explicitly requests them. The record workflows
describe how an adopting project uses the template.

**Commit standalone task work and each PLAN build/document step before your
final response, with a nonempty descriptive message.** This is standing
authorization for local commits. Runtime fix/docs-fix workers are the explicit
exception: they return scoped edits uncommitted for coordinator audit and
commit, as defined in [RULES](.ai/RULES.md#session-and-authorization). Honor
an explicit user instruction not to commit; read-only tasks need no empty
commit.

Read and follow [.ai/RULES.md](.ai/RULES.md), [PROJECT](.ai/state/PROJECT.md),
[STATE](.ai/state/STATE.md), the selected record and your
[role](.ai/agents/README.md) before acting.

**Report, then follow the user's decision.** An explicit instruction already
authorizes its exact scope. Do not turn a report into execution.

During approved work, resolve contradictions through the
[Rules](.ai/RULES.md). Establish whether the code or the
document is wrong. Correct the wrong side with evidence; never bend code to
satisfy a stale sentence or rewrite a valid requirement to excuse a bug.

Specs describe current behavior. Plans propose future changes and carry
their exact contract wording. ADRs explain decisions; amendments and the
journal retain history. Plan and FIX stages come from their directories.
Use [truth-map](.ai/truth-map.md) to find each fact's single owner.

Use the selected agent file for its specific rules, methods and positive
read/write scope; shared project/workflow rules live in RULES.md. Report unrelated findings
through [defer](.ai/commands/defer.md). Work only in the assigned checkout;
verify its absolute root and branch before writes. Roles are instructions,
not an installed dispatcher or permission system.

All tracked mutations use an assigned immediate-child worktree and the reviewed
delivery lifecycle in [.ai/commands/worktree.md](.ai/commands/worktree.md).
The primary checkout is read-only for tracked edits and commits; it is used for
inspection, fetch and verified fast-forward synchronization.

Start with [onboard](.ai/commands/onboard.md) for project context,
[plan-status](.ai/commands/plan-status.md) for a snapshot, and
[verifier](.ai/agents/verifier.md) for evidence before delivery.

Plans define desired future state and carry exact proposed contract wording.
For requested intent changes, fill the PLAN's Execution contract and record
each human resolution under
[Intent and PLAN approval](.ai/RULES.md#intent-and-plan-approval) before implementation.
Use [Review and documentation](.ai/RULES.md#review-and-documentation) for the
handoff from code agents to documentation agents.
Existing specs govern behavior left unchanged. Specs must be truthful on the
merged/deliverable revision, while intermediate implementation commits may
precede that batch. Amendments, specs and ADRs land together in the
documentation commit in the same PR as code; supersede ADRs with a new ADR and
links from the old record.
