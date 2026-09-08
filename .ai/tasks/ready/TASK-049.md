---
id: TASK-049
title: Resolve model profiles and invoke provider bridge
status: ready
plan: PLAN-002
depends_on:
- TASK-045
scope:
- src/ai_engineering/agents.py
- tests/test_agents.py
resources:
- agents-api
acceptance:
- Resolve role definition -> profile -> provider/model/reasoning and permissions independently
  for all seven roles; reject missing profiles and inadequate reviewer configuration.
- CommandAgentProvider uses only the runner and a configured bridge with permission-boundary
  attestation; persist YAML request/result metadata and validate returned status/output.
- Preserve implementation session IDs on repair and require independent reviewer identity;
  never fabricate provider success or a PASS when the bridge is absent.
validation:
- tests
- lint
- format
- types
batch: agents
effort: 3
context:
- ARCHITECTURE.md
- .ai/decisions/ADR-006.md
- .ai/plans/active/PLAN-002.md
---
# TASK-049 — Resolve model profiles and invoke provider bridge

## Acceptance criteria

- Resolve role definition -> profile -> provider/model/reasoning and permissions independently for all seven roles; reject missing profiles and inadequate reviewer configuration.
- CommandAgentProvider uses only the runner and a configured bridge with permission-boundary attestation; persist YAML request/result metadata and validate returned status/output.
- Preserve implementation session IDs on repair and require independent reviewer identity; never fabricate provider success or a PASS when the bridge is absent.

## Ownership boundary

Bridge credentials, paid use and real invocation remain gated by configured authority; tests use controlled providers.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
