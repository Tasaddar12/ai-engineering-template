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
- Narrowed dispatch guidance to active path ownership and immutable snapshots;
  documented interim chunk events, coder continuation and the host-without-events
  fallback. A plan SUMMARY is required only at final completion.
- Retired and explicitly rejected `--no-review`, retaining the mandatory final
  integrated independent review. Moved operational route/chunk/review/evidence
  inputs to the ignored `.worktrees/pipeline-inputs/` directory.
- Clarified that the runtime records argv results but does not interpret test logs
  for zero-run/all-skipped suites. Mandatory test adapters must assert expected
  counts and unexpected-skip policy; the shared scout role stays host-agnostic.

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

- `python -m unittest tests.test_agent_sources tests.test_workflow_links tests.test_parallel_contracts -v` - 22 passed.
- `git diff --check` — passed.
- Execute-phase, quick and verify-work command/skill mirror comparisons — all equal.
- `git diff -- .planning` — empty.

## Deferred

Final aggregate checks and fresh independent review are coordinator-owned after
the runtime and documentation slices are integrated.

## PR56/PR57 rebase reconciliation (2026-10-08)

The user authorized rebasing PR57 onto merged PR56 while preserving both
behaviors. Work was confined to the registered isolated checkout
`D:/Codex/2026-10-08/task-3/rebase-reconcile`, branch `phase-pr57-rebase`.
The clean starting head was `15b8223e0c875324118009b01f14b14713f16035`;
main was `6e3280a06b680547972fe9def3240f872fb842dd`. The recoverable
`backup/pr57-before-pr56-rebase-15b8223` remains coordinator-owned.

The default rebase flattened old completed integration merges, replaying all
runtime slices and the final `dd00e0f`, `f8b13a2` and `f025760` corrections.
Conflicts were resolved by combining the contracts, without wholesale ours/theirs
selection or changes to adoption records, benchmark fixtures, pins or Git settings.
No push, PR merge, benchmark run or edit to the original checkout occurred.

- Preserved PR56's `verification_checks.py`, receipt/environment/resource behavior,
  guarded final-nonpass bookkeeping compensation, provisional/final verifier
  lifecycle, repeated-ship currentness and specialist evidence ownership.
- Preserved PR57's immutable registered chunk IDs, detached reviewer/test SHA
  gates, dependency/path/resource readiness, schema-validated source packets,
  empty-directory topology, actual PATH executable identity and canonical root
  aliases. `pipeline.py` and `evidence.py` are byte-for-byte unchanged from the
  original PR57 head; PR56 verification implementation and shipping/evidence
  contracts are unchanged from main.
- Reconciled full PR56 scout task/output and requested-field schemas with PR57
  validated-packet reuse, bounded distinct questions, lifecycle waiting and
  read-only Luna authority. Retained mandatory final independent review and the
  unsupported `--no-review` rejection. Command and skill mirrors remain exact.
- Distinguished registered chunk readiness from ordered legacy waves for
  completed unregistered whole-plan assignments. Legacy overlapping ownership
  assertions remain; efficiency assertions additionally require the registered
  path/resource/dependency contract. The scout procedure now tests all seven
  numbered steps and both PR56 schema and PR57 lifecycle requirements.

### Rebase validation

- `python -m unittest tests.test_agent_sources tests.test_workflow_links tests.test_unattended_flow tests.test_parallel_contracts tests.test_efficiency_contracts -v`: 39 tests, 38 passed; one expected failure in the reserved adaptation guide scheduling assertion. No skip or other failure. Final log: `.worktrees/rebase-validation/rebase-contract-final.log`.
- `tests.test_verification_bookkeeping`: 3/3 passed; `tests.test_verification_receipts`: 34/34 passed in the initial focused 76-test run. That run's four contract failures were reconciled to the one adaptation-only failure above; its combined result was not a full pass. Log: `.worktrees/rebase-validation/rebase-contract-tests.log`.
- `python -m unittest tests.test_parallel_pipeline tests.test_evidence_cache -v`: 43 tests, 38 passed, five expected Windows platform/privilege skips, no failures, 188.457 seconds. Log: `.worktrees/rebase-validation/rebase-runtime-tests.log`.
- Exact source comparisons confirmed original PR57 `pipeline.py`/`evidence.py` and main's PR56 verification implementation, ship workflow, verification-evidence reference and `.planning/` were preserved. Every changed path belongs to the original PR57 scope or the explicitly authorized inherited efficiency test.
- `git diff --check`, command/skill byte comparisons, conflict-marker and UTF-8 checks passed. No aggregate duplicate, heavy engine, Docker or model benchmark was run.

### Remaining integration obligation

`.ai/references/agent-adaptation.md` is reserved for a separate doc-writer;
this coder did not edit it. Its Schedule work operation must distinguish
`pipeline.route` for registered chunks from dependency and file-overlap waves
for completed unregistered whole-plan assignments. The guide also needs isolated
executor worktrees and the distinction between `pipeline.run-checks` and
final/legacy `verification.run-checks`. The new scheduling assertion remains
honestly failing until that guide is integrated. Final aggregate checks and fresh
independent review are coordinator-owned on the integrated frozen tree.
