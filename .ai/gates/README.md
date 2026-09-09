# Gates

A gate is a PASS/FAIL check before a named workflow transition. Policies own the
requirements; each gate names the criteria and evidence needed for that transition.

| Gate | Apply before |
| --- | --- |
| [Action approved](action-approved.md) | Starting the particular proposed action. |
| [Parallel ready](parallel-ready.md) | Starting a wave of concurrent assignments. |
| [Review ready](review-ready.md) | Handing a proposal, research record or implementation to review. |
| [Delivery ready](delivery-ready.md) | Each commit, push, PR creation or merge action. |
| [Retirement ready](retirement-ready.md) | Removing a merged worktree and local branch. |

PASS requires all applicable criteria to be met with current evidence. Missing,
unknown, stale or failed evidence produces FAIL. A criterion can be Not applicable
only when the definition permits it; record the reason. There is no implied pass.

Use [gate-result.md](../templates/gate-result.md). Record the subject, revision, each
criterion's evidence, overall result, evaluator and next action in the selected plan
or intake. A journal entry links to that evaluation. Re-evaluate after relevant
content, scope or approval changes. PASS never supplies new user authority.

These checks are manual. A FAIL stops the specified transition; it does not require
moving all work into blocked.
