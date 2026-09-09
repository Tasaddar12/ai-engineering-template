---
name: critical-review
trigger: Complete exact-head diff with required validation evidence
responsible_role: critical_review
required_inputs:
- subject
- exact_head
- complete_diff
- implementer_session
permitted_effects:
- inspect_declared_context
- run_read_only_inspections
- write_assigned_review
outputs:
- exact_head_verdict
stop_conditions:
- incomplete_or_changed_diff
- missing_required_evidence
resume: Create a fresh independent review after repair and revalidation.
---
# Critical review

One independent GPT-6 Astra/xhigh reviewer examines the complete current diff and
acceptance contract. Reviewer identity is distinct from the implementer and read-only.

1. Bind the reviewer session, subject, implementer session and exact head.
2. Inspect correctness, edge cases, failure behavior, relevant security surfaces,
   documentation and actual validation evidence.
3. Return one report containing either PASS or all actionable CHANGES_REQUIRED findings.
4. Reject the report if identity, head, subject, schema or immutable assignment differs.

Any implementation, validation-affecting repair or conflict resolution makes the old
review stale. A review iteration limit routes diagnosis/recovery; it does not convert
unreviewed work into PASS or create a hard block by itself.
