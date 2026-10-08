---
status: complete
base: dcb5c78af583a09e508194925b25686d0776e759
branch: codex/workflow-efficiency-docs
scope: authorized workflow and role contract maintenance
---

# Workflow and role efficiency contracts

Updated the reusable workflow template to route evidence work conditionally,
consume deterministic check receipts, and reconcile independent reviewer
evidence on a frozen revision while preserving ordered dependency/file-overlap
waves. Verification remains read-only on product/source; the coordinator saves
the tracked report with its actual tested revision and applies a narrow
report-only publication currentness rule.

## Changes

- Replaced the blanket scout fanout rule with conditional discovery and
  complementary specialist dispatch, retaining assignment/result schemas and
  revision/path/line citations.
- Aligned shared rules, every non-scout role adapter, agent catalog, installer
  entry description and scout contract tests with the conditional policy.
- Clarified independent role ownership: code-reviewer handles correctness and
  security; doc/integration specialists handle bounded claims; verifier
  reconciles evidence and inspects selectively for gaps or conflicts.
- Updated execute, verify and ship workflows to use successful runtime receipts,
  dispatch applicable read-only evidence against a frozen revision, and route
  AI diagnosis to failures or ambiguous results. Documented source/environment
  stamps and reuse opt-outs for volatile external state.
- Added `verification-evidence.md` as the shared receipt and coordinator
  currentness contract. Exact revision remains the fast path; only clean-tree,
  per-commit changes to that phase's exact verification report may follow the
  tested revision. Runtime status metadata is explicitly not a freshness gate.
- Made wave behavior explicit: `phase-plan-index` and `execute-phase` process
  ordered dependency and file-overlap waves, with path conflicts isolated.
- Added focused efficiency contract coverage and updated existing agent/workflow
  tests that encoded the superseded mandatory scout minimum.

## Checks

- `python -m unittest discover -s tests -p "test_efficiency_contracts.py"` — 5 passed.
- `python -m unittest discover -s tests -p "test_agent_sources.py"` — 12 passed.
- `python -m unittest discover -s tests -p "test_workflow_links.py"` — 3 passed.
- `python -m unittest discover -s tests -p "test_unattended_flow.py"` — 10 passed.
- `git diff --check` — passed.

The broader runtime and installation suites are left for the coordinator's
integrated validation. No runtime implementation was changed in this slice.
