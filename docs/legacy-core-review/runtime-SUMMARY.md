# Runtime retirement maintenance summary

## Why

Remove the confirmed retired implementations, CLI exports and exclusive callers identified by the complete legacy-core review. Preserve native manager/pipelines/issues/ideas, independent review, instruction generation, probes, verification and owned-worker safety. This is template maintenance; no adoption or shared planning record was changed.

Repository: `D:/Codex Projects/ai-engineering-template/.worktrees/legacy-runtime-201131548`.
Branch: `phase-legacy-runtime`.
Input revision: `734ecc2cb80e1b72041f0e823802530ce3ed8541` (verified before changes).

## Changes

- Removed dynamic capabilities/hooks, developer profiles/name policy, external CLI review lanes, Claude Workflow orchestration, output overflow protocol and broken-windows implementations with their exclusive tests.
- Removed retired CLI registrations and the unknown-`check.*` compatibility fallback, research cache/confidence/store, estimator/calibration, teams/intel/global learning copy, roadmap annotation, context drift and background PID worker command producers.
- Kept direct retained checks and exposed `check.prohibition-enforcement` directly through the existing real producer/gate. No caller assertion substitutes for actual fail-first enforcement evidence.
- Kept native `review.dispatch`/`review.record`/`review.status`, which record actual scope, reviewer independence and captured revisions. External `--explicit` review selection is rejected.
- Kept native instruction generation (`project-instruction-file`, `generate-claude-md`), bounded phase research/discussion/pattern inputs, map stamp/drift/status, security/UI/TDD checks and worker liveness/terminal-receipt/unknown-worker preservation.
- Removed package/test command inference and obsolete configuration defaults, including `runtime`, external-review settings, build/test inference settings, broken windows, context drift and `plan_chunked`. Closed validation rejects obsolete keys. Host identity comes from `runtime-identity.host`; no adoption configuration was rewritten.
- Removed detector, backup and orphan restoration code/routes from installation.py. Coordinator confirmed the supported pinned ownership-manifest updater separately owns update/recovery. Installed provenance/context and pinned change inspection remain. Existing backups were not altered.
- Quick-batch completion persists a durable `completionTransaction` in BATCH.json before updating authoritative QUICK.md. Resume validates the integrated source/PLAN/SUMMARY evidence and replays that intent idempotently. Pending completion intent cannot be silently cancelled or changed. No completion or recovery reads/writes the retired STATE quick-task table.
- Removed only the retired QuickTasks table schema/helpers and obsolete validation contracts (AI integration W016/repair action, ship capability hook shape, advisor/chain checks, automatic checkpoint approval protocol, GRAPHIFY exemption). Generic table parsing and other guards remain.
- Updated CLI documentation and focused shared tests; added behavioral retirement, native review, prohibition-proof and interrupted-completion regressions.

## Verification

- `python -m compileall -q engineer/bin tests`: passed.
- Imported every retained `engineer/bin/lib/*.py` module: all 77 imports passed.
- `python -m unittest tests.test_health_diagnostic tests.test_gen_health_docs tests.test_artifacts tests.test_markdown_table -q`: 224 tests passed, including one expected failure.
- `python -m unittest tests.test_quick_batch tests.test_legacy_runtime_retirement -q`: 9 tests passed; covers real Git implementation evidence, rejection of 34 retired/unknown routes without record mutation, closed configuration, native reviewer revision checks and fail-closed prohibition evidence.
- `python -m unittest tests.test_engineer_cli tests.test_misc_verbs tests.test_code_review_flags tests.test_code_review_depth tests.test_verification_receipts tests.test_verify_checks tests.test_scope tests.test_plan_checks tests.test_model_omit_when_inherit_guard tests.test_workflow_size_budget tests.test_check_contract_drift -q`: 333 tests run; 331 passed/skipped/expected-failed; two stale GRAPHIFY exemption assertions failed and were updated to verify no exemption.
- `python -m unittest tests.test_check_contract_drift tests.test_engineer_runtime tests.test_legacy_runtime_retirement -q`: corrected rerun passed all 146 tests, with two skips and one expected failure. Includes retained real Git/worktree and planning safety behavior.
- `python -m unittest tests.test_quick_batch -q`: final five tests passed after adding the pending-transaction update guard.
- `git diff --check`: passed after removing trailing blank lines.
- Initial targeted run exposed stale health counts and a one-item new batch fixture; corrected assertions/fixture, and affected tests passed. No failed outcome is represented as a pass.

## Rows

Authorized rows: V01,03,08-10,12,13,19,22,27,30,52,53,57,74,75,79,82,98,119-121,135-139,142-145,148,149; C04,11,14-16,18,21,28,38; R-WF181.

## Deleted paths

- engineer/bin/lib/capabilities.py
- engineer/bin/lib/capability_registry.py
- engineer/bin/lib/profile_output.py
- engineer/bin/lib/runtime_name_policy.py
- engineer/bin/lib/review_lane_descriptor.py
- engineer/bin/lib/review_execution.py
- engineer/bin/lib/quality.py
- engineer/bin/lib/claude_orchestration.py
- engineer/bin/lib/io_output.py
- tests/test_capability_registry.py
- tests/test_profile_output.py
- tests/test_runtime_name_policy.py
- tests/test_review_lane_descriptor.py
- tests/test_claude_orchestration.py
- tests/test_io_output.py

`tests/test_review_execution.py` did not exist. No other whole files were deleted.

## Deferred / integration obligations

- Agent/command/skill/workflow/reference callers are owned by parallel workers and require merged-tree checks. Health generated workflow tables must reflect 36 codes and six repair actions.
- Full repository tests were not run; the maintenance plan identifies pre-existing general semantic/installer migration gaps. Existing skips/expected failures in targeted source-linked guard suites remain visible.
- Independent review and verification belong to the coordinator at the integrated revision. This worker does not publish, merge, change shared records or certify the entire parent PR.
