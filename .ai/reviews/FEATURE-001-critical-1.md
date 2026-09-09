---
subject: FEATURE-001
iteration: 1
status: CHANGES_REQUIRED
base: e3d3208
head: ee8776a31378bf792aad0c1e819a65c4ca656a98
reviewer_session: critical-review-20260908
implementer_session: root-core-20260908
issues:
- id: REVIEW-001
  category: correctness
  files: [src/ai_engineering/artifacts.py]
  issue: Public write_artifact bypasses canonical planning containment and metadata validation.
  required_change: Apply canonical planning location and metadata checks at every public artifact write boundary.
  validation_required: Direct writes of plans, tasks and features outside .ai or with malformed metadata must fail without creating files; valid writes must round-trip.
- id: REVIEW-002
  category: correctness
  files: [src/ai_engineering/artifacts.py]
  issue: ArtifactStore.save can reopen completed, archived or superseded records and remove their historical location.
  required_change: Enforce the historical-state guard in save using the persisted original status before writing or unlinking.
  validation_required: Direct save cannot reopen each historical status and leaves original bytes and path intact.
- id: REVIEW-003
  category: correctness
  files: [src/ai_engineering/artifacts.py]
  issue: Approved decomposed plans are accepted with empty task and feature references.
  required_change: Require nonempty correctly typed task and feature references after approved decomposition while permitting explicit empty lists before decomposition.
  validation_required: Approved plans with either empty list are rejected by create/save/read validation; pre-decomposition plans remain supported.
- id: REVIEW-004
  category: correctness
  files: [src/ai_engineering/state.py]
  issue: Feature review freshness compares two stored heads instead of the observed Git revision.
  required_change: Bind feature review freshness to its observed subject worktree head, including when the review is stored only on the feature.
  validation_required: Feature and review head old with observed head new must report stale feature review in read-only and apply modes without inventing approval or changing intent.
---
# Critical Change Review

## Summary

CHANGES_REQUIRED. The complete eight-file feature diff was inspected for correctness, relevant security and documentation. Four reproduced contract violations block acceptance. Existing core tests, lint, formatting and typing pass. These are ordinary implementation repairs within the existing feature scope; no structural recovery or second review stage is needed.

## Blocking issues

| Category | Location | Exact issue | Required fix |
| --- | --- | --- | --- |
| correctness | artifacts.py:80 | Public artifact writes can put planning outside .ai and skip required metadata | Enforce canonical planning location and metadata at this boundary |
| correctness | artifacts.py:189 | Direct save bypasses the historical transition guard | Validate original versus requested status before mutations |
| correctness | artifacts.py:217 | Approved plans may have empty task/feature graphs | Validate nonempty references once decomposition is approved |
| correctness | state.py:193 | Two stale stored heads conceal stale review evidence after Git changes | Compare review revision with observed subject Git head |

### REVIEW-001 — Public writes bypass the hard planning-location rule

Category: correctness

Files: src/ai_engineering/artifacts.py:80

Issue: write_artifact accepts an arbitrary output path and writes unvalidated metadata directly. A temporary-project probe successfully created docs/PLAN-999.md with only id and status. Therefore the public API bypasses both the user's hard planning-location requirement and the store's required plan/task/feature metadata checks. This is a public boundary in PLAN-002, not a private serialization helper.

Required change: Enforce canonical .ai planning location and required metadata for plans, tasks and features before any write, including direct calls. Reuse validation so store and direct writes cannot diverge; retain generic report/handoff support where intended.

Validation required: Direct writes outside .ai and malformed plan/task/feature writes fail before creating files or directories. A valid canonical direct write remains readable.

### REVIEW-002 — Saving can reopen historical work

Category: correctness

Files: src/ai_engineering/artifacts.py:189

Issue: transition rejects reopening historical records, but save does not compare original.status with the requested status. A probe created a task, completed it, changed the returned object's metadata status to ready, and called save. The completed file was removed and the task became ready. This bypass defeats the promised historical preservation through another supported public method.

Required change: Enforce the same historical-state rule inside save against the persisted original artifact before writing the destination or deleting the old path.

Validation required: Repeat the direct-save probe for completed, archived and superseded artifacts; each attempt fails with original bytes/path preserved. Ordinary active transitions and permitted same-status updates still work.

### REVIEW-003 — Empty approved plans are treated as valid

Category: correctness

Files: src/ai_engineering/artifacts.py:217

Issue: The validator only verifies that tasks/features are lists of strings, and create supplies empty defaults regardless of decomposition status. A probe successfully created an in-progress PLAN-001 with decomposition_status: approved and both lists empty. FEATURE-001 explicitly permits empty lists only before decomposition; the resulting document presents an approved plan without its mandatory task/feature graph.

Required change: Validate the post-decomposition invariant centrally. Approved decomposed plans need nonempty task and feature references of their corresponding ID types. Keep explicit empty lists valid for an undecomposed plan.

Validation required: Reject approved plans with either empty list on create/save and when loading canonical records. Verify undecomposed creation remains valid and populated approved plans round-trip.

### REVIEW-004 — Review freshness is not bound to observed Git state

Category: correctness

Files: src/ai_engineering/state.py:193

Issue: The feature check compares review.head only with feature.metadata.head. Both may be stale after changes in the feature worktree. A probe stored feature.head=old and a PASS review.head=old, with a registered subject worktree whose actual Git head was new. Reconciliation reported only worktree head drift and never stale feature review. The worktree-level review check does not cover the normal case where the review resides on the feature artifact.

Required change: Resolve the feature's registered/observed subject worktree and compare its review revision against Git's actual head. Report stale or unverifiable review evidence as appropriate without rewriting approval or intended state.

Validation required: Reproduce old stored feature/review heads with new observed Git head in both modes; stale review must be explicit, read-only must leave bytes untouched, and apply must preserve intended state/approval. An unchanged reviewed head must remain valid.

## Security findings

Inspected strict YAML parsing, path containment, link/junction rejection, atomic writes, locks and template lookup. No subprocess/provider/network behavior is introduced in this diff. REVIEW-001 concerns the durable artifact boundary as well as correctness. Windows reserved-name/trailing-dot path handling was separately identified by the implementer and is being repaired in the same iteration; its updated implementation must be included in the complete next diff review. The existing symlink-creation test is skipped because this Windows host lacks that privilege.

## Documentation findings

The plan-specific contract is under .ai/plans/active/PLAN-002.md, with explicit task and feature references. Referenced architecture and operating guidance describe the intended boundaries; CLI execution and real Git/provider adapters are later features and are not failures in this bounded slice. No additional documentation blocker was found.

## Validation inspected and limits

- Ran root .venv/Scripts/python.exe -m pytest tests/test_core.py -q in the assigned worktree: 7 passed, 1 skipped.
- Ran the same interpreter with ruff check src/ai_engineering tests: passed.
- Ran ruff format --check src/ai_engineering tests: 37 files already formatted.
- Ran mypy src/ai_engineering: no issues in 6 source files.
- Ran temporary-project Python probes for all four findings; each reproduced as described, with no source/index/branch modifications.
- Inspected the complete diff e3d3208..ee8776a31378bf792aad0c1e819a65c4ca656a98, package metadata, feature/task acceptance, role/review templates and referenced operating/security documentation.
- Initial AGENTS status command using the system Python failed because this feature has no package CLI yet; no CLI acceptance is claimed here.
- Real Git integration, provider execution, external delivery, installation acceptance and other future-feature behavior were not substituted with invented evidence.
