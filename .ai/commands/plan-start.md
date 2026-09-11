---
description: Move a plan to active and implement it
argument-hint: <plan-id>
---

Read and follow [RULES](../RULES.md).

Start work on: **$1**

1. Locate the plan under `.ai/plans/`. If it is in `blocked/`, confirm the
   blocking question has been answered. Have the planner record the human
   resolution, then check the entire Execution contract under
   [Intent and PLAN approval](../RULES.md#intent-and-plan-approval).
2. Check `lifecycle.max_active` in `.ai/config.yaml`. If `active/` is already
   above the suggested count, report which plans are active and continue under
   [Scheduling and IDs](../RULES.md#scheduling-and-ids).
3. `git mv` the file into `.ai/plans/active/`. Do not add a status field —
   the directory is the stage.
4. Update **Now** and **Next** in `.ai/state/STATE.md`.
5. Delegate to the **implementor** agent to implement it.
6. Append a journal entry: what was started, and what the implementor reported.

Use [Review and documentation](../RULES.md#review-and-documentation) for the
code-to-documentation handoff. The coordinator moves the completed implementation
to `.ai/plans/review/` and gathers the required review/documentation evidence
before `/plan-review $1` validates closeout.

If the implementor hits a question only a human can answer, run `/plan-block $1`
with the question rather than guessing — but finish everything the answer does
not block first.
