---
id: TASK-048
title: Apply validated decomposition revisions with lineage
status: ready
plan: PLAN-002
depends_on:
- TASK-047
scope:
- src/ai_engineering/planning.py
- tests/test_planning.py
resources:
- planning-api
acceptance:
- Accept complete reasoned revision proposals with replacement task lineage, scoped
  supersession and newly required prerequisites; validate the full resulting graph
  before writes.
- Preserve unaffected completed tasks/features and retained dependencies while redirecting
  incoming/outgoing edges to explicit replacements.
- Rejected revisions leave original artifacts intact. Accepted revisions preserve
  superseded history, create .ai tasks/features, and produce an approved replacement
  decomposition.
validation:
- tests
- lint
- format
- types
batch: planning
effort: 3
context:
- ARCHITECTURE.md
- .ai/decisions/ADR-006.md
- .ai/plans/active/PLAN-002.md
---
# TASK-048 — Apply validated decomposition revisions with lineage

## Acceptance criteria

- Accept complete reasoned revision proposals with replacement task lineage, scoped supersession and newly required prerequisites; validate the full resulting graph before writes.
- Preserve unaffected completed tasks/features and retained dependencies while redirecting incoming/outgoing edges to explicit replacements.
- Rejected revisions leave original artifacts intact. Accepted revisions preserve superseded history, create .ai tasks/features, and produce an approved replacement decomposition.

## Ownership boundary

Recovery supplies the reasoned proposal; this boundary validates and applies it and must not manufacture scope expansion authority.

Follow the public contract and task/feature references in [PLAN-002](../../plans/active/PLAN-002.md). Historical implementations are evidence only.
