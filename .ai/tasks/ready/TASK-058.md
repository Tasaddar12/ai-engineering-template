---
id: TASK-058
title: Recover structural feature failures automatically
status: ready
plan: PLAN-002
depends_on:
- TASK-057
scope:
- src/ai_engineering/workflows.py
- tests/test_workflows.py
- src/ai_engineering/state.py
- src/ai_engineering/templates/handoffs/agent-recovery.md
resources:
- workflows-api
acceptance:
- Recovery receives failed feature, original plan/tasks, all relevant reviews and
  conflict evidence, and returns a reasoned split/reorder/replacement/prerequisite
  proposal.
- Apply revisions through planning, preserve superseded evidence and unaffected completed
  work, redecompose and resume eligible features automatically within existing scope.
- Reject unauthorized material scope expansion and invalid graphs; exhausted attempts
  preserve an explicit blocker and do not corrupt active workflow state.
- State refresh retains feature evidence while indexing BUG review and pull-request
  metadata; workflows regression covers both subject types.
validation:
- tests
- lint
- format
- types
batch: workflows
effort: 3
context:
- ARCHITECTURE.md
- .ai/decisions/ADR-006.md
- .ai/plans/active/PLAN-002.md
kind: tasks
---
# TASK-058 — Recover structural feature failures automatically

## Acceptance criteria

- Recovery receives failed feature, original plan/tasks, all relevant reviews and conflict evidence, and returns a reasoned split/reorder/replacement/prerequisite proposal.
- Apply revisions through planning, preserve superseded evidence and unaffected completed work, redecompose and resume eligible features automatically within existing scope.
- Reject unauthorized material scope expansion and invalid graphs; exhausted attempts preserve an explicit blocker and do not corrupt active workflow state.

## Ownership boundary

Integrate the TASK-054 hook without importing orchestration at module load time; ordinary defects do not enter recovery.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
