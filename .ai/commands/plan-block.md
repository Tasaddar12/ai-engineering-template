---
description: Park a plan on a decision only a human can make
argument-hint: <plan-id> <the question>
---

Arguments: **$ARGUMENTS** — the first token is the plan id; everything after it
is the blocking question. If no id was given, infer it from the plan currently
in `.ai/plans/active/` and say which one you picked.

Read and follow [RULES](../RULES.md#when-you-are-genuinely-blocked).
Check whether there is an unresolved human decision, including any requested
intent change inside the PLAN's target. Record that request and its resolution
in the PLAN's Execution contract. Use this diagnostic map:

- A SPEC appears wrong → investigate the code and pass evidence to the documentor.
- A PLAN's route appears wrong → report evidence for the planner; preserve its
  approved outcome.
- A document contradicts code → establish which side is wrong before routing
  the correction.
- A PLAN requests an intent change → resolve it with a human before implementing.
- Documentation is missing → pass the gap to the documentation agent after
  code review.
- Code violates established requirements/invariants → capture a FIX and identify
  the needed correction or supporting PLAN.

If it is a real blocker:

1. `git mv` the plan into `.ai/plans/blocked/`.
2. Have the planning/documentation agent add a `## Blocked` section to the plan with the question, the options you
   see, your recommendation, and what you already finished.
3. Add a row to the **Blockers** table in `.ai/state/STATE.md`, and move
   **Now** on to something else if there is other work.
4. Append a journal entry.
5. **Do every part of the task that does not depend on the answer**, then
   report what landed and what is waiting.

Report the question in one sentence, the options, and your recommendation — the
user should be able to unblock this in a single reply. Then `/plan-start $1`
resumes it.
