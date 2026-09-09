# Show plan status

## Purpose

Give a read-only snapshot of every plan by lifecycle stage, live state, blockers
and suspected drift.

## Inputs

Config, plan lifecycle records, STATE, current specs, linked intake/FIX records and
read-only revision information from the assigned worktree.

## Gates

Report-only inspection is permitted by [action-approved](../gates/action-approved.md).
Any proposed change follows that gate separately.

## Steps

1. The orchestrator reads every configured plan phase. List all PLAN files, including
   done and abandoned, and show each stage even when empty. List intake separately;
   it is not a plan stage. Flag duplicate IDs or folder/metadata mismatches.
2. For each plan, show its ID/title, record link, actual folder, recorded status,
   review type and recorded progress. Mark missing information Unknown.
3. Summarize Now / Next / Blockers from STATE with links. Include per-plan blockers,
   their owners and resume conditions; distinguish these from global blockers.
4. Compare the records with their linked specs and available observations. List
   suspected drift with evidence and uncertainty, separately from confirmed open FIX
   records. State the inspection boundary; missing evidence does not prove no drift.
5. Return the status template and decision summary. Propose any correction or
   investigation without modifying records, running tests or changing plan stages.

## Output and handoff

A dated report identifying the inspected revision, all stages and plans, live state,
blockers, suspected drift and confirmed defects. The report is a snapshot, not a new
owner of facts. The orchestrator presents the next decision.

## Stop conditions

If records are unavailable, return an explicitly incomplete report with the missing
paths. Do not silently omit plans, declare unknown work done or repair drift.
