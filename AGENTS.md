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
[STATE](.ai/state/STATE.md), the selected record, and the relevant
[command](.ai/commands/README.md) and [role](.ai/agents/README.md).

**Default: inspect and report. Do not implement until the user says yes or
explicitly instructs the action.** A request to review or report authorizes that
only. A direct instruction already authorizes
its exact scope; do not ask again for the same action.

Within approved work, resolve contradictions through the
[RULES amendment protocol](.ai/RULES.md#the-amendment-protocol). Establish which
side is wrong; do not change a valid requirement to excuse a bug. Use the
[truth map](.ai/truth-map.md) to locate each fact's owner.

Verify the assigned absolute worktree and branch before writes. Keep that
ownership fixed. The coordinator owns shared state, commits and delivery;
track roles have the narrower scopes in their role files. Capture unrelated
findings through [defer](.ai/commands/defer.md) when record writes are appropriate.

Use [verifier](.ai/agents/verifier.md) before delivery. Review the actual diff
and report validation results and review independence. Every commit has a
descriptive message. Keep affected current specs accurate in adopting projects.
Push, PR creation and merge must stay within the user's granted scope.
After an authorized merge, pull the target, confirm the merge and contents,
then remove only the clean, merged worktree and its branch. Use
[orchestrate-clean](.ai/commands/orchestrate-clean.md) for run cleanup.

These are instruction files, not an installed dispatcher or sandbox. Consult
[adoption](docs/ADOPTING.md) and [hooks](.ai/hooks/README.md) for integration limits.
