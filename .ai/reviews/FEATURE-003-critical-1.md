---
subject: FEATURE-003
iteration: 1
status: CHANGES_REQUIRED
base: c1a0728
head: cc3ed1b0e25e7d7f8ddf101ff48b980440958288
reviewer_session: critical-review-feature003-20260908-1
implementer_session: native-decomposition-implementation
issues:
- id: REVIEW-001
  category: correctness
  files: [src/ai_engineering/planning.py]
  issue: Default recovery loses explicit incoming feature prerequisites when replacing their dependent feature.
  required_change: Remap and preserve existing feature edges across all replacement feature owners, not only dependencies of fixed features.
  validation_required: An accepted feature-only prerequisite survives replacement, splitting and merging of either endpoint without cycles or self-edges; unaffected completed/active features remain unchanged.
- id: REVIEW-002
  category: correctness
  files: [src/ai_engineering/planning.py]
  issue: Rollback snapshots normalize CRLF to LF and rejected revisions change original artifact bytes.
  required_change: Snapshot and restore original file contents without newline or encoding normalization.
  validation_required: Inject a write failure into a revision whose originals use CRLF and mixed line endings, then assert all original paths and bytes are identical and no new artifact remains.
- id: REVIEW-003
  category: security
  files: [src/ai_engineering/planning.py]
  issue: Case-insensitive overlap comparison is reused for scope authorization, admitting different unauthorized directories on case-sensitive filesystems.
  required_change: Separate conservative ownership conflict matching from filesystem-correct scope authorization checks for tasks, features and recovery.
  validation_required: On a case-sensitive path policy, src/approved must not be authorized by src/Approved, while normal descendants remain accepted and ownership conflict matching stays conservative.
---
# Critical Change Review

## Summary

CHANGES_REQUIRED. Reviewed the complete c1a0728..cc3ed1b0e25e7d7f8ddf101ff48b980440958288 FEATURE-003 diff: planning.py and test_planning.py. Task/feature DAG validation, batching, persistence, revision preparation, lineage and rollback were inspected against TASK-046/047/048 and PLAN-002. Existing validation passes, but three actionable issues block acceptance. These are bounded implementation repairs within the same feature and the same critical review stage.

## Blocking issues

| Category | Location | Exact issue | Required fix |
| --- | --- | --- | --- |
| correctness | planning.py:685 | Existing edges are redirected only for fixed features; replaced consumers lose incoming prerequisites | Preserve/remap edges for every old feature endpoint |
| correctness | planning.py:491 | read_text normalizes CRLF before rollback | Preserve exact original bytes/newlines |
| security | planning.py:74, planning.py:638 | casefold-based ownership comparison authorizes distinct Linux paths | Use separate scope authorization containment |

### REVIEW-001 — Replacing a feature drops its incoming feature-level dependency

Category: correctness

Files: src/ai_engineering/planning.py:685

Issue: Recovery rewrites old dependencies only on proposals[:len(fixed)]. A replaced feature is batched afresh from task edges, so an explicit prerequisite that existed on the old feature but was not duplicated on its tasks disappears. A temporary-project probe created independent TASK-001 and TASK-002 in separate batches, explicitly added FEATURE-002 dependencies: [FEATURE-001], and confirmed validate_features returned no issues. After apply_revision replaced TASK-002 with TASK-003, the approved result was FEATURE-001 unchanged plus FEATURE-003 with dependencies: []. The consumer can now start before its preserved prerequisite.

Required change: Preserve the existing feature graph through replacement mapping for all old endpoints, including incoming prerequisites of newly generated replacement features. Drop only genuine intra-feature self-edges introduced by a merge, and revalidate the complete graph. Keep unaffected completed/active feature records immutable. Deliberate dependency removal needs an explicit justified revision rather than occurring as an accidental side effect of default batching.

Validation required: Retain the exact feature-only-edge reproduction. Cover replacing the consumer, replacing the prerequisite, splitting and merging, and an unchanged completed prerequisite. The revised feature graph must retain the required ordering and remain acyclic.

### REVIEW-002 — A failed revision changes Windows artifact bytes during rollback

Category: correctness

Files: src/ai_engineering/planning.py:491

Issue: previous[path] is captured using read_text, whose universal-newline handling converts CRLF to LF. The exception handler writes this normalized content through atomic_write. In a temporary-project probe, all existing Markdown artifacts were converted to CRLF, then the third write of a replacement revision was forced to raise FrameworkError. The expected failure occurred and paths were restored, but original TASK-001, PLAN-001 and FEATURE-001 bytes changed to LF. This contradicts the rejected-revision preservation guarantee and causes repository changes even though the recovery operation failed.

Required change: Preserve original bytes, or decode without newline translation and restore them equivalently, through the entire snapshot/rollback path. Do not rewrite untouched original content into a different encoding or line-ending form.

Validation required: Extend write-failure coverage to CRLF and mixed-line-ending originals (including a BOM where supported). Assert exact byte equality and path equality for the complete before/after artifact snapshot, plus absence of partially created artifacts.

### REVIEW-003 — Case-insensitive conflict matching must not grant scope authority

Category: security

Files: src/ai_engineering/planning.py:74; src/ai_engineering/planning.py:638

Issue: _path_parts always casefolds path components. That is appropriately conservative for conflict detection, but _covers is also used to authorize feature scope against tasks and recovery scope against the PLAN. On a case-sensitive filesystem, src/Approved and src/approved are different directories. The current platform-independent check accepts a replacement scoped to src/approved/two.py when the PLAN authorizes only src/Approved. A probe confirmed the revision is accepted while PurePosixPath containment correctly says the new path is outside the approved directory. The Windows host cannot demonstrate distinct directories with those names, but the unconditional source logic has the same permissive comparison on Linux.

Required change: Separate conservative conflict overlap from scope authorization. Authorization must respect actual filesystem/path case semantics, or use consistently strict case-sensitive lexical containment, and continue to reject traversal and linked escapes. Apply the corrected authorization helper to both task-to-feature ownership containment and PLAN-to-recovery scope checks.

Validation required: Add case-sensitive-policy tests proving a differently cased sibling cannot expand declared authority, plus valid descendant and sibling-prefix cases. Keep conflict detection conservative so differently cased ownership declarations cannot be scheduled concurrently on Windows.

## Security findings

REVIEW-003 is the blocking scope-boundary issue. Also inspected safe_path use, canonical .ai destinations, provider-metadata serialization preflight, historical overwrite protection, coordinator locking and rollback deletion paths. No subprocess, network, credential or external-delivery behavior is introduced by this feature. Scope expansion remains explicitly prohibited by the plan contract.

## Documentation findings

No additional documentation blocker. Public docstrings describe proposal fields, temporary feature IDs, semantic-versus-deterministic responsibility, and the synchronous rollback/process-crash distinction. Plan-specific contracts remain embedded under .ai/plans/active/PLAN-002.md. The module does not claim deterministic checks prove semantic clarity. Fix the implementation to meet the documented preservation and scope guarantees.

## Validation inspected and limits

- Ran root .venv/Scripts/python.exe -m pytest tests/test_core.py tests/test_planning.py -q in the assigned planning worktree: 37 passed, 1 skipped.
- ruff check src/ai_engineering tests: passed.
- ruff format --check src/ai_engineering tests: 39 files already formatted.
- mypy src/ai_engineering: no issues in 7 source files.
- git diff --check c1a0728..cc3ed1b0e25e7d7f8ddf101ff48b980440958288: passed.
- Independently reproduced feature-edge loss and CRLF rollback mutation in temporary projects without altering repository source or Git state.
- Independently exercised the casefolded authorization path and compared its result with POSIX containment; actual Linux filesystem execution was unavailable.
- The one inherited skip is Windows symlink-creation privilege. No source edits, Git/index mutations, installs or external actions were performed by the reviewer.
