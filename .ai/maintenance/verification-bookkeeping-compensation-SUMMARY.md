# Verification bookkeeping compensation

Date: 2026-10-08
Branch: `codex/workflow-efficiency-contract-fixes`

## Delivered

- Added a narrowly guarded coordinator-only `git revert` for the exact
  success-bookkeeping commit when the final verifier returns a nonpass. Guards
  require a clean worktree, exact expected HEAD and parent, and changes limited
  to ROADMAP, STATE and REQUIREMENTS. Conflicts/failed guards preserve work and
  block completion; corrected status is written through the runtime before a
  fresh final nonpass reconciliation.
- Added the only matching exception to runtime-only planning-record rules and a
  real temporary-Git regression proving the revert restores planning records,
  preserves source, and rejects a mixed source/bookkeeping commit.
- Ship reuses a current passed report and still-valid preflight receipts when
  its same-branch preparation record was already present; any needed verifier is
  resumed only after checks join.
- Removed the verifier's remaining unconditional duplicate key-link trace.

## Validation

- `python -m unittest discover -s tests -p test_verification_bookkeeping.py` — 3 passed
- `python -m unittest discover -s tests -p test_efficiency_contracts.py` — 6 passed
- `python -m unittest discover -s tests -p test_agent_sources.py` — 12 passed
- `python -m unittest discover -s tests -p test_workflow_links.py` — 3 passed
- `python -m unittest discover -s tests -p test_unattended_flow.py` — 10 passed
- `git diff --check` — passed

## Notes

- No runtime API or source behavior changed; full validation remains with the coordinator.
