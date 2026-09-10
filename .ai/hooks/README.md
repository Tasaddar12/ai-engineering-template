---
tier: contract
authority: agent
title: Manual checkpoints
---
> Contract: amend with evidence inside the approved scope.

# Manual checkpoints

| Event | Procedure |
| --- | --- |
| Before a new action | [Agent entry point](../../AGENTS.md) |
| Before dispatching a wave | [Orchestrate](../commands/orchestrate.md) |
| Before review | [Track reviewer](../agents/track-reviewer.md) |
| Before done | [Plan done](../commands/plan-done.md) |
| Before Git delivery | [Onboarding PR](../commands/onboard-pr.md) |
| Before exact cleanup | [Orchestration cleanup](../commands/orchestrate-clean.md) |

These are checkpoints, not installed hooks. They make missing evidence
visible without pretending that a document can enforce a sandbox.
Report the checkpoint result; a failing checkpoint holds that transition,
not every independent action in the project.
