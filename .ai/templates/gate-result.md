---
tier: log
authority: agent
title: Gate result
---
> Log: preserve evidence; append corrections.

# Gate result

Gate: {{ definition_link }}

Subject / revision / evaluator / time: {{ evaluation_context }}

| Criterion | Met / unmet / N/A | Evidence or permitted exception |
| --- | --- | --- |
| {{ criterion }} | {{ result }} | {{ reference }} |

Result: {{ PASS_or_FAIL }}

Next action and owner: {{ bounded_handoff }}

Record in the selected PLAN/FIX evidence section. Append new evidence for a
historical record to the journal. Missing evidence cannot produce PASS.

<!-- Evidence report. A changed relevant subject or authority needs a fresh
evaluation. A passing gate grants no additional action authority. -->
