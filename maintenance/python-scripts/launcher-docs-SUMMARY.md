# Launcher and workflow documentation closure

## Why

The runtime migration left workflow and agent instructions without the shared identity-checked launcher preamble, three documented discuss-phase modes were missing, and several review-ledger tests still expected retired Node behavior. Auto-advance wording could also dispatch execution without phase-scoped user authorization, and UAT gap provenance needed to match the validated `gap_ids` plan contract.

## Changes

- Added the shared `run-resolver.md` include to every workflow and agent document that invokes `engineer_run`; the launcher snippet and embedded copy now pin `sed` to `LC_ALL=C`.
- Added the `power`, `chain`, and `advisor` discuss-phase procedures. Chain mode keeps discussion interactive and advances to planning only; it does not automatically execute the phase.
- Corrected UAT gap reconciliation instructions to require a unique `gap_id`, a same-phase plan listing it in `gap_ids`, a matching summary, and validated `resolved_by`/`resolved_at` provenance. Removed the obsolete `gap_closure: true` instruction.
- Added a default-not-granted, phase-scoped execution authorization record to the context template and an auto-advance check that preserves prior valid authorization but blocks automatic execution without direct user evidence. Discuss chain clears the ephemeral execute-chain flag and starts planning without auto flags.
- Replaced stale launcher, catalog, chain-mode, and Node-ledger test expectations with current shared-reference, Python catalog, plan-only chain, authorization-gate, fail-closed duplicate-ID, and commit-receipt contracts. Kept positive Git receipt coverage.
- Confirmed remaining `.js`/`.cts` mentions in the owned documentation are generic adopting-project examples or explicitly labeled historical artifacts; no active template helper invocation remains in workflow command fences.

## Verification

- `python -I tests/test_runtime_launcher_parity.py` — 60 passed, 5 skipped.
- `python -I tests/test_lint_response_language_coverage.py` — 49 passed.
- `python -I tests/test_workflow_size_budget.py` — 54 passed, 13 skipped.
- `python -I tests/test_code_review_pipeline_regression.py` — 194 passed, 30 skipped.
- `python -I tests/test_python_doc_references.py` — 12 passed.
- `python -I engineer/bin/helper.py gen-health-docs --check` — up to date, 37 codes / 7 repair actions.
- `python -I engineer/bin/helper.py gen-state-md-docs --check` — passed; all targets up to date.

The skipped cases are platform or capability skips reported by the existing suites. Broader integration CI and independent review remain with the coordinator.
