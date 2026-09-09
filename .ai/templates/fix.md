---
tier: plan
authority: agent
id: FIX-{{ nnn }}
found: {{ date }}
found_by: {{ role }}
severity: {{ critical_major_or_minor }}
violates: []
links: []
title: {{ title }}
---
> Plan: revise the proposed route as evidence changes; preserve accepted
> results.

# {{ title }}

## Symptom

Describe the failure from outside in: expected/observed behavior, affected
revision/environment and confirming evidence. Do not diagnose in this section.

## Root cause

Name the mechanism and location. State Unknown until established; never
confuse the location of a symptom with its cause.

## Change and scope

The smallest conformance repair, affected files and exclusions. State exact
execution/delivery authority. Behavior or intent changes escalate to a PLAN.

## Proof

Name the repeatable regression guard and record the actual command/output
against unfixed behavior, then fixed behavior. Include revision/environment
and relevant regression results. A check that never failed proves less than
a check that demonstrates the defect. Missing proof keeps this record open.

## Contract

Name the existing requirement violated. Distinguish restoring it from
clarifying an already agreed but undocumented behavior or changing behavior.
A clarification needs evidence and an AMD; a new behavior needs a PLAN.
Update current SPEC verification_refs without altering valid criteria.

## Related and closure

Link originating INTAKE, PLAN if escalated, review, user acceptance and
authorized delivery. Name remaining blockers or a linked recurrence.

<!-- FIX-{nnn}-{slug}.md. Directory owns stage. Write the symptom first;
unknown cause stays unknown; no before/after proof means no closure. -->
