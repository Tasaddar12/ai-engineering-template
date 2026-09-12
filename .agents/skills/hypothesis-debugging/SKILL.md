---
name: hypothesis-debugging
description: Diagnose a failure with an uncertain cause or a repair that did not work. Use falsifiable hypotheses and controlled experiments to produce a bounded diagnosis or regression-backed correction.
---

# Debug with discriminating evidence

Use the assigned role and [shared rules](../../../.ai/RULES.md).
A diagnosis-only request ends with findings; implementation follows its actual
authorization.

## Establish the failure

Capture expected behavior and its authority, the observed behavior, minimal
input, environment/revision and repeatability. Reproduce through the relevant
entry point where practical. A test failing to import or set up does not
establish the product defect.

For intermittent failures, record timing, ordering and frequency under controlled
conditions. For concurrency failures, trace state ownership, transaction
boundaries, ordering and waits. Keep useful evidence in the assigned RESEARCH or
SUMMARY instead of creating a separate debug lifecycle.

## Test explanations before patching

Keep the working hypothesis explicit:

| Explanation | Predicted observation | Experiment that distinguishes it | Actual result |
|---|---|---|---|

Choose the cheapest experiment that could disprove the leading explanation.
Change one relevant factor at a time, inspect both callers and the failing
boundary, and keep eliminated explanations so another worker does not repeat
them. Do not force a fixed hypothesis count when evidence already isolates the
cause.

A successful patch attempt is weaker evidence than an explained cause with a
regression. If an experiment disproves the explanation, revise it before making
another speculative patch. When investigation is blocked by missing access,
unavailable evidence or a consequential decision, return that exact limit and
the useful findings rather than retrying the same action indefinitely.

## Verify the correction

Minimize the reproduction without losing the triggering condition, and retain
the original example. Check neighboring inputs that might share the cause.
For a filename defect, case differences and leading whitespace are different
conditions; one passing example does not establish the other.

Keep expected behavior intact. Removing a guard, swallowing an error or weakening
an assertion may hide the failure instead of fixing it. If source and guidance
disagree, use the [conflict rules](../../../.ai/RULES.md#documents-and-conflicts)
to establish which side needs correction.

Return the causal explanation, changed boundary, before/after evidence, tested
revision and remaining limits. Apply [regression design](../regression-design/SKILL.md)
when choosing tests needs more detail; do not load it merely to repeat these
instructions. Preserve required phase acceptance and documentation coverage.
