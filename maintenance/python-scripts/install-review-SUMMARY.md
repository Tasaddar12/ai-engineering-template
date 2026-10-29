---
phase: template-maintenance
plan: python-scripts-install-review
status: complete
subsystem: installation
tags: [python, migration, preservation, regression]
requirements-completed: []
acceptance: []
documentation: []
issue_refs: []
plan_head_before: "f383757251565b869495a71fdffec9b1c0a24dd5"
---

# Python migration review corrections

Reviewed migration preserves undecodable custom text bytes, isolates the old
runtime and hooks from the active engine, and supports pinned updates after
migration while retaining all original legacy source files.

## Assignment

Coordinator-authorized correction of review finding CR-02 plus full legacy-tree
migration validation. Assigned root:
`D:/Codex Projects/ai-engineering-template/.worktrees/scripts-install-review-200320946`.
Assigned branch: `phase-scripts-install-review-200320946`. Immutable input:
`f383757251565b869495a71fdffec9b1c0a24dd5`.
Only `bin/install_support.py`, `tests/test_install_scripts.py`, and this summary
are changed. No adopting-project records, legacy source deletions, pushes or
merges are part of this worker's assignment.

## Outcomes

- CR-02: `.md`, `.txt`, `.json` and other text-like legacy files whose bytes are
  not UTF-8 are copied without decoding or replacement. Their reviewed entries
  explicitly record `text_transform: no-text-transform` and
  `text_transform_reason: non-utf8-bytes`. Regeneration validates this metadata
  along with the byte hashes before applying. The original and transaction
  backup retain the exact source bytes; rollback removes newly copied files.
- Complete older runtimes map to `.HOST/legacy/runtime` and their hooks map to
  `.HOST/legacy/hooks`, preserving the sibling imports used by those hooks.
  Their `lib` modules cannot contaminate `.HOST/engineer/bin/lib`.
- `--select-all` explicitly selects all paths in the exact reviewed plan and is
  mutually exclusive with `--select`. The review hash and explicit conflict
  resolution are still mandatory. This avoids Windows command-line limits for
  full-tree migration using hundreds of repeated `--select` arguments.
- The ownership manifest records the reviewed original legacy-file snapshots
  and whether all legacy mappings were selected and applied/backed up. A later
  pinned update is allowed while the retained originals match that reviewed
  snapshot. Changed/new real legacy files still require migration review.
- Python `__pycache__`, `.pyc` and `.pyo` artifacts are excluded consistently
  from migration mappings and snapshot comparisons. Running a retained legacy
  hook cannot invalidate the review just by generating bytecode. Original
  artifacts remain untouched.
- Existing migration metadata survives ordinary update manifest rewrites.
- An already migrated legacy copy whose bytes and mode match the reviewed
  destination is classified as unchanged. Re-review does not manufacture a
  customization conflict for identical copies; real differences still require
  an explicit conflict resolution.

## Checks

- Targeted undecodable-byte regression: passed for Claude and Codex, including
  three text-like extensions, selected apply, original/backup equality and
  explicit rollback.
- Targeted full-tree regression: one test passed in 73.948 seconds, exercising
  both hosts with all 280 tracked source `.ai` files, selected full migration,
  active and legacy runtimes, mapped and retained hooks, generated-cache
  tolerance, pinned installed-CLI update, metadata retention and later-source
  drift refusal.
- Two direct export-transform behavior tests passed in 4.497 seconds: CRLF and
  non-shell/unknown-JavaScript preservation, recognized probe conversion, and
  execution of a generated Python JSON-reader command.
- `python -m py_compile bin/install_support.py tests/test_install_scripts.py`
  and `git diff --check`: passed.
- `python -m unittest discover -s tests -p test_install_scripts.py -v`: **12
  tests passed in 186.998 seconds** on Python 3.13 / Windows. This includes all
  prior installer regressions and the new migration/export-transform coverage.
- Subsequent targeted full-tree rerun with the final unchanged-copy assertion:
  **one test passed in 72.921 seconds**, exercising both hosts after the final
  source change.
- `python -I bin/migrate.py --help` exposes mutually exclusive `--select` and
  `--select-all` alongside the reviewed-plan SHA-256 option.

## Deviations and remaining work

Full-tree testing exposed two defects beyond the original undecodable-text
review finding: legacy runtime module collisions and perpetual migration
refusal caused by intentionally retained original source. Both are corrected
in this owned installer slice, with regression coverage.

The preserved legacy runtime retains its existing PyYAML dependency and its
normal Python invocation. It is not advertised as the new isolated stdlib
runtime. The active new engine is exercised with `python -I`.

POSIX mode behavior was not executed on this Windows worker. No legacy installer
suite repeats were performed. The coordinator owns combined validation, native
host checks, documentation integration and publication.

## Security and stubs

This correction preserves the existing trust boundary: only selected reviewed
paths are written, unresolved custom conflicts refuse replacement, and exact
backups precede writes. No new endpoint or authentication surface is added.
There are no placeholder implementations or known stubs in this slice.

## Reconciliation

No planning-state, roadmap, project-decision or requirement changes are proposed.
Integrate this commit, reconcile the documented legacy layout and selection
flag, rerun combined checks, and attach the evidence to the tracking PR.

Context usage: unavailable.

## Self-Check: PASSED

The assigned root/branch and immutable base were verified; all changed paths
are owned by the assignment. The complete 12-case focused suite passed, and
the final source adjustment passed the targeted full-tree flow on both hosts.
Changed Python files compile and the diff passes whitespace checks. This
summary is committed with the implementation, and the resulting commit hash is
returned to the coordinator after Git confirms it. No legacy source is deleted.
