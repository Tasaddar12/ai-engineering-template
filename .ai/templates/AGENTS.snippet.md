<!-- Merge this into root AGENTS.md; preserve useful existing instructions.
Links below resolve from the destination repository root. -->

## Engineering work

Read [.ai/RULES.md](.ai/RULES.md), [.ai/state/PROJECT.md](.ai/state/PROJECT.md),
[STATE](.ai/state/STATE.md), the selected record and the relevant
[role](.ai/agents/README.md) and [command](.ai/commands/README.md).

**Inspect and report before implementing.** Wait for the user's decision unless
their existing instruction already authorizes that exact action. Do not ask
again for actions already authorized.

Within approved work, resolve document/code contradictions through RULES and
use [truth-map](.ai/truth-map.md) to find each fact's owner. Verify the fixed
absolute worktree and branch before writes. Commands and roles are instructions,
not installed tools or a sandbox.

Use [verifier](.ai/agents/verifier.md) to check current specs and observed
behavior. Review the actual diff and disclose review independence. Commit with
descriptive messages and publish only within the granted scope. After an
authorized merge, confirm the result and pull the target before removing the
exact clean, merged worktree and branch.
