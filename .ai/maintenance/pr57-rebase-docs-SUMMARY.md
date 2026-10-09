# PR57 Rebase Documentation Summary

**The adaptation guide now distinguishes legacy ordered whole-plan waves from registered immutable-chunk routing.**

## Files changed

- `.ai/references/agent-adaptation.md` — clarified the two scheduling modes, `pipeline.route` readiness, isolated executor worktrees, coordinator/runtime responsibilities, chunk versus integrated checks, scoped waits, and mandatory final phase gates.
- `.ai/maintenance/pr57-rebase-docs-SUMMARY.md` — this evidence record.

## Evidence

- The frozen PR57 `.ai/references/parallel-pipeline.md` defines ready/wait/blocked routing, registers immutable chunk revisions, prepares detached reviewer and test snapshots, and allows independent ready coding to continue during gates.
- The frozen PR57 `.ai/workflows/execute-phase.md` directs the coordinator to continue disjoint ready work and wait only on dependent tasks. Its pipeline guidance retains final aggregate verification and integrated independent review.
- The legacy ordered-wave wording remains scoped to unregistered whole-plan assignments. Integration at those wave boundaries is limited to completed unregistered whole-plan assignments, matching the `worktree.merge-wave` fallback constraint. Registered `pipeline.run-checks` receipts cover immutable chunks, while `verification.run-checks` remains the final integrated phase gate.
- Dispatch and lifecycle events remain coordinator/host-owned; runtime state and evidence enforcement remain runtime-owned. No automatic host dispatch or provider prompt-cache/speed behavior is asserted.

## Checks

- Confirmed branch `phase-pr57-rebase-docs` at `6e3280a06b680547972fe9def3240f872fb842dd` with a clean starting tree.
- Focused link check: the relative `parallel-pipeline.md` link resolves to the frozen PR57 reference at `backup/pr57-before-pr56-rebase-15b8223`.
- No broad tests or runtime checks were run; this slice changes documentation only, and the registered pipeline checks remain for the future integrated PR57 tree.

## Remaining

- The linked PR57 pipeline reference is supplied by the parallel pipeline slice and must be integrated with this guide for the link to resolve on the combined tree.