# Agent entry point

This repository is being prepared as a reusable template. Do not create
repo-specific plans, specs, decisions, amendments or journal entries for
template cleanup unless the user explicitly requests them. The record workflows
describe how an adopting project uses the template.

**Always commit the changes made for a task before your final response, with a
nonempty, descriptive commit message.** This is standing authorization for
local commits: do not leave completed work uncommitted or ask for commit
permission again. This requirement overrides role or command instructions
that say to commit only when separately asked. Honor an explicit user
instruction not to commit; read-only tasks need no empty commit.

Read [.ai/RULES.md](.ai/RULES.md), [PROJECT](.ai/state/PROJECT.md),
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

Use the selected role's positive read/write scope. Report unrelated findings
through [defer](.ai/commands/defer.md). Work only in the assigned checkout;
verify its absolute root and branch before writes. Roles are instructions,
not an installed dispatcher or permission system.

Start with [onboard](.ai/commands/onboard.md) for project context,
[plan-status](.ai/commands/plan-status.md) for a snapshot, and
[verifier](.ai/agents/verifier.md) for evidence before delivery.

Plans define desired future state. Every PLAN, including a draft or unapproved
PLAN, always has authority to require changes to any contract in its declared
target and carries exact target wording until the final documentation batch.
Document conflicts never block PLAN creation, review, approval or implementation
on that ground; lifecycle permission to start work remains separate.
Existing specs govern behavior left unchanged. Specs must be truthful on the
merged/deliverable revision, while intermediate implementation commits may
precede that batch. Amendments, specs and ADRs land together in the
documentation commit in the same PR as code; supersede ADRs with a new ADR and
links from the old record.
