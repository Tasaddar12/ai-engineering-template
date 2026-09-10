---
tier: contract
authority: agent
description: Close out a verified plan
argument-hint: <plan-id>
---

Close **$1**.

Do not run this on a plan the verifier has not passed. If `/plan-review` has
not been run, run it first — "the steps are all checked off" is not a
definition of done.

1. Confirm the closing conditions from `.ai/RULES.md#definition-of-done`:
   - the specs it touched describe what the code now actually does, in present
     tense, with no annotation about what they used to say and no criteria for
     behavior that does not exist
   - **everything the plan's Contract changes section promised has landed** —
     specs created, amended or deleted; ADRs written; any superseded ADR marked
     `status: superseded` with `superseded_by:`. Walk that section line by line
     against the repository; this is the check most worth doing, because
     nothing else will catch a promised amendment that never happened.
   - every contract change has an amendment record in
     `.ai/decisions/amendments/`
   - `.ai/state/STATE.md` reflects the new present
   - a journal entry exists

   If any fail, fix them now — that is part of closing, not a nice-to-have. If
   the plan's drafted wording turned out not to describe what was built, land
   what is actually true and say the draft was wrong; do not land a spec you
   know is inaccurate because the plan said so.
2. `git mv` the plan into `.ai/plans/done/<period>/`, where `<period>` follows
   `lifecycle.done_partition` in `.ai/config.yaml` (e.g. `2026-Q3`). Create the
   directory if needed.
3. Move the item from **Now** to **Recently verified** in `.ai/state/STATE.md`,
   and set the new **Next**.
4. Record pending Git delivery separately. A plan in done is verified work;
   it does not assert that its PR merged. Confirm delivery from Git and the forge.
5. Consider whether `docs/` is now stale. If so, run the **scribe** agent.
6. Append the closing journal entry: what shipped, what was learned, what
   specs moved.

Report what shipped, which specs were created, amended or retired, which ADRs
were written or superseded, and what is next. Do not commit or push unless the
user asked.
