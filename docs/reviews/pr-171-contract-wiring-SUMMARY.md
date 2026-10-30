---
status: complete
input_revision: 1324570d282ed3054c88b0ed2e773a6a1f090616
branch: review-pr171-contract-comments
---

# PR 171 dispatch record and retained hook wiring

## Changes

- CR01: Normal `dispatch-isolation --phase PHASE --plan PLAN` calls now atomically
  persist the validated mode, host, phase, plan identifier and current revision.
  Plan identifiers must belong to the supplied phase. A later plan replaces the
  single-slot record. Inspection and unscoped probes preserve existing bytes.
- CR03: Restored the small parent closed capability renderer, with its retained
  config conditions, agent/skill/query references and metadata. Registered both
  `loop render-hooks EVENT` and `loop.render-hooks EVENT`, plus catalog/event views.
  Query references use current registered names. Removed the retired broken-windows
  hook and instructions. No dynamic registry, shell execution or new configured
  roles were introduced.
- `ship:post` is a known event with no catalog hooks, matching the parent catalog;
  other events render real conditional entries. No new postship agent or review
  was invented. The parent catalog declares no `consumes` entries; the restored
  API does not add artifact consumption obligations or execute dispatches.
- Clarified the existing estimate compatibility behavior: historical SUMMARY
  estimates may supply raw estimates when a PLAN estimate is absent.

## Checks

- `python -m unittest tests.test_dispatch_contracts tests.test_loop_hooks tests.test_native_worker_receipts tests.test_research_contracts tests.test_retained_planning_tools -q`:
  26 passed in 79.186 seconds. This exercises sequential plan recording without
  force, inspection byte preservation, generic probe preservation, malformed plan
  rejection, both render command spellings, enabled/disabled catalog conditions,
  current query names, unknown event rejection, native receipt lifecycle and the
  preceding research/calibration contracts.
- `git diff --check`: passed.

## Remaining

Coordinator-owned ship protocol and per-plan worktree documentation are not edited
here. The combined frozen verification batch remains coordinator-owned.
No project identity, shared planning records or YAML files were changed.

## Self-Check: PASSED

Owned source, tests and this report exist. No stubs or additional threat surface
beyond the assigned contained dispatch record and data-only renderer were found.
