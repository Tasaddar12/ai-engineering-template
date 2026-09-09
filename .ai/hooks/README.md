# Manual checkpoints

Hooks identify when to evaluate a gate. The linked gate owns its PASS/FAIL criteria;
the policy it cites owns the requirement.

| Event | Gate |
| --- | --- |
| Before a proposed action begins | [Action approved](../gates/action-approved.md) |
| Before starting a concurrent wave | [Parallel ready](../gates/parallel-ready.md) |
| Before handing a subject to review | [Review ready](../gates/review-ready.md) |
| Before each commit, push, PR creation or merge | [Delivery ready](../gates/delivery-ready.md) |
| Before removing a merged worktree/local branch | [Retirement ready](../gates/retirement-ready.md) |

Record the result with [gate-result.md](../templates/gate-result.md). Follow the gate's
failure handoff when it returns FAIL.

No executable hooks are installed. Automating a checkpoint requires a separately
approved change; these definitions alone do not enforce the requirements.
