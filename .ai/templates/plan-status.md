---
tier: status
authority: agent
title: Plan status
---
> Status: replace stale coordination with current observations.

# Plan status

Observed at / revision / scope: {{ snapshot_context }}

## Plans by directory

| Stage | Plan ID / title / link, or None | Progress / blocker |
| --- | --- | --- |
| {{ configured_stage }} | {{ record_or_none }} | {{ evidence }} |

Include every configured stage and every PLAN. Intake is not a plan stage.

## Now and next

Link STATE's current focus and next action.

## Blockers and drift

Link owners, questions and resume conditions. Separate suspected drift and
waiting intake from confirmed open FIX records.

## Things worth attention

Supported signs of stale activity, aging review, capacity pressure, repeated
defect causes, missing FIX proof or untriaged intake. State what was not read.

## Recommendation

One bounded next action. This snapshot changes no records.

<!-- Returned snapshot. Directory owns stage; do not trust duplicated
status/stage metadata or infer absence of drift from missing evidence. -->
