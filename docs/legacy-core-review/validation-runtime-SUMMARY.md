# Runtime validation corrections

## Why

Independent review found that a coordinator-created worker could not acquire terminal native-host evidence through the retained record-agent route. Guard suites also still required deleted model, power-mode, execute-plan and initial-read reference surfaces.

Verified root: `D:/Codex Projects/ai-engineering-template/.worktrees/validation-runtime-203733724`.
Branch: `phase-legacy-validation-runtime`.
Input revision: `7605c4f6653f0a4cbb8673fcc26fc95a55f125ec`.

## Changes

- CR03: `worktree.record-agent` now validates and attaches a native-host terminal receipt to an exact existing `worktree.create` ownership entry. It checks plan, path, branch, base, allowed bases, file/deletion scope and manifest/registry identity; then persists matching receipt metadata in both records without adding duplicate entries.
- Creation may use its default plan ID as the pre-dispatch agent placeholder. The first validated terminal host receipt may bind that placeholder to the actual supplied native agent ID. An already bound actual identity cannot be replaced. Workflow owner confirmed new create calls omit `--agent-id` and record the actual host ID only after a native terminal result is available.
- Receipt shape remains `{host, source: native-host, status, agent_id, branch, head, worktree_path, optional summary_path}`. Supported terminal statuses remain complete/completed/stopped. The coordinator must preserve actual host event evidence; a worker-authored summary or `--completed` flag does not establish termination.
- Same-byte receipt replay is idempotent. Contradictory receipt, host identity, summary path, ownership or manifest evidence is rejected. Missing evidence preserves unknown liveness. Validation also binds the receipt HEAD to the current worker HEAD, preventing later commits from borrowing stale termination evidence.
- Real Git regressions cover create/commit source and SUMMARY/record actual host receipt/merge, absent or contradictory receipt and ownership, conflicting replay, manifest drift, stale HEAD and required committed SUMMARY enforcement. Test host receipts are explicit fixtures using identities read from real temporary Git worktrees.
- CR06: the model omit guard now reads the actual surviving rule in `AGENTS.md` Dispatch, which states that resolved inherit means omit the argument. No deleted reference or `.ai` fallback was restored. Model resolution, placeholder binding, omit-on-inherit and spawn-coverage guards remain active.
- CR07: the missing-required-reading diagnostic now directs the agent to `AGENTS.md` and its assigned role instructions. The regression checks that the named owner exists.
- Removed obsolete power-mode and execute-plan embed requirements/assertions. Generic prompt include scanning, workflow budgets, source guards, surviving discussion-mode checks and model guards remain. Generic reference existence fixtures now use surviving model-profiles.md.

## Verification

- `python -m unittest tests.test_native_worker_receipts tests.test_engineer_runtime tests.test_quick_batch -q`: all 18 tests passed in 55.735 seconds.
- After adding manifest-identity drift coverage, `python -m unittest tests.test_native_worker_receipts -q`: all five tests passed in 27.278 seconds.
- `python -m unittest tests.test_model_omit_when_inherit_guard tests.test_workflow_size_budget tests.test_check_contract_drift -q`: 202 tests ran; only two known workflow-owned diagnose-issues binding failures remained, with 14 skips and one expected failure. The deleted-model-reference, obsolete power/embed and diagnostic-owner failures were resolved.
- Final affected guard rerun, `python -m unittest tests.test_workflow_size_budget tests.test_check_contract_drift tests.test_model_omit_when_inherit_guard.ModelReference -q`: all 178 tests passed, with 13 skips and one expected failure.
- `python -m compileall -q engineer/bin/lib tests/test_native_worker_receipts.py tests/test_check_contract_drift.py tests/test_workflow_size_budget.py`: passed.
- `git diff --check`: passed.

## Rows and scope

Corrections address independent-review CR03, CR06 and CR07 and the obsolete feature-specific assertions in the coordinator's 577-test batch at the input revision. No whole files were deleted. Only engineer/bin/lib/, tests/ and this assigned summary changed. No integration, publication or shared planning records were performed.

## Integration dependency

The isolated input still has two legitimate diagnose-issues.md failures: DEBUGGER_MODEL has no bound source, and debugger spawning has no model resolution. The workflow worker owns that correction; these valid guard tests were preserved. The coordinator must rerun the combined batch and independently trace the final workflow/CLI lifecycle after joining both slices. No other material gap remains in this runtime correction.
