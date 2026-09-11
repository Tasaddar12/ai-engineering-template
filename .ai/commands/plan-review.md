---
description: Verify a finished plan against specs and observed behavior
argument-hint: <plan-id>
---

Read and follow [RULES](../RULES.md).

Verify **$1**.

1. Locate the plan. If it is still in `.ai/plans/active/`, `git mv` it to
   `.ai/plans/review/`.
2. Delegate to the **verifier** agent. It grades against current contracts,
   the preserved PLAN target, observed behavior and coordinator receipts under
   [Definition of done](../RULES.md#definition-of-done).
3. If the project is in `mode: full`, also confirm the acceptance gate named by
   the plan or the phase.
4. Append a journal entry with the verdict.

Report the verifier's verdict verbatim, including any failing command output.
Do not soften a failure and do not round a partial result up to a pass.

Then, by verdict:

- **verified** — tell the user to run `/plan-done $1`.
- **defects found** — leave the plan in `review/`, list the defects, and
  list missing implementation or overall SPEC coverage and concrete actions.
  Route confirmed bugs to FIX and substantial missing work to a supporting PLAN.
- **cannot verify** — say exactly which criteria could not be checked and what
  would be needed. Never present an unverified criterion as satisfied.

Classify documentation findings using
[Definition of done](../RULES.md#definition-of-done). Return missing overall
SPEC coverage to the documentation agent with code evidence. Include editorial
findings in the report without treating them as incomplete implementation.
