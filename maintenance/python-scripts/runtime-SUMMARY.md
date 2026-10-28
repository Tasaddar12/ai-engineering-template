---
phase: maintenance-python-scripts
plan: runtime
status: complete
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
- Runtime JSON uses UTF-8 even on Windows. A relocated non-ASCII namespace is
  exercised; the shared test CLI decoder now explicitly matches that contract.
- New state documents and generated schema use the established
  `workflow_state_version` key. Existing `engineer_state_version` and
  `gsd_state_version` metadata survive state updates without forced renaming.
- State/health generators emit actual Python helper names. State generation
  accepts the old exact marker for a safe regeneration transition.
- Real CLI subprocess tests cover idea capture/update/idempotent promotion,
  pipeline queue reuse, dependency validation, cancellation, host restrictions,
  and manager recommendations/discussion/authorization gates.

## Checks

- New suites: `test_python_runtime.py` 10 passed, `test_python_hooks.py` 3 passed,
  `test_python_scripts.py` 5 passed (18 tests total across final targeted runs).
- `python -m unittest discover -s tests -p test_engineer*.py -v`: 15 passed,
  including installed namespace identity, record lifecycle, worktree boundaries,
  merge authorization, repair freshness; one POSIX shell test skipped on Windows.
- `python -m unittest discover -s tests -p test_unattended_flow.py -v`: 10 passed.
- Focused regression suites passed: code_review_depth 55, ui_consideration_probe
  46, fallow_runner 38, state_md_schema 13, spec_probes 2.
- Generator suites: gen_health_docs 30 tests (one expected failure for unmerged
  shipped docs); gen_state_md_docs 41 tests (one expected failure for unmerged
  shipped docs). Fixture write/check round trips passed.
- `helper.py lint-health-diagnostic-rule-table`: passed fixture proof for 34 rule
  codes, with the existing W024 exemption and absent S0NN source skip reported.
- `git diff --check`: passed.

## Decisions and deviations

The typed review-depth resolver already existed but its registered CLI used a
different override shape and first-match glob rules. The CLI now shares the
tested implementation. No new dependency was introduced.

## Remaining

Coordinator/doc worker must regenerate `engineer/workflows/health.md` and
`engineer/templates/state.md` using the corrected generators, pass actual
`--check`, then remove the expected-failure decorators on their shipped-doc
checks. Response-language lint detects a removed shared reference; the doc worker
owns its import/directive correction. Three real unknown verb uses in active docs
(`milestone.release-tags`, `progress`, `websearch`) were sent to that worker;
validator false positives for built-ins and `VERB` placeholders are corrected.
Full-suite integration remains coordinator-owned. No external Claude/Codex host
execution was attempted; pipeline orchestration checks exercise durable queue and
authority boundaries through real subprocess CLIs. No planning or legacy file
was changed.

## Threat outcomes

No new threat identified in the inspected helper, script and adapter surface.
Helper names are explicitly whitelisted. Existing input containment and explicit
output-file checks remain enforced; hook tests operate in disposable repositories.

## Self-Check: PASSED

All source and test files named above exist. The slice commit is recorded in Git;
the coordinator receives its exact hash in the worker handoff.
