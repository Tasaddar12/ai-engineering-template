# Feature Complete

## Subject

FEATURE-004

## Session Id

native-execution-agents

## Status

COMPLETE

## Summary

Configured roles/model profiles, structured immutable handoffs, attested command bridge, resumable bound outputs and one critical review contract.

## Changed Files

- src/ai_engineering/agents.py
- src/ai_engineering/handoffs.py
- src/ai_engineering/review.py
- tests/test_agents.py
- src/ai_engineering/templates/handoffs
- src/ai_engineering/definitions

## Tasks Completed

- TASK-049
- TASK-050
- TASK-051

## Validation

- Windows full suite:73 passed,2 symlink privilege skips before one additional agent
  transport regression.
- Final agent suite:23 passed.
- Ruff lint/format and native mypy12modules pass; Linux-target mypy new3modules pass.
- Independent earlier Linux agent snapshot:19 passed; final expanded Linux run pending.

## Documentation

Definitions expose output_schema and phase-specific templates; module docs describe trusted bridge protocol, deterministic replay and uncertainty boundary.

## Assumptions

Real providers require an explicit model, configured trusted bridge and configured authority. Test bridges are local controlled adapters.

## Deviations

Optional phase parameter and read-only preflight added to agreed APIs; separate agent-output templates preserve planning renderer compatibility.

## Structural Issues

[]

## Context Refs

- AGENTS.md
- .ai/plans/active/PLAN-002.md
- ARCHITECTURE.md
- docs/workflows.md
- .ai/constraints.yaml
- .ai/project/commands.yaml

## Constraints

.ai/constraints.yaml

