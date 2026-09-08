---
id: HANDOFF-PLAN-002-DECOMPOSITION
plan: PLAN-002
status: approved
agent: work_decomposition
task_count: 23
feature_count: 7
features:
- FEATURE-001
- FEATURE-002
- FEATURE-003
- FEATURE-004
- FEATURE-005
- FEATURE-006
- FEATURE-007
parallel_waves:
- - FEATURE-001
- - FEATURE-002
  - FEATURE-003
- - FEATURE-004
- - FEATURE-005
- - FEATURE-006
- - FEATURE-007
coverage: exactly_once
blockers: []
---
# Decomposition — PLAN-002

## Plan

[PLAN-002](../plans/active/PLAN-002.md), authoritative reset of 2026-09-08. All plans and plan-specific contracts are PLAN-NNN Markdown under .ai with explicit task/feature references; task and feature artifacts are also under .ai.

## Status

APPROVED for implementation scheduling. This approves task/feature structure, not code, security, delivery or external authority. No runtime implementation was performed by this decomposition pass.

## Task Changes

Retained all 23 fresh TASK-040 through TASK-062. Each now has narrow file ownership, concrete observable acceptance and a boundary note. No task was discarded, merged or superseded because each represents a coherent public boundary or integration behavior after refinement. Raised complex state/runner/Git/batching/revision/provider/review/recovery tasks to effort 3; every task remains within effort 1..3 and every feature within five tasks/eight effort. Semantic criteria now distinguish agent judgment from deterministic graph checks. The all-.ai planning rule is explicit in persistence, templates, CLI, escalation and documentation acceptance.

## Features

- [FEATURE-001](../features/ready/FEATURE-001.md): TASK-040, TASK-041, TASK-042; effort 7; prerequisites none.
- [FEATURE-002](../features/ready/FEATURE-002.md): TASK-043, TASK-044, TASK-045; effort 8; prerequisites FEATURE-001.
- [FEATURE-003](../features/ready/FEATURE-003.md): TASK-046, TASK-047, TASK-048; effort 8; prerequisites FEATURE-001.
- [FEATURE-004](../features/ready/FEATURE-004.md): TASK-049, TASK-050, TASK-051; effort 8; prerequisites FEATURE-002.
- [FEATURE-005](../features/ready/FEATURE-005.md): TASK-052, TASK-053, TASK-054, TASK-055; effort 8; prerequisites FEATURE-003, FEATURE-004.
- [FEATURE-006](../features/ready/FEATURE-006.md): TASK-056, TASK-057, TASK-058; effort 7; prerequisites FEATURE-005.
- [FEATURE-007](../features/ready/FEATURE-007.md): TASK-059, TASK-060, TASK-061, TASK-062; effort 8; prerequisites FEATURE-006.

## Dependencies

Task order is preserved within each coherent feature. Cross-feature prerequisites match the plan graph. Core state uses the agreed Git API with controlled test doubles; real integration waits for execution. Core packages model/role assets; agent resolution belongs to agents. Orchestration owns the recovery hook; workflows supplies it through a late import. These are contractual prerequisites, not missing implementations to conceal. No additional prerequisite task is needed within the approved scope.

## Parallel Waves

1. FEATURE-001
2. FEATURE-002, FEATURE-003
3. FEATURE-004
4. FEATURE-005
5. FEATURE-006
6. FEATURE-007

FEATURE-004 can begin after FEATURE-002 code is available even while FEATURE-003 continues; FEATURE-005 waits for both. Runtime concurrency is capped by framework configuration. A task never receives its own worktree merely because it is a task.

## Ownership Checks

All 23 plan task IDs occur exactly once across seven features. Both DAGs are acyclic and every task prerequisite is either in the same feature or reachable through feature dependencies. FEATURE-002 and FEATURE-003 have disjoint source/test paths and exclusive resources. All other overlapping ownership, including core/CLI packaging metadata, is transitively serialized. No database schema exists in this change; core, execution, planning, agents, orchestration, workflows and CLI API resources are distinct. Same-batch source/test overlap is deliberate and handled by one implementer.

## Rationale

Seven feature agents balance bounded context and conflict avoidance. A larger fanout would create shared-module ownership conflicts and unnecessary worktrees; a single batch would obscure validation and review scope. Review stays one independent complete-diff stage. Ordinary defects return to the implementer; structural mistakes return through recovery and this decomposition contract.

## Context Refs

- AGENTS.md
- .ai/STATE.yaml
- .ai/plans/active/PLAN-002.md
- .ai/agents/work_decomposition.yaml
- .ai/templates/agents/work-decomposition.md
- ARCHITECTURE.md
- docs/workflows.md
- .ai/constraints.yaml
- .ai/project/commands.yaml

## Constraints

Writes were limited to fresh .ai plan/task/feature/handoff files and a temporary .ai/local decomposition validator. Coordinator retains exclusive STATE ownership. No Git mutation, provider call, external write or runtime implementation occurred. Repository role permissions describe future runtime behavior; the direct decomposition assignment expressly authorized these local artifact edits.

## Validation evidence

The one-off Python validator `.ai/local/approve_plan_002.py` checked all task/feature metadata, task and feature DAGs, exact coverage, task-to-feature edge preservation, batch limits, resource/path serialization and every parallel wave. It completed successfully using the existing local virtual environment. No product planning implementation exists yet, so this is an independent bootstrap graph check.

The required initial `python -m ai_engineering status` returned `No module named ai_engineering` before runtime installation; this is preserved as baseline evidence and is not an approval of runtime functionality. System Python also lacked PyYAML; the repository virtual environment supplied PyYAML 6.0.3. No dependency was installed.
