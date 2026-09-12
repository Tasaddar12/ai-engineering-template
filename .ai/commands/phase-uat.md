# User acceptance

Read [RULES](../RULES.md), phase acceptance, summaries and VERIFICATION.
Use UAT when the user must establish behavior or the phase requires it.

Create or inspect the persistent acceptance session:

```text
python .ai/runtime/phase.py uat 01-authentication
```

Present concrete observable cases with expected outcomes. Record what the user
actually reports; do not turn silence or an agent's guess into a pass. For example:

```text
python .ai/runtime/phase.py uat 01-authentication --case 1 --result pass --note "The user confirmed the expected outcome."
```

Use `fail`, `blocked` or `skipped` as appropriate, with the observed detail.
Only record that example statement when it is true. Resume the existing file
rather than replacing earlier results. Required cases must pass before publication.

Diagnose failures using evidence and route bounded corrections through the phase.
Preserve the failure and retest the affected case after correction. UAT does not
replace automated checks or independent code/documentation verification.
