---
phase: maintenance
plan: archive-runtime
subsystem: planning-runtime
tags: [archive, recovery, history, offline]
requires: []
provides:
  - Explicit planning archive previews and journaled apply for phases, ADRs and quick tasks
  - Guarded rollback, historical discovery and active-only counts
  - Planning review/repair CLI registration for the coordinator-owned helper
affects: [planning-maintenance, phase-discovery, runtime-installation]
actuals:
  tokens: 22302
  tasks: 3
  commits: 2
tech-stack:
  added: []
  patterns: [deterministic-preview, exact-byte-recovery-journal]
key-files:
  created: [.ai/runtime/lib/archive.py, tests/test_planning_archive.py]
  modified: [.ai/runtime/phase.py, .ai/runtime/lib/phases.py, .ai/runtime/lib/roadmap.py, .ai/runtime/lib/quick.py, .ai/runtime/lib/bundles.py, .ai/runtime/lib/milestones.py, .ai/runtime/lib/paths.py, .ai/runtime/lib/validate.py, .ai/runtime/README.md, .ai/runtime/TEMPLATE-CONTRACT.md]
key-decisions:
  - Historical phase blocks remain in ROADMAP; active counters exclude archived blocks.
  - Explicit legacy evidence never bypasses active or in-progress guards.
patterns-established:
  - Archive and recovery preview by default; apply requires an explicit flag.
requirements-completed: []
acceptance: []
documentation: [.ai/runtime/README.md, .ai/runtime/TEMPLATE-CONTRACT.md]
coverage:
  - id: ARCHIVE-API
    description: All three archive kinds, deterministic no-write previews, discovery and exact-byte guarded recovery
    verification:
      - kind: integration
        ref: tests/test_planning_archive.py
        status: pass
    human_judgment: false
  - id: ARCHIVE-COMPAT
    description: Historical phase lookup, dependency resolution, active counts, identifier reservation and milestone readiness
    verification:
      - kind: integration
        ref: tests/test_planning_archive.py
        status: pass
      - kind: unit
        ref: tests/test_phase_runtime.py
        status: pass
    human_judgment: false
duration: 14.1min
completed: 2026-10-09
status: complete
plan_head_before: 6e3280a06b680547972fe9def3240f872fb842dd
work_branch: feat/maintenance-archive-slice
review_repair_head_before: b00a0c5116d93dd2f447fcb3acb19c2500bde181
review_repair_branch: feat/maintenance-archive-fixes
review_followup_head_before: 764d6e56d1935ae6f13d449bbfffa908cc2fb9fd
review_followup_actuals:
  tokens: 810
  tasks: 1
  commits: 1
review_repair_actuals:
  tokens: 4390
  tasks: 3
  commits: 1
---

# Phase Maintenance Plan Archive Runtime: Summary

**Explicit planning archival preserves record IDs and references, supports recoverable moves, and separates historical discovery from active progress.**

## Performance

- Implementation started: 2026-10-09T17:26:10.9897814Z (first owned source creation).
- Implementation completed: 2026-10-09T17:40:14.2696882Z.
- Measured implementation interval: 14.1 minutes; initial inspection is outside this measurement.
- Tasks: 3 (archive API/recovery; history consumers; tests/documentation).
- Files: 12 source/test/doc deliverables plus this SUMMARY.
- Context usage: unavailable.
- Estimate-scale actuals: 89,208 characters / 4 = 22,302 tokens in the realized text diff from immutable assigned base to implementation commit. No binary/generated changes. This measurement excludes this metadata SUMMARY and is not host token usage.
- Commit count: one implementation commit plus this final SUMMARY commit; verified final count is returned to the coordinator.

## Accomplishments

- Added `planning.archive <phase|adr|quick> <id-or-path> [--apply] [--evidence PATH] [--replacement PATH]`, `planning.archives [--kind ...]`, and `planning.archive-recover <recovery-id> [--apply]`.
- Dry runs return deterministic moves, rewritten paths and recovery IDs without creating locks/directories. Apply preserves artifacts under `.planning/archive/{phases,decisions,quick}/`, a discovery catalog/index, and exact-byte recovery journals.
- Phase retirement requires checked plans, complete summaries with authored Accomplishments and passed verification. Quick retirement requires authored completion/retirement evidence. ADR archival preserves original reasoning and links the accepted replacement in both directions. Explicit legacy evidence records `archive_kind`, `archive_id`, `archive_status`, and authored `archive_reason` without bypassing active guards.
- Rebases moved/unmoved planning Markdown destinations, reference links, and canonical repository paths. Catalog references follow later ADR archival.
- Recovery preflights original/proposed/intermediate bytes, directory shape, journal checksum and path safety. It refuses subsequent edits, new files/directories, collisions, traversal and symlink/junction escapes. Pending operations remain recoverable and block additional archives; repeated apply/recovery is idempotent.
- Historical phase blocks remain queryable. Active phase/plan counts and STATE progress exclude archived records, dependencies/prior context still resolve, archived IDs stay reserved, and milestone closure retains historical membership/accomplishments.
- Added lazy CLI registration for `planning.review` and `planning.repair --apply --expect ... --only ...` at coordinator request. Their helper module is owned by the planning slice and is integrated by the coordinator.

## Task Commits

1. **Archive runtime, history consumers, fixtures and documentation** - `9f9cc55a0ea2d259a307b378040b6b6dd0e77f2e` (`feat(runtime): archive planning records with guarded recovery`).
2. **Plan metadata** - final SUMMARY commit, reported separately in the worker result.

## Checks

- Tested input: assigned immutable base `6e3280a06b680547972fe9def3240f872fb842dd` plus owned changes committed as `9f9cc55a0ea2d259a307b378040b6b6dd0e77f2e`.
- `python -m unittest discover -s tests -p test_planning_archive.py -v`: final run **29 tests passed**, 24.389 seconds, no skips. Fixtures cover every archive kind, previews, repeat/recovery lifecycle, status/evidence guards, collisions, source/unmoved links, binary/empty-directory interrupted recovery, checksum/edited-file/additional-directory refusal, active counts, dependencies, legacy records, reserved quick/phase IDs and milestone history.
- `python -m unittest discover -s tests -p test_phase_runtime.py -v`: **158 tests passed**, 223.541 seconds. Run covered the implementation before the final bounded milestone-history and missing-plan semantic refinements.
- Final targeted runtime regression using `unittest` classes `Milestones`, `PhaseCrud`, and `PlanProgress`: **19 tests passed**, 13.097 seconds, after those refinements.
- `git diff --check`: passed.
- `python -m py_compile .ai/runtime/lib/archive.py .ai/runtime/phase.py`: passed before the final bounded refinements; all final CLI fixtures import and exercise both modules.
- Windows lacks symlink creation privilege; the final escape fixture exercised an actual Windows junction instead and passed without a skip.

## Files Created/Modified

- `.ai/runtime/lib/archive.py` - selection/evidence gates, rebasing, discovery/indexing, journaled apply and guarded recovery.
- `.ai/runtime/phase.py` - archive and planning helper CLI registration, historical dependency completion, archived mutation guard.
- `.ai/runtime/lib/phases.py`, `roadmap.py`, `bundles.py` - historical lookup, prior context, active counts and ID reservation.
- `.ai/runtime/lib/quick.py` - archived discovery, reserved sequences and explicit obsolete status.
- `.ai/runtime/lib/milestones.py` - milestone historical membership.
- `.ai/runtime/lib/validate.py` - completed archived phases retain requirement traceability.
- `.ai/runtime/lib/paths.py` - structural containment instead of a vulnerable string-prefix containment test.
- `.ai/runtime/README.md`, `TEMPLATE-CONTRACT.md` - actual archive evidence/storage/recovery API contracts.
- `tests/test_planning_archive.py` - offline fixture suite.
- `docs/maintenance/archive-SUMMARY.md` - assigned durable evidence/handoff.

## Decisions Made

Retain historical roadmap blocks rather than deleting/renumbering them. A separate active/history view keeps dependencies resolvable without inflating active progress. Recovery rolls back only guarded bytes and preserves its journal; later changes produce a conflict instead of being overwritten. These choices are within the delegated archive scope and do not establish an adopting project identity.

## Deviations from Plan

- The runtime has no `lib/init.py`; its init consumers live in `lib/bundles.py`. Coordinator confirmed bounded ownership there.
- Coordinator approved a one-line `lib/milestones.py` history membership change after inspection showed archived completed phases otherwise made milestone completion appear empty. The dedicated fixture proves readiness and accomplishment discovery.
- Coordinator requested lazy planning review/repair CLI registration to avoid conflicting edits to the owned registry; helper implementation remains the planning worker's contribution.

## Issues Encountered

The configured default command helper is unavailable on this Windows host before process creation. Supported per-command elevated execution was used as directed; no automatic approval rejection occurred. No credentials/network services were needed.

## Known Stubs

None in the delivered archive API. Stub scan matches were the evidence-placeholder detector and existing todo symbols, not unfinished implementations. The reusable adoption skeleton remains intentionally unfilled and unchanged.

## User Setup Required

None. Existing Python/PyYAML/Git runtime requirements remain sufficient.

## Next Phase Readiness

Ready for coordinator integration and independent review. Exact APIs and the producer/consumer behavior are documented in the runtime README. The planning helper's CLI handlers require the planning worker's module in the combined revision.

## Remaining

- Coordinator must integrate the planning helper module before invoking `planning.review`/`planning.repair`; this branch intentionally has lazy imports rather than duplicating the other worker's implementation.
- Independent code review, documentation verification and combined acceptance remain coordinator-owned; no claim of final verification or publication is made here.
- Archive apply is a journaled multi-file operation, not a crash-atomic transaction. The tested interruption path restores original files through `planning.archive-recover`; conflicting later user edits require reconciliation.
- Source queries support Markdown links/reference definitions and canonical `.planning/...` references. No unrelated parser or external-document editing scope was added.

## Deferred

None.

## Reconciliation proposals

| Operation | Worker supplies | Coordinator reconciles |
|---|---|---|
| Advance position | Archive component complete; planning/updater integration remains external | Maintenance plan boundary only; adopting skeleton remains unfilled |
| Update progress | 29 archive fixtures and 19 final regressions passed | Record component evidence after integration |
| Record metrics | Immutable base, measured 14.1-minute implementation interval, 3 tasks, 22,302 source-diff tokens | Preserve metric scale and final commit count |
| Add decisions | Historical roadmap blocks with active/history views; guarded journal rollback | Maintenance CONTEXT only if required |
| Record session | Source committed; SUMMARY complete; ready for review | Independent review next |
| Update roadmap | No adopting phase/roadmap edits performed | Maintain authorized maintenance records only |
| Complete requirements | No adopting requirement IDs assigned | Do not invent completion IDs |
| Record blockers | No archive implementation blocker; combined helper integration remains | Merge planning module before its CLI checks |

## Self-Check: PASSED

All 12 owned implementation/test/documentation files exist; source commit `9f9cc55a0ea2d259a307b378040b6b6dd0e77f2e` resolves in Git. Assigned root/branch/base guard passed before the implementation commit. Final SUMMARY/root/branch/commit-count verification is recorded in the returned worker result.


## Independent review repairs: CR-02, CR-04 and CR-05

This repair packet applies to `feat/maintenance-archive-fixes`, assigned immutable
base `b00a0c5116d93dd2f447fcb3acb19c2500bde181`. The original implementation packet
above is historical evidence; this section records the current bounded repairs.
Only `.ai/runtime/lib/archive.py`, `tests/test_planning_archive.py`,
`.ai/runtime/README.md` and this SUMMARY changed.

- **CR-02:** Compare the complete directory tree's PLAN inventory with registered
  roadmap IDs before archival. Reject missing/unregistered/noncanonical/nested
  plans and every unsummarized PLAN. Affirmatively incomplete PLAN or SUMMARY
  status rejects archival even when explicit legacy completion evidence is
  supplied. Checked roadmap completion and the original `archive-active` error
  precedence remain required. Fixtures assert both preview and apply leave all
  records unchanged, including active-count discovery of unregistered work.
- **CR-04:** Every guarded ancestor/scanned item checks `lstat` Windows reparse
  attributes, independent of `Path.is_junction`, which is unavailable on Python
  3.11. The Windows regression creates an internal junction, makes
  `Path.is_junction` unavailable, and verifies rejection of the junction and its
  descendants as well as archive preview/apply; its protected target is unchanged.
  Existing external symlink/junction rejection continues to pass.
- **CR-05:** Live selection and catalog matching share one alias matcher. Repeated
  ADR numeric, prefixed-number, stem, filename and original-path selectors return
  `already_archived` with the same recovery ID and no writes for preview/apply.
  Ambiguous historical numbers and active/archive identity collisions still fail.
- Corrected README wording to “completion value plus authored Verification”; no
  unrelated timestamp-format validation was added. A fixture accepts a substantive
  non-timestamp completion value with authored verification.

### Repair checks

- `python -m unittest discover -s tests -p test_planning_archive.py -v`:
  **40 tests passed**, 39.211 seconds, no skips, against the final repair source.
  Eleven new regressions cover the reviewed gaps and documentation boundary.
- Bounded existing `test_phase_runtime` classes `PlanProgress` and `QuickTasks`:
  **8 tests passed**, 6.069 seconds; runtime phase completion and quick creation/update behavior
  remains intact. The full 158-test suite was not repeated for this bounded repair.
- `git diff --check`: passed.
- The initial repair fixture run found one `archive-active` precedence regression;
  it was corrected before the final all-pass run. No failure remains.
- Python 3.11 was not separately installed/executed. Its missing junction API is
  simulated against a real Windows junction, as assigned; the implementation uses
  the existing `lstat` reparse attribute available without that API.

### Repair self-check and remaining

All four owned repair paths exist. Assigned root, branch and base guards passed
before writes; root/branch/base ancestry is checked again before the repair commit.
Repair estimate-scale actuals are 17,562 text-diff characters / 4 = 4,390 tokens
from the assigned repair base across the three source/test/documentation paths,
excluding this SUMMARY; no binary/generated files changed.
One meaningful source/docs/tests/SUMMARY repair commit is returned to the
coordinator, who owns integration and independent re-review. No new network,
authentication or operational-store surface was added. Stub scanning found no
unfinished implementation; the adoption skeleton remains untouched.

No repair implementation blocker remains. Independent re-review and combined
verification remain coordinator-owned. Repair duration was not separately
measured; the test elapsed times above are actual command results.


## Re-review follow-up: PLAN suffix case variants

Continued the same owned repair checkout from immutable input
`764d6e56d1935ae6f13d449bbfffa908cc2fb9fd` on
`feat/maintenance-archive-fixes`. Physical PLAN discovery now checks
`name.lower().endswith('-plan.md')`, after which the existing canonical filename
matcher rejects noncanonical casing. This prevents unfinished
`01-02-PLAN.MD` work from disappearing into an archived directory.

Added a platform-independent fixture for that exact extra filename. Its matrix
checks preview and apply, each with and without valid legacy evidence; every
rejection preserves all bytes, the PLAN file and active discovery counts. No
Windows-specific API is required by this fixture.

README now qualifies the modern SUMMARY/Accomplishments/passed-VERIFICATION proof
with “Without valid legacy evidence”. The unconditional missing/unregistered/
unsummarized/affirmatively-incomplete work guards remain documented immediately
before that qualification and are unchanged.

- `python -m unittest discover -s tests -p test_planning_archive.py -v`:
  **41 tests passed**, 39.869 seconds, no skips, against the final follow-up source.
- `git diff --check`: passed.
- Follow-up estimate-scale actuals: 3,240 text-diff characters / 4 = 810 tokens
  across archive source, focused test and runtime README, excluding this SUMMARY;
  no binary/generated files changed. These are separate from the first repair's
  recorded actuals.
- All four owned paths exist; assigned root/branch/input guard passed before
  writes. The commit/root/base ancestry is guarded again at delivery.
- No new blocker or unfinished implementation remains. Coordinator owns
  integration and independent re-review. This continuation adds one meaningful
  source/test/docs/SUMMARY commit, bringing the repair branch to two commits from
  its original assigned repair base.
