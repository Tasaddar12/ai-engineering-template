# Workflow efficiency contract repairs

Date: 2026-10-08
Branch: `codex/workflow-efficiency-contract-fixes`
Base: `0152e42`

## Delivered

- Verification now starts the verifier, configured checks and applicable
  read-only specialists together on one frozen revision. The initial verifier
  pass is provisional; final status follows the joined evidence.
- A provisional pass commits phase/requirement/session bookkeeping before a
  second frozen reconciliation. The verifier examines that actual record diff
  and source coverage; the coordinator writes and commits the tracked report
  alone as the last local write. The shared reference keeps the existing exact
  revision fast path and bounded report-only currentness rule.
- Verifier methods consume valid receipts and bounded specialist citations,
  account for all acceptance artifacts and links, and reserve direct scans/tests
  for uncovered claims, conflicts or evidence gaps. Matching test/probe receipts
  prevent duplicate runs.
- Ship records a truthful, idempotent pre-publication status before final
  reconciliation. `pr.open` owns the actual PR URL in session metadata, avoiding
  a tracked post-push edit that would stale verification. CI source repairs
  return to verification before another push or judgment.
- Wave descriptions now agree that the plan index defines ordered dependency
  and file-overlap waves, with concurrency inside an eligible wave. Shared
  orchestration rules distinguish write-capable worker ownership from a frozen
  read-only evidence batch.

## Validation

- `python -m unittest discover -s tests -p test_efficiency_contracts.py` — 6 passed
- `python -m unittest discover -s tests -p test_agent_sources.py` — 12 passed
- `python -m unittest discover -s tests -p test_workflow_links.py` — 3 passed
- `python -m unittest discover -s tests -p test_unattended_flow.py` — 10 passed
- `git diff --check` — passed

## Notes

- No runtime implementation or cache behavior changed.
- Full repository/CI validation remains with the coordinator.
