---
description: Move a plan to active and implement it
argument-hint: <plan-id>
---

Start work on: **$1**

1. Locate the plan under `.ai/plans/`. If it is in `blocked/`, confirm the
   blocking question has actually been answered before proceeding — and record
   the answer in the plan.
2. Check `lifecycle.max_active` in `.ai/config.yaml`. If `active/` is already
   at the limit, say which plans are there and ask before adding another.
3. `git mv` the file into `.ai/plans/active/`. Do not add a status field —
   the directory is the stage.
4. Update **Now** and **Next** in `.ai/state/STATE.md`.
5. Delegate to the **implementor** agent to implement it.
6. Append a journal entry: what was started, and what the implementor reported.

The implementor has authority to amend specs it finds to be wrong, and is required
to do so rather than working around them — see `.ai/RULES.md`. If it reports an
amendment, surface that in your summary: which spec, and why it moved.

When the implementor believes the work is complete it moves the plan to
`.ai/plans/review/`. Then run `/plan-review $1`.

If the implementor hits a question only a human can answer, run `/plan-block $1`
with the question rather than guessing — but finish everything the answer does
not block first.
