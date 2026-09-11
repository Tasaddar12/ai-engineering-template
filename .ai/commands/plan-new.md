---
description: Write a new plan into .ai/plans/backlog/
argument-hint: <what needs building>
---

Create a plan for: **$ARGUMENTS**

If the argument is an `INTAKE-{nnn}` id, this is a promotion: read that file in
`.ai/plans/intake/` and plan the problem it describes. The intake item is the
raw capture; the plan is the sized, spec'd version of it. Link the plan back to
the intake id, and `git mv` the intake file into `.ai/plans/abandoned/` only if
planning it reveals it is not worth doing — otherwise leave it where it is
until the plan closes.

**First, check this is a plan and not a fix.** If the specs already describe
the behavior being asked for and the code merely fails to deliver it, that is a
bug fix: say so and use `/fix`, which is the whole lifecycle in one command. A
fix restores conformance with the contract; a plan changes what conformance
means. See `.ai/RULES.md#bug-fixes`.

1. Read `.ai/config.yaml` for `mode`, and `.ai/state/PROJECT.md` for non-goals
   and hard constraints. If the request pursues a stated non-goal or violates a
   hard constraint, say so before writing anything and ask whether to proceed.
2. Check `.ai/plans/intake/` and `.ai/plans/backlog/` for the same problem
   already captured. Fold it in rather than opening a second thread on it.
3. Allocate the next id: the highest `PLAN-` number anywhere under `.ai/plans/`
   — including `done/` and `abandoned/` — plus one. Numbers are never reused.
4. Delegate to the **planner** agent to write
   `.ai/plans/backlog/PLAN-{nnn}-{slug}.md` from `.ai/templates/PLAN.md`.
   In `standard` and `full` mode the planner identifies the governing specs and
   fills in **Contract changes** — the specs this plan will create, amend or
   retire, with their wording drafted in present tense, plus any ADR it needs
   or supersedes. That section is the plan's contract with the future and the
   main thing the checker reviews. In `light` mode the acceptance criteria go in
   the plan instead.

   Nothing drafted there is written into `.ai/specs/` yet: a spec states what
   is true on the merged/deliverable revision, so the documentor lands the
   wording in the final documentation batch in the same PR as the working code.
5. On anything non-trivial, then run the **plan-checker** agent against the new
   plan and report its verdict. If it finds blocking conflicts, have the
   planner revise before you report back.
6. Append a line to today's journal at `.ai/state/journal/YYYY-MM-DD.md`.

Report the plan id and path, the specs it satisfies, what its **Contract
changes** section commits to, the checker's verdict, and anything you need from
the user before work can start. Do not start implementing — use `/plan-start`
for that.
