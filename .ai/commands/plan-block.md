---
tier: contract
authority: agent
links: [AMD-002]
description: Park a plan on a decision only a human can make
argument-hint: <plan-id> <the question>
---

Arguments: **$ARGUMENTS** — the first token is the plan id; everything after it
is the blocking question. If no id was given, infer it from the plan currently
in `.ai/plans/active/` and say which one you picked.

First, check that this is genuinely a blocker. Per `.ai/RULES.md`, blocked
means you cannot proceed without a decision that is not yours to make —
`intent`-tier questions, and irreversible or outward-facing actions. These are
**not** blockers:

- a spec is wrong → amend it with a record, and continue
- a plan is wrong → rewrite it, and continue
- a document contradicts the code → resolve it, and continue
- a doc is missing → write it, and continue
- the blocker is a defect the specs already condemn → `/fix` it, and continue

If it is one of those, say so and do that instead of blocking.

If it is a real blocker:

1. `git mv` the plan into `.ai/plans/blocked/`.
2. Add a `## Blocked` section to the plan with the question, the options you
   see, your recommendation, and what you already finished.
3. Add a row to the **Blockers** table in `.ai/state/STATE.md`, and move
   **Now** on to something else if there is other work.
4. Append a journal entry.
5. **Do every part of the task that does not depend on the answer**, then
   report what landed and what is waiting.

Report the question in one sentence, the options, and your recommendation — the
user should be able to unblock this in a single reply. Then `/plan-start $1`
resumes it.
