# Plan verification

Plan and completion evidence: {{ plan_link_and_completion }}

Revision / baseline / pending diff: {{ exact_subject }}

Evaluator, time and environment: {{ evaluator_time_environment }}

Validation authority: {{ approved_scope_reference }}

## Acceptance, specs and observed behavior

| Feature / task / acceptance | Owning spec | Check / journey | Expected | Observed | PASS / FAIL / NOT_RUN / N/A | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| {{ acceptance }} | {{ spec }} | {{ check }} | {{ expected }} | {{ actual }} | {{ outcome }} | {{ reference }} |

Include every acceptance condition, affected spec and agreed regression check.
Each evidence reference identifies its revision/environment; explain each N/A.

## Review and findings

Link independent review when required. Separate confirmed defects (FIX links when
recorded) from suspected drift or unresolved questions (INTAKE links when recorded).

## Result and limits

Overall: {{ PASS_or_FAIL }}

Missing, failed, stale or unrun required checks prevent PASS. Record untested scope
and remaining defects. A completed checklist alone is not verification.

## Next action

{{ action_and_owner }}

Link the decision summary. Verification does not authorize repairs, record transitions
or merge. Keep historical done plans intact.
