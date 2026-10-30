# PR 171 structured health diagnostics follow-up

- Status: complete
- Root: `C:/Users/killi/.codex/worktrees/pr171-runtime-comments/ai-engineering-template`
- Branch: `review-pr171-runtime`
- Input revision: `a43894fefaf95f132e97cd5cbb2f04c6b2478221`

## Changes

Health now skips loading a missing config.yaml and catches filesystem errors while checking or loading an existing config as a config-unreadable finding with path and message. The normal broken health packet remains available, including counts and structuralOnly, without mutation or automatic repair. Actual configuration validation Failure codes remain intact.

Reproduction refined the initial report: a real validate.health subprocess after unlinking config.yaml already returned structured missing-record diagnostics, because core.read defaults missing content and config loading supplies defaults. Malformed YAML already returned invalid-yaml in the health errors. A deterministic PermissionError at the actual config read reproduced the gap: the CLI returned generic invalid-input/exit 2 instead of health diagnostics. The correction preserves missing/malformed behavior and makes that inaccessible-config case structured.

## Checks

- Before correction, config-read-denial subprocess regression failed with exit 2 and generic invalid-input as expected.
- `python -m unittest discover -s tests -p test_retained_runtime.py`: 8 passed, including real missing/malformed config subprocesses, filesystem-read denial seam and no-mutation checks.
- `python -m unittest discover -s tests -p test_health_diagnostic.py`: 133 passed.
- Total: 141 passing tests, no skips.
- `python -m compileall -q engineer/bin/lib/workflow_ops.py tests/test_retained_runtime.py`: passed.
- `git diff --check`: passed.

## Deviations

Reproduction found the missing-file premise was already handled; the actual runtime correction targets inaccessible config reads and avoids the redundant missing-file load. Source change is confined to _health. No schema or sub-repository setting was added, and no previous summary was edited.

## Remaining

No runtime blocker. Coordinator owns integration and independent review. Health reports remain read-only; documentation owns removal of unsupported auto-repair claims. No push, merge, branch switch or children.
