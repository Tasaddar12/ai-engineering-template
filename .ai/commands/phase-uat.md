# User acceptance

Read [RULES](../RULES.md), phase acceptance, summaries and VERIFICATION.
Use UAT when the user must establish behavior or the phase requires it.

Before presenting cases, the coordinator and verifier MUST classify every
deliverable using the [SUMMARY coverage contract](../templates/summary.md).
Record the deliverable ID, classification, inspected verification references and
reviewed revision in VERIFICATION. Auto-pass requires `human_judgment: false`,
nonempty verification and passing evidence for every entry. Present every other
deliverable to the human with its exact missing or failing condition. Required
human-only acceptance cases remain pending until the user reports their result;
automated classification cannot supply that report.

Create or inspect the persistent acceptance session:

```text
python .ai/runtime/phase.py uat 01-authentication
```

Present concrete observable cases with expected outcomes. Record what the user
actually reports; do not turn silence or an agent's guess into a pass. For example:

```text
python .ai/runtime/phase.py uat 01-authentication --case 1 --result pass --note "The user confirmed the expected outcome."
```

Set `--result fail` for an observed mismatch, `blocked` when a prerequisite prevents
execution, or `skipped` when the user explicitly declines the case. Record the
observation or reason in `--note`; do not treat missing feedback as a skipped case.
Only record that example statement when it is true. Resume the existing file
rather than replacing earlier results. Required cases must pass before final readiness and merge. Draft progress pushes
follow [phase-ship](phase-ship.md); the runtime publisher still requires UAT.

Diagnose failures using evidence and route bounded corrections through the phase.
Preserve the failure and retest the affected case after correction. UAT does not
replace automated checks or independent code/documentation verification.

## Preserve the full acceptance record

Read the complete [UAT template](../templates/UAT.md), including its update rules,
gap records and resume behavior. Follow the [runtime contract](../runtime/TEMPLATE-CONTRACT.md)
for the machine-checked fields. Keep expected behavior, observed results, gaps
and diagnosis visible. A failed observation remains a gap until a correction is
verified; only the user can supply a human acceptance observation.
