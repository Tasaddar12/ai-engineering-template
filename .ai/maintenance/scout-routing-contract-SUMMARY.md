---
status: complete
scope: explicit scout task/output routes and read-only role result contracts
---

## Changes

- Replaced uncertainty and task-size scout heuristics with one authoritative
  task/output table, fixed scout task classes, required assignment inputs and
  requested fields, and a cited `field_results` response.
- Routed extraction, structured summaries, classification, and proposed
  transformations to read-only Scouts; retained implementation, correctness,
  security, diagnosis, documentation verdicts, integration verdicts, and phase
  acceptance with their named owners.
- Added six before/after assignment routes for bug fixes, code plus documentation
  review, coding, feature planning, integration checks, and test execution.
- Defined same-question/revision/scope/input reuse, one missing-field follow-up,
  targeted conflict extraction, and join-before-repair acceptance rules.
- Updated role adapters, shared rules, install entry text, verification triggers,
  reviewer eligibility, planning waves and sizing, read-only concurrency, and
  source-changing versus read-only completion outputs.
- Updated mirrored quick command/skill wording and focused contract tests.

## Validation

- `python -m unittest discover -s tests -p test_efficiency_contracts.py -v` — 7 passed
- `python -m unittest discover -s tests -p test_agent_sources.py -v` — 12 passed
- `python -m unittest discover -s tests -p test_workflow_links.py -v` — 3 passed
- `python -m unittest discover -s tests -p test_unattended_flow.py -v` — 10 passed
- `git diff --check` — passed

No runtime source or runtime tests were changed.
