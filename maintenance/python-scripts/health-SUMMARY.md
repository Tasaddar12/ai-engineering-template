---
status: complete
acceptance: []
documentation:
  - engineer/bin/lib/health_snapshot.py
  - engineer/bin/lib/health_diagnostic.py
  - engineer/bin/lib/health_diagnostic_rules.py
plan_head_before: 5b12b06199168f9975fea4d53e965fdf7640a89c
---

# Native repository health runtime

`validate.health` now evaluates actual native planning and Git evidence instead
of returning a structural-only file inventory.

## Changes

- Added a standard-library snapshot reader for native `config.yaml`, project,
  requirements, state, numeric roadmap phases, phase plans/summaries/verification,
  research validation, milestone archives and Git worktree/ignore/tracking facts.
  Planning reads reject paths resolving outside the inspected repository.
- Preserved `status`, `errors`, `warnings`, `info` and `counts`; added diagnostics,
  truthful evaluated/skipped coverage, evidence gaps, `repairable_count`, and
  `repairs_performed`/`repairs` results. Unfilled adoption skeletons are explicitly
  informational and never adopted as approved project identity.
- Kept pure upstream-shaped evaluator and repair API compatibility. Native CLI
  only repairs W008 through the existing locked, comment-preserving YAML config
  handler, then rebuilds the snapshot and reports remaining findings. Unsupported
  and destructive actions receive explicit refusal details; no native CLI path
  creates config.json, regenerates state, rewrites verification or backfills records.
- Updated the evaluator and rules module opening documentation to describe the
  native snapshot builder; rules functions and the separately owned W019 registry
  were left untouched.
- Made planning-integrity classification argument-aware: only explicit
  `validate.health --repair` can mutate. Default health and `--backfill` retain
  immutable-byte checks. Health alone tolerates unreadable records as sanitized
  evidence gaps; repair refuses incomplete/unreadable before-state fingerprints.
  Other verbs retain their original strict capture path. The home guard runs
  before health bootstrap reads planning content.
- Added actual CLI fixtures using disposable Git repositories, without network,
  paid hosts or writes to this checkout's real planning records.

## Checks

- `python -m unittest discover -s tests -p test_health_runtime.py -q`: 18 passed.
  Exercises fresh/unonboarded/healthy repositories, malformed YAML/native schema,
  missing project sections, invalid UTF-8 plans, phase mismatch/naming/disk drift,
  orphan summary/unexecuted plan, research/completion advisories, real Git ignore
  and tracked-file evidence, absent Git evidence, home guard, default byte
  immutability, safe explicit YAML repair/recheck, unsafe repair/backfill refusal,
  narrow mutation classification and sanitized native validation errors.
- `python -m unittest discover -s tests -p test_health_diagnostic.py -q`: 133 passed.
- `python -m unittest discover -s tests -p test_planning_integrity.py -q`: 51 passed.
- `git diff --check`: passed before final staging.

## Evaluated coverage and limits

For a readable numeric native fixture with working Git, evaluated table codes:
E002, E003, E004, W001, W002, W011, W021, W026, W003, E005, W004, W008,
W012, W013, W014, W015, W022, W029, W005, W023, I001, W009, W030, W006,
W007, W020, W017, W027, W018, W019 (30 of 34 catalog rules). Native health also
evaluates C001–C004 consistency advisories and the E001/E010/I010 safety prechecks.
The catalog is not a claim that all 37 codes are executed against usable evidence.

Explicit static skips:

- W010: upstream GSD agent installation has a different contract from native hosts.
- W016: `workflow.ai_integration_phase` is not accepted by native config.yaml.
- W024: the upstream rule is inert and has no snapshot freshness probe.
- W028: the native runtime has no install-shadow renderer.

Unavailable Git additionally skips W017/W027/W029 with reasons, records a Git
evidence gap and emits W020. Native snapshot parsing supports numeric phase
headings; unsupported custom/bracket conventions explicitly skip their dependent
phase rules. Missing/unreadable evidence is returned separately from static
inapplicability. `coverage.complete` remains false whenever a rule is skipped or
evidence is unavailable; `structuralOnly: false` means actual rules execute, not
that semantic project outcomes or external host installation are verified.

## Deviations

The actual CLI immutability guard initially rejected a successful explicit native
config repair. Coordinator expanded exact ownership to `engineer/bin/engineer.py`
and `engineer/bin/lib/planning_integrity.py`; the guarded argument-aware repair
classification and health-only unreadable-evidence capture close that integration
gap. This is native adaptation, not a relaxation for other commands.

## Remaining

No required owned implementation remains. Workflow/generated catalog prose is
owned by the documentation worker. Upstream-only/inert rules and unsupported
automatic native repairs remain explicitly reported limits rather than silent
passes. No planning records, branch switches, merges or publications performed.

## Self-Check: PASSED

Owned implementation and test files exist; checks above executed successfully.
The coordinator owns integration and publication of this committed slice.
