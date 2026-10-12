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

- `git diff --check` passed; manually inspected map-step ordering, map status
  fields, caller paths, CLI entry points, index output and coordinator wave
  grouping against committed source.
- No tests run for documentation wording. The three focused runtime test
  results above are reported by the separate Task2 source summary, not run by
  this documentation assignment.
- Independent documentation verification, combined acceptance and repository
  final checks remain with the coordinator. No tests or benchmarks were
  invented or run for this doc-only slice.
