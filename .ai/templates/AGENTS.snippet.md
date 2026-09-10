<!-- Merge this into root AGENTS.md; preserve useful existing instructions.
Links below resolve from the destination repository root. -->

## Engineering work

Read [.ai/RULES.md](.ai/RULES.md), [.ai/state/PROJECT.md](.ai/state/PROJECT.md),
[STATE](.ai/state/STATE.md), the selected record and the relevant
[role](.ai/agents/README.md) and [command](.ai/commands/README.md).

**Inspect, report and return the [decision summary](.ai/templates/decision-summary.md)
before implementing.** Wait for the user's decision unless their existing
instruction already authorizes that exact action. The
[approval policy](.ai/policies/approval.md) owns this boundary.

Within approved work, resolve document/code contradictions through RULES and
use [truth-map](.ai/truth-map.md) to find each fact's owner. Verify the fixed
absolute worktree and branch before writes. Commands and roles are instructions,
not installed tools or a sandbox.

Use [plan-verify](.ai/commands/plan-verify.md) and
[deliver](.ai/commands/deliver.md) for verification, descriptive commits,
current specs, authorized publication, merge confirmation and exact cleanup.
