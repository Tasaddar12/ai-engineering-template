# Invocation effort evidence within frozen v1 contracts

An independent Astra/xhigh advisory review checked the current model-default
requirement against the frozen agent/run/review schemas during implementation.
No schema or task-graph change is needed for the documented requirement to
record actual model and effort in handoff/review evidence.

Use an immutable invocation-evidence document and existing references:

- `agent-output.artifact_refs`;
- applicable `review-result.checks[].evidence`;
- `handoff.reviewer_notes` referring to that same evidence;
- `workflow-run.pending_operations[].evidence_refs` for dispatch observations;
- checkpoint and archive content-hash references for retention.

The document identifies request, attempt, invocation, provider and model. It
distinguishes configured expectations, submitted settings, and observed effort
with its observation source. Omitted or unknown effort is explicit. A configured
profile alone is not proof of provider-confirmed effort, and effort never raises
a model's capability rank. Fake-adapter observations identify themselves as
deterministic simulation evidence.

Do not add undeclared effort fields to existing `actual_model` or `reviewer`
objects. The reviewer confirmed that existing evidence-reference routes validate
against v1 and that undeclared reasoning-effort keys are rejected. Those schema
checks validate the references, not the prose inside a referenced document.
Structured automatic comparison of provider-confirmed effort after resume would
need a separately owned provenance schema; it is not implied by the current
evidence-recording requirement.

Review invocation: `/root/isolation_review`, advisory follow-up configured by
the coordinator with `gpt-6-astra`, `xhigh`. This describes observed tool
configuration and does not claim an additional provider-returned model identity.
