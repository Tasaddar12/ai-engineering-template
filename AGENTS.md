# Agent entry point

Read [.ai/RULES.md](.ai/RULES.md), [PROJECT](.ai/state/PROJECT.md),
[STATE](.ai/state/STATE.md), the selected record and your
[role](.ai/agents/README.md) before acting.

**Report, return the decision-summary template, then follow the user's
decision.** An explicit instruction already authorizes its exact scope;
see [approval](.ai/policies/approval.md). Do not turn a report into execution.

During approved work, resolve contradictions through the
[record policy](.ai/policies/records.md). Establish whether the code or the
document is wrong. Correct the wrong side with evidence; never bend code to
satisfy a stale sentence or rewrite a valid requirement to excuse a bug.

Specs describe current behavior. Plans propose future changes and carry
their exact contract wording. ADRs explain decisions; amendments and the
journal retain history. Plan and FIX stages come from their directories.
Use [truth-map](.ai/truth-map.md) to find each fact's single owner.

Use the selected role's positive read/write scope. Report unrelated findings
through [report](.ai/workflows/report.md). Work only in the assigned checkout;
verify its absolute root and branch before writes. Roles are instructions,
not an installed dispatcher or permission system.

Start with [initialize](.ai/commands/initialize.md) for project context,
[plan-status](.ai/commands/plan-status.md) for a snapshot, and
[plan-verify](.ai/commands/plan-verify.md) for evidence before delivery.
