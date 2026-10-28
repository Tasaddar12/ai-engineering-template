---
phase: maintenance-python-scripts
plan: runtime
status: in_progress
requirements-completed: []
acceptance: []
documentation: []
issue_refs: []
plan_head_before: 7723b2d1ce2b0d698613639547c35e2b98688a70
---

# Python runtime and script maintenance summary

The installed runtime now invokes the tested review-depth and UI probe algorithms,
normalizes native Fallow reports, exposes isolated maintenance helper commands,
and validates script and hook entrypoints on draft pull requests.

## Accomplishments

- `review.depth` consumes canonical `paths` arrays and selects the strongest
  matching directory rule through `code_review_depth.resolve_code_review_depth`.
- `spec.ui-probe` uses the tested UI taxonomy, exposes proposal and conservative
  auto modes, and keeps behavior verification false. `spec.ui` remains compatible.
- `spec.section` retains authored items and adds canonical section status fields.
- `review.normalize-fallow` accepts native reports and preserves normalized findings.
- `engineer/bin/helper.py` runs explicitly whitelisted Python helpers from any
  working directory, including a relocated installed copy.
- `scripts/SCRIPT.py` discovers and dispatches the existing maintenance scripts.
- CI installs both runtimes' dependencies, exercises the new CLI tests, retains
  all legacy tests/hooks and runs on draft pull requests.

## Checks

- `python -m unittest discover -s tests -p 'test_python_*.py' -v`: 14 passed.
- `python -m unittest discover -s tests -p test_engineer*.py -v`: 15 passed,
  including installed namespace identity, record lifecycle, worktree boundaries,
  merge authorization, repair freshness; one POSIX shell test skipped on Windows.
- `python -m unittest discover -s tests -p test_unattended_flow.py -v`: 10 passed.

## Decisions and deviations

The typed review-depth resolver already existed but its registered CLI used a
different override shape and first-match glob rules. The CLI now shares the
tested implementation. No new dependency was introduced.

## Remaining

Manager/pipeline/idea subprocess flows and final targeted regression checks are
pending in the next slice. Full-suite integration remains coordinator-owned.
No planning records or legacy files were changed.

## Threat outcomes

No new threat identified in the inspected helper, script and adapter surface.
Helper names are explicitly whitelisted. Existing input containment and explicit
output-file checks remain enforced; hook tests operate in disposable repositories.

## Self-Check: PASSED

All source and test files named above exist. The slice commit is recorded in Git;
the coordinator receives its exact hash in the worker handoff.
