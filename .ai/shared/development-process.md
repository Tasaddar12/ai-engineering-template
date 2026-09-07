# Contributing

The repository ships a working bootstrap installer, plan/task record CLI, and foundation validator. Install with `python -m pip install -e ".[dev]"`; validate with `python src/validate_foundation.py`. Planned orchestration and provider runtime tests will be added by their owning tasks and are not represented as passing today.

Read the plan and isolation report. Claim one dependency-ready task using the future coordinator or a documented manual state checkpoint until it exists. Create `ai/PLAN-001/TASK-NNN/a1` in a dedicated worktree from the accepted prerequisite integration commit. No two active task agents share a worktree or edit coordinator state.

Use Python 3.11+, full annotations on public APIs, immutable dataclasses for domain values, Protocols at side-effect boundaries, and explicit errors. Avoid a generic plugin system until adapters require one. JSON Schema defines wire contracts; typed parsing models must match it. Test behavior, failure recovery, and observable outcomes rather than implementation shape.

Changes to a shared schema/interface require a prerequisite contract task and graph re-review. Place task-specific notes and tests within declared ownership paths. Central docs, package metadata, exports, and registries have single owners; don't casually edit them from feature tasks.

Reviewers need exact base/head, scope diff, acceptance evidence, and context fingerprint. Every applicable checklist item needs evidence; justified N/A is allowed, silent omission is not. Both reviews use independent invocations. Fixes require fresh review results.

Commits must contain no secrets or transient credentials. PR descriptions explain problem, change, resulting behavior, actual validation, and remaining risk. Archive only after integration and observed merge gates. Release and license selection are later decisions.
