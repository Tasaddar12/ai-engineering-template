# Validation correction: retained workflow execution

## Why

Independent review and the integrated test run identified six concrete workflow blockers after retirement. Repair their actual dispatch, gate and flag paths while preserving the complete retained methods. No files were deleted and no runtime source, shared planning record or publication state was changed.

## Changes

- CR01: the TDD gate uses registered query tdd.review-checkpoint, captures its actual result, parses block and stops on invocation/parse failure.
- CR02: Quick coordinator now parses exact plan scope, initializes an owned manifest, calls worktree.create before native dispatch, parses actual root/branch/base/scope fields, validates the checkout and generates a literal runnable root guard. The native host must bind the worker to that actual checkout; the child only verifies the root. Harness and orchestrator paths both record actual host terminal evidence before merge-wave/cleanup-wave. Removed the primary-checkout/worktree-opt-out route. Quick planner, discussion, research, executor and verification bodies remain; required SUMMARY output is committed.
- CR03: execute-phase, the isolation dispatcher and quick-batch use the native-host receipt procedure: actual host id/status from the native wait/status tool, original host event preserved, Git-observed checkout identity/head, schema-bound receipt, record-agent attachment to the same owned manifest before merge. Artifact presence, timeout and agent claims cannot establish stop. Quick-batch creates/parses its native checkout before dispatch, commits SUMMARY, preserves per-item scope and actual host identity, and projects only its deterministic mergeable prefix from the receipt-bearing runtime manifest. Missing ownership/receipt blocks recovery instead of recreating an ownerless manifest or inventing an agent id.
- CR04: restored retained --tdd, --text and --no-reversibility-gates initialization: TDD uses the direct shared setting, text mode comes from init/argument and reversibility defaults true with explicit false override. No retired planning features were restored.
- CR05: restored debugger resolve-model and resolve-effort bindings, with conditional omission on inherit/empty; removed remaining inline-primary diagnosis fallback instructions.
- CR06: manager plan/execute handlers invoke their complete pipelines inline, preserving native worker boundaries and existing runtime APIs. Removed the unreachable capability-registry/background-orchestrator branches and claims.

## Verification

Root: D:/Codex Projects/ai-engineering-template/.worktrees/validation-workflows-203732369.
Branch: phase-legacy-validation-workflows.
Verified starting revision: 7605c4f6653f0a4cbb8673fcc26fc95a55f125ec.

- git diff --check: passed.
- Valid model source guards: python -m unittest tests.test_model_omit_when_inherit_guard.PlaceholderBinding tests.test_model_omit_when_inherit_guard.SpawnCoverage tests.test_model_omit_when_inherit_guard.OmitRule — 21 tests passed in 8.618 seconds. Full module run had 26 tests with one skip and only the obsolete ModelReference check failing because model-profile-resolution.md was deliberately deleted; sibling runtime correction owns that test retirement.
- Actual Quick setup/root guard Bash blocks executed against a real temporary Git repository and the actual CLI: owned checkout created at captured base; generated guard accepted that checkout and rejected the primary checkout with exit 42. Repeated with an actual checkout path containing an apostrophe and a space: passed.
- Actual retained plan flag Bash block executed with the actual CLI: default flags, explicit --text/--tdd/--no-reversibility-gates and init-provided text_mode cases all passed.
- Markdown/Bash comparison against assigned base: 78 original and 85 edited bash fences; no new unbalanced/nested fences or bash -n failures.
- Normalized changed-workflow local links: no newly broken source/target pairs.
- scripts/verbs.py: registered direct calls remain recognized; the five baseline unknown sites remain (README VERB/help placeholders, git-integration milestone.release-tags twice, progress query progress).
- Exact ownership audit: only engineer/workflows plus this summary, no deleted paths.

The receipt attachment depends on the parallel runtime correction 0a028616d2c3a58fb7e16d99c86342dc3cd10e6e: create initially uses its plan id placeholder; the first validated terminal receipt binds the actual host id once. This workflow slice uses the confirmed unchanged receipt schema. The runtime coder independently reported five passing real Git receipt lifecycle tests, including actual merge and refusal cases. Merged integration verification remains coordinator-owned; no claim is made that a real external native host worker was launched during these isolated fixtures.

## Rows

Independent findings CR01–CR06, correcting retained TDD, native isolated execution, host terminal proof, planner flags, debugger model binding and manager routing after WFL02–WFL05 retirement. No unrelated parent migration gaps were expanded.
