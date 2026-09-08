---
id: TASK-040
title: Persist Markdown artifacts and strict YAML configuration
status: completed
plan: PLAN-002
depends_on: []
scope:
- src/ai_engineering/errors.py
- src/ai_engineering/io.py
- src/ai_engineering/artifacts.py
- src/ai_engineering/config.py
- tests/test_core.py
resources:
- core-api
acceptance:
- Read/write strict YAML mappings and Markdown front matter with stable IDs, kind/status
  locations and atomic replacement; reject duplicate IDs and malformed metadata.
- Create/find/list/save/transition/next_id obey the PLAN-002 ArtifactStore contract
  and preserve bodies and historical records.
- Reject absolute, traversal, symlink and junction escapes. Plans and plan-specific
  contracts are PLAN-NNN Markdown under .ai with explicit tasks/features lists; empty
  lists are allowed only before decomposition.
validation:
- tests
- lint
- format
- types
batch: core
effort: 2
context:
- ARCHITECTURE.md
- .ai/decisions/ADR-006.md
- .ai/plans/active/PLAN-002.md
kind: tasks
---
# TASK-040 — Persist Markdown artifacts and strict YAML configuration

## Acceptance criteria

- Read/write strict YAML mappings and Markdown front matter with stable IDs, kind/status locations and atomic replacement; reject duplicate IDs and malformed metadata.
- Create/find/list/save/transition/next_id obey the PLAN-002 ArtifactStore contract and preserve bodies and historical records.
- Reject absolute, traversal, symlink and junction escapes. Plans and plan-specific contracts are PLAN-NNN Markdown under .ai with explicit tasks/features lists; empty lists are allowed only before decomposition.

## Ownership boundary

Storage owns parsing and lifecycle location, not Git execution or provider calls.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
