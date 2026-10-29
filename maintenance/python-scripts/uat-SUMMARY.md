---
phase: maintenance-python-scripts
plan: uat
status: complete
requirements-completed: []
acceptance: []
documentation: []
issue_refs: []
plan_head_before: 5b12b06199168f9975fea4d53e965fdf7640a89c
---

# Python tooling: UAT provenance and Windows ledger summary

## Why

UAT acceptance ignored structured gap resolutions, while both canonical artifact registries omitted the JSON ledger produced by quality.py.

## Changes

- UAT parses structured `## Gaps` YAML and validates resolved gaps using a nonempty gap_id, ISO resolved_at, resolving PLAN basename, same-phase regular PLAN and matching SUMMARY files, and PLAN gap_ids naming the gap. This preserves engineer/workflows/verify-work.md:540 and engineer/templates/UAT.md:125-130.
- Historical issue/failed tests become effectively resolved only when every linked gap validates. Pending, blocked, unproven resolved results, orphan failed gaps, malformed gaps and later regressions remain blockers. Audit commands share the same disposition.
- Canonical artifact and W019 registries recognize active windows.json and retain legacy WINDOWS.md. Registry equivalence and recognition are tested.

## Checks

- `python -m unittest discover -s tests -p test_uat*.py`: 15 tests passed with one symlink test skipped because this Windows host cannot create symlinks.
- `python -m unittest discover -s tests -p test_artifacts.py`: 12 tests passed.
- `python -m unittest discover -s tests -p test_health_diagnostic.py`: 134 tests passed.
- CLI fixtures cover valid dates/timestamps, missing and nonregular evidence, mismatched/absent plan gap_ids, traversal/absolute/ADS paths, invalid fields, unresolved regression, malformed YAML, baseline pass/pending and required human verification.
- Owned changes scanned for TODO/FIXME/placeholder stubs; none introduced.

## Deviations

No new gap_closure flag, approval receipt, or summary schema requirement was introduced. The existing contract requires matching summary existence and plan gap_ids membership.

## Remaining

The host disallows creation of filesystem symlinks, so the real symlink CLI fixture was skipped. Same-phase directories masquerading as PLAN/SUMMARY files and invalid path forms were exercised; source explicitly rejects symlinks. Coordinator owns integration, documentation, broader verification and publication. No real planning records were modified.

## Reconciliation

Both assigned implementation tasks are delivered; no adopting-project decisions, requirement completion, or planning status changes are proposed. Resume with integration of owned commits and final read-only verification. This maintenance assignment carried no token/duration estimate.

## Self-Check: PASSED

Assigned files and this SUMMARY exist. Root and branch match the assignment; source-changing slice commits are returned separately to the coordinator after commit verification.
