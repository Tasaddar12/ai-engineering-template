---
description: Verify a finished plan against specs and observed behavior
argument-hint: <plan-id>
---

Verify **$1**.

1. Locate the plan. If it is still in `.ai/plans/active/`, `git mv` it to
   `.ai/plans/review/`.
2. Delegate to the **verifier** agent. It grades against `.ai/specs/` and
   against observed behavior — **not** against the plan's checklist. Ticked
   boxes are not evidence.
3. If the project is in `mode: full`, also confirm the acceptance gate named by
   the plan or the phase.
4. Append a journal entry with the verdict.

Report the verifier's verdict verbatim, including any failing command output.
Do not soften a failure and do not round a partial result up to a pass.

Then, by verdict:

- **verified** — tell the user to run `/plan-done $1`.
- **defects found** — leave the plan in `review/`, list the defects, and
  recommend either resuming with `/plan-start $1` or a follow-up plan.
- **cannot verify** — say exactly which criteria could not be checked and what
  would be needed. Never present an unverified criterion as satisfied.

If the verifier reports **record drift** — a spec that no longer matches the
code, a contract change with no amendment record, something the plan's
**Contract changes** section promised and never landed, or a spec carrying
history ("deprecated", "was previously") or unbuilt behavior — that is a
defect, not a footnote. It is what makes the next task go wrong. Have the
executor land it before closing the plan.
