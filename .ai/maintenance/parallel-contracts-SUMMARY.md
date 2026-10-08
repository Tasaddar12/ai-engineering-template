---
status: complete
repository: D:/Codex/2026-10-08/task-3/contracts-worker
branch: phase-parallel-contracts
base: aa0b0443aa3e583e8a60370928c44b5edc9463c6
slice: workflow/agent/handoff contracts for the parallel chunk pipeline
---

# Parallel pipeline contract maintenance

## Changes

- Documented readiness routing by registered prerequisite chunks, exact
  independently reviewable path subsets, and named resources. Independent ready
  work continues while each committed chunk is reviewed and checked on separate
  detached snapshots. Dependent work waits for prerequisite gates, integration and
  unchanged relevant evidence.
- Aligned phase and quick workflows with runtime-owned `pipeline.*` and
  `evidence.*` CLI schemas. The coordinator merges only the registered immutable
  head after applicable gates pass; `pipeline.integrate` validates and records
  that Git revision. Preserved the completed legacy whole-plan merge fallback
  without making it a barrier for routed chunks.
- Added chunk-handoff and source-evidence packet templates, including explicit
  cache reuse/invalidation and provisional evidence boundaries. Updated reviewer
  instructions to return the schema-1 report accepted by `pipeline.record-review`.
- Removed the unconditional minimum of two scouts. Dispatch is cache-aware and
  limited to distinct questions; Luna scouts extract or propose from evidence but
  do not implement, execute checks, or make correctness/security verdicts.
- Updated install entry points, runtime overview, template contract, rules and
  command/skill mirrors. Added tests for the cross-file pipeline, scout and mirror
  contracts; kept `.planning/` untouched.

## Files

Updated `AGENTS.md`, `.ai/install-assets/agent-entry.txt`, `.ai/RULES.md`,
`.ai/agents/{README,coordinator,coder,code-reviewer,scout}.md`,
`.ai/references/{scout-dispatch,worker-handoff,parallel-pipeline}.md`,
`.ai/runtime/{README,TEMPLATE-CONTRACT}.md`,
`.ai/workflows/{execute-phase,verify-work,quick}.md`,
`.ai/commands/{execute-phase,verify-work,quick}.md`, their matching
`.agents/skills/*/SKILL.md`, `.ai/templates/{chunk-handoff,scout-packet}.md`,
`tests/test_parallel_contracts.py`, `tests/test_workflow_links.py`, and this
summary.

No runtime Python was edited. PR56 compatibility, frozen benchmarks and pins
were left unchanged. No checkout switch, Git merge or push was performed.

## Validation

- `python -m unittest tests.test_parallel_contracts tests.test_workflow_links tests.test_unattended_flow -v` — 17 passed.
- `git diff --check` — passed.
- Execute-phase, quick and verify-work command/skill mirror comparisons — all equal.
- `git diff -- .planning` — empty.

## Deferred

Final aggregate checks and fresh independent review are coordinator-owned after
the runtime and documentation slices are integrated.
