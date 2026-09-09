---
subject: FEATURE-001
iteration: 2
status: CHANGES_REQUIRED
base: e3d3208
head: d4f36adec85435ce7bc21a7fbe9a88471d8497dc
reviewer_session: critical-review-20260908-2
implementer_session: root-core-20260908
issues:
- id: REVIEW-003
  category: correctness
  files: [src/ai_engineering/artifacts.py]
  issue: The post-decomposition check ignores decomposition_status approved, allowing approved ready plans with empty task and feature references.
  required_change: Treat explicit approved decomposition as requiring nonempty task and feature references regardless of plan execution status or presence of a decomposition path.
  validation_required: Ready approved plans with either empty list must fail; undecomposed ready plans and populated approved plans must still work.
- id: REVIEW-004
  category: correctness
  files: [src/ai_engineering/state.py]
  issue: Review freshness still misses Git changes when worktree ownership is recorded by subject in STATE but not duplicated on the feature metadata.
  required_change: Resolve observed worktree HEAD from authoritative STATE worktree subject ownership as well as a feature worktree reference; do not silently fall back to matching stale heads when known evidence is unavailable.
  validation_required: The registered-subject-only reproduction must report stale review in read-only and apply modes while preserving intent and approval evidence.
---
# Critical Change Review

## Summary

CHANGES_REQUIRED. Reviewed the complete updated feature diff e3d3208..d4f36adec85435ce7bc21a7fbe9a88471d8497dc, including all six Python modules, all core tests and packaging configuration. Iteration-1 REVIEW-001 and REVIEW-002 are repaired. REVIEW-003 and REVIEW-004 remain partially unresolved in reproduced cases. These remain ordinary fixes in the same feature and review stage.

## Blocking issues

| Category | Location | Exact issue | Required fix |
| --- | --- | --- | --- |
| correctness | artifacts.py:245 | Explicit approval without a decomposition path bypasses the nonempty-plan invariant | Include decomposition_status: approved in centralized validation |
| correctness | state.py:195 | Freshness ignores worktree ownership stored solely in STATE.worktrees.subject | Resolve the observed Git head using registered subject ownership |

### REVIEW-003 — Explicitly approved ready plans can still be empty

Category: correctness

Files: src/ai_engineering/artifacts.py:245

Issue: The new condition checks decomposition and in-progress/completed, but ignores decomposition_status, the explicit approval field used by the current plan. The call store.create('plans', 'PLAN-001', 'Approved plan', 'ready', decomposition_status='approved') still succeeds with tasks: [] and features: []. This is already approved decomposition even though execution has not started, so it violates the stated empty-lists-only-before-decomposition contract.

Required change: Centrally require nonempty task and feature references when decomposition_status is approved, as well as for the other executing/decomposed indicators. Keep legitimate pre-decomposition ready documents supported. References should use the corresponding TASK/FEATURE ID forms described by the contract.

Validation required: Cover approved ready plans without a decomposition path, each empty list independently, a populated approved plan, and an undecomposed ready plan. Confirm failed saves leave original files unchanged.

### REVIEW-004 — Registered subject ownership does not invalidate stale review

Category: correctness

Files: src/ai_engineering/state.py:195

Issue: The repair consults Git only when feature.metadata.worktree exists. The authoritative current-state worktree index also identifies the owning subject. In the original probe, feature.head and feature.review.head are old, STATE.worktrees contains path .worktrees/feature and subject FEATURE-001, and Git reports new for that path. With no redundant worktree field on the feature, both reconciliation modes still return only Worktree head differs; stale feature review is absent. The check again compares two stale metadata values despite an available Git observation for the feature.

Required change: Resolve a feature's observed worktree through registered STATE subject ownership as well as its optional artifact worktree field. When known worktree evidence is missing or conflicting, surface that review cannot be verified instead of treating equal stored heads as current. Do not invent approval, delete work, or overwrite intent.

Validation required: Preserve the registered-subject-only case exactly. Both read-only and apply must report stale feature review for new Git head; unchanged Git head must not. Check read-only bytes are unchanged and apply retains worktree intent/review evidence. Cover missing observations for a known active reviewed feature.

## Security findings

Rechecked strict YAML parsing, canonical planning writes, historical immutability, portable component validation, link/junction guards, template-root containment, atomic replacement and coordinator locking. The added Windows reserved-name/trailing-dot/space checks address the previously identified cases. No additional blocking security issue found in this diff. This code adds no subprocess, network, credential or provider execution. Symlink creation remains unavailable on this Windows host; the corresponding test skips openly.

## Documentation findings

Planning remains under .ai and the revised canonical write boundary enforces that location. Referenced architecture remains consistent with the bounded feature scope. No separate documentation blocker found. A minor encoding regression was noted to the implementer: the default artifact heading's em dash became mojibake, and the Unicode test fixture Cafe-accent text was similarly altered. Restore the intended UTF-8 strings during repair.

## Validation inspected and limits

- Root .venv/Scripts/python.exe -m pytest tests/test_core.py -q in assigned worktree: 13 passed, 1 skipped.
- ruff check src/ai_engineering tests: passed.
- ruff format --check src/ai_engineering tests: 37 files already formatted.
- mypy src/ai_engineering: no issues in 6 source files.
- Independent temporary-project probes reproduced both remaining findings. Read-only reconciliation preserved STATE bytes; apply preserved worktree intent but still omitted stale-review evidence.
- Inspected all files in the complete feature diff, not only previous-review repairs. Package discovery now includes asset namespaces; runtime CLI/real Git/provider/integration acceptance remains assigned to later features.
- No source edits, Git/index mutations, installs or external actions performed. This report is immutable; subsequent repairs require a new report bound to their complete updated head.
