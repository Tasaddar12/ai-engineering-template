# Plan status

Observed at: {{ timestamp }}

Revision and inspection scope: {{ revision_and_limits }}

## Plans by stage

Show every configured stage, including empty stages, and every plan within it.
Intake is reported separately from plan stages.

| Stage | Plan / title / link, or None | Recorded status / review type | Recorded progress |
| --- | --- | --- | --- |
| {{ stage }} | {{ plan_or_none }} | {{ status }} | {{ progress_or_unknown }} |

## Current state and blockers

Now: {{ state_reference_and_now }}

Next: {{ state_reference_and_next }}

| Scope / plan | Blocker | Owner | Resume condition | Evidence |
| --- | --- | --- | --- | --- |
| {{ scope }} | {{ blocker_or_none }} | {{ owner }} | {{ condition }} | {{ reference }} |

## Intake and suspected drift

Waiting/unconfirmed intake, suspected discrepancy, supporting observation, uncertainty
and proposed next action. State what was not inspected.

## Confirmed defects

Link open FIX records separately; do not present suspicions as confirmed defects.

## Next decision

One bounded next action and its required authority. This snapshot grants no approval.
