# PR 171 health dispatch boundary follow-up

- Status: complete
- Root: `C:/Users/killi/.codex/worktrees/pr171-runtime-comments/ai-engineering-template`
- Branch: `review-pr171-runtime`
- Input revision: `07d12cf9503de60a200a8772483d1f379eb01fa7`

## Changes

The validate.health dispatcher alone bypasses the before/after planning integrity snapshots: those snapshots hash config.yaml bytes and cannot run when the diagnostic's subject is unreadable. Every other verb retains the same capture/finish enforcement. The health function and general integrity/digest contracts are unchanged.

The subprocess read-denial regression now denies both read_text and read_bytes for config.yaml, reproducing the snapshot failure before repair. It requires the normal structured broken/config-unreadable health packet and compares all fixture file bytes before and after. A separate subprocess injects an actual record write into a read-only verb and an allowed mutating verb: state.get is rejected as unexpected-planning-write while state.patch remains accepted. Existing planning-integrity tests cover guarded mutations and introduced malformed records.

## Checks

- Stronger read-denial regression failed before correction with generic invalid-input and exit 2, confirming the independent review finding.
- `python -m unittest discover -s tests -p test_retained_runtime.py`: 9 passed.
- `python -m unittest discover -s tests -p test_planning_integrity.py`: 51 passed.
- `python -m unittest discover -s tests -p test_health_diagnostic.py`: 133 passed.
- `python -m unittest discover -s tests -p test_engineer_runtime.py`: 9 passed.
- Total: 202 passing tests, no skips.
- `python -m compileall -q engineer/bin/engineer.py tests/test_retained_runtime.py`: passed.
- `git diff --check`: passed.

## Deviations

None. Source edits affect only the explicitly authorized validate.health dispatch boundary. Health's no-mutation behavior is verified by subprocess regressions instead of snapshots that cannot read denied files. No previous summary, schema or other source was changed.

## Remaining

No runtime blocker. Coordinator owns integration and independent review. No push, merge, branch switch or children.
