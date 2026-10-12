# Planning Audit Documentation Summary

**Status:** Documentation for Tasks 1-3 complete. Final combined verification
and independent documentation review remain coordinator-owned.

## Task 1: Canonical review and correction handoff

- Defined one `PLAN REVIEW` result for phase planning and validated quick
  planning. `approved` requires conclusive mandatory goal, safety, coverage,
  task, ownership and dependency checks with no blockers or warnings. INFO
  advisories may accompany approval and remain visible. Findings carry stable
  IDs, authority citations, observed evidence and optional non-binding hints;
  reports record revisions, reviewed plans, coverage and prior
  content-sensitive evidence.
- Wired targeted preparer and fresh independent checker prompts through the
  same `<revision_context>` packet in both callers. Corrected properties are
  inspected directly; missing evidence requires a full applicable assessment,
  and ownership/dependency changes require the full graph check. Existing
  revision limits and `REVISION_CONFLICT` handling remain in place.
- Reconciled severity guidance and examples; sizing preferences/counts alone
  are advisory. Task1 source commit: `91a609ebd38fb076965adbd8a0ca3972cbc1c4e4`.

## Task 2: Map refresh instructions

- Moved relevant-map status/refresh after context loading and before research
  or plan preparation. The workflow selects `tech`/`arch` from the named phase
  interfaces, skips irrelevant or fresh maps, refreshes relevant missing/stale
  maps, waits for integration and passes current paths to consumers. The same
  rule applies to gap and correction scope; freshness thresholds and source
  sensitivity remain owned by `codebase.status`.
- Inspected the integrated runtime at `f713a9e77f63a03c1655afb4261683f04c3b7e02`:
  `codebase.status` returns each map's `focus`, `path` and `state` and uses
  configured positive overrides or the existing defaults: STACK after 1 source
  commit and ARCHITECTURE after 15 (`.ai/runtime/lib/codebase.py:23-42,54-60`);
  `PLANNING_AGENTS` includes `codebase-mapper`, and `plan_phase` resolves models,
  efforts and installed-agent metadata through existing helpers
  (`.ai/runtime/lib/bundles.py:18,59-63,79-83`). The committed
  `.ai/maintenance/planning-audit-runtime-SUMMARY.md` reports focused `Bundles`
  (11), `Dispatch` (15) and `CodebaseMapFreshness` (13) tests passing.

## Task 3: Runtime and index claims

- Replaced `phase.py check` claims with direct, bounded inspection of assigned
  PLANs against `TEMPLATE-CONTRACT`, separate from semantic assessment. The
  documented optional `python .ai/runtime/phase.py query planning.review` is a
  read-only whole-planning-tree audit, not a per-correction gate.
- Corrected index claims against `.ai/runtime/lib/phases.py:372-389`:
  `plan_index` returns phase/directory/count and plan ID, file path, declared
  dependencies and optional summary path; it does not derive waves. Wave
  grouping, ordered integration/checks and concurrency constraints are
  attributed to the coordinator's `execute-phase` instructions
  (`.ai/workflows/execute-phase.md:307-329,331-366`).
- Verified the command route against `.ai/runtime/phase.py:847-879` and
  `VERBS` (`:740-817`): the CLI accepts `query` and `init`; `planning.review`
  is a query verb and no `check` verb exists. `planning_review.review` delegates
  to `_audit`, which iterates the planning tree (`.ai/runtime/lib/planning_review.py:221-235,288-343,486-488`).

## Files

- `.ai/workflows/plan-phase.md`
- `.ai/agents/phase-preparer.md`
- `.ai/agents/phase-checker.md`
- `.ai/references/methods/gates.md`
- `.ai/references/agent-adaptation.md`
- `.ai/templates/phase-prompt.md`
- `.ai/references/methods/planner-chunked.md`
- `.ai/references/template-adaptation.md`

## Checks and remaining work

- A prior Ubuntu CI run found one wording regression in
  `test_execute_keeps_dependency_waves_and_uses_receipts` (the canonical phrase
  `dependency and file-overlap waves` was missing from the Schedule work row);
  that run reported 556 tests, one failure and 13 skips. The local full-suite
  run was interrupted with the same failure. GitHub run `38258207986` concluded
  cancelled and the Windows job was cancelled. All four hooks passed (235
  checks).
- Restored the tested phrase while keeping `phase-plan-index` inventory-only and
  assigning prerequisite/file-overlap grouping and ordered integration checks
  to the coordinator's `execute-phase` procedure. The authorized focused command
  `python -m unittest discover -s tests -p test_efficiency_contracts.py -v`
  passed: 8 tests, including the regression test.
- `git diff --check` passed; manually inspected the changed row against the
  workflow source and reviewed the exact two-path diff. No benchmarks ran.
- Independent documentation verification, combined acceptance and repository
  final checks remain with the coordinator.

## Wording and report-format correction

- Rephrased the structural-check guidance as direct PLAN inspection against the
  runtime contract, with independent semantic review and optional whole-tree
  `planning.review` inventory. Described `phase-plan-index` as an inventory and
  assigned eligible wave grouping, ordered integration and checks to the
  `execute-phase` coordinator procedure.
- Converted the assigned long operational paragraphs to concise imperative
  lists while preserving code, issue examples, safety constraints, dependency
  rules and revision limits.
- Updated the checker to use one human-readable Markdown report with distinct
  approved and needs-revision layouts, mandatory per-check coverage, a plan
  inventory, stable findings grouped by severity, and lossless mapping to the
  existing correction issue fields. Approval still requires conclusive mandatory
  checks and zero blockers/warnings; INFO remains visible and non-blocking.
- Correction packets now reference the captured prior report by its result
  destination and carry issue payloads once, rather than embedding the report
  body. The independent checker still inspects corrected content and reuses only
  evidence whose compared inputs are unchanged.
- Representative wording: “There is no `phase.py check` command” became “Inspect
  the assigned PLANs directly against the runtime contract for structural
  readiness, then assess goal delivery and semantic feasibility independently.”
  Index wording now directs readers to `phase-plan-index` for IDs, paths,
  dependencies and summaries, then to `execute-phase` for coordinator wave
  grouping and integration/check order.

Changed paths in this correction:

- `.ai/agents/phase-checker.md`
- `.ai/agents/phase-preparer.md`
- `.ai/references/methods/gates.md`
- `.ai/references/methods/planner-chunked.md`
- `.ai/references/methods/planner-revision.md`
- `.ai/references/template-adaptation.md`
- `.ai/templates/phase-prompt.md`
- `.ai/templates/planner-subagent-prompt.md`
- `.ai/workflows/plan-phase.md`
- `.ai/workflows/quick.md`

**Checks:** `git diff --check` passed. The writer ran no tests or benchmarks;
coordinator-reported static-document suite results are listed below. Independent
documentation verification remains coordinator-owned.

## Coordinator follow-up

- Refined the report guidance into explicit approved and needs-revision
  templates, removed the duplicate ID field, and clarified the lossless Markdown
  finding-to-handoff mapping.
- The coordinator reports the affected static-document suites passed:
  efficiency-contracts (8), workflow-links (3) and agent-sources (16). The writer
  did not run those suites.
- Staging is blocked: Git cannot write the linked worktree's shared index, and
  auto-review rejected the escalation requests. The edits remain unstaged for
  coordinator handling; no commit was created.
