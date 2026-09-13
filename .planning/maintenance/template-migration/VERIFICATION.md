# Template and planning migration verification

## Outcome

Independent review passed for the integrated migration at `55f944c`, with a
passed reference/naming addendum at `0459dbb`. The original findings remain in
[REVIEW-01](REVIEW-01.md). Final delivery also requires passing checks on the
actual PR head; this record is not a substitute for the remote check results.

## Acceptance and evidence

| Required outcome | Evidence |
|---|---|
| Complete templates, including examples and consumers | All 40 templates and 447 support files reconstruct their exact original source hashes after reversing enumerated adaptations |
| Consistent local references | Ten library tests pass at `0459dbb`, including real Markdown links, source fragments and workflow-step file references; regeneration checks 493 outputs with zero differences |
| Project planning separate from tooling | Project records, configuration, phases, codebase maps, specifications and decisions live in `.planning`; runtime and entry-point navigation checks cover the relocated paths |
| Full artifacts work in execution | Real Git/process fixtures exercise full plans, summaries, verification, UAT and authored STATE preservation, plus native TDD feature plans and optional summary variants |
| Safeguards preserved | Tests cover ownership, declared deletions, shared-file serialization, prerequisite integration, immutable roadmap, interrupted live workers, stale inputs, verifier mutation and publication gates |
| Local template depth | Independent review confirmed ADR and CURRENT-SPEC purpose, consumers, complete artifact blocks, instructions, good/bad examples and handoffs |
| Accurate human documentation | Workflow, onboarding, features, template guide and proposed workflow direction distinguish working behavior from future extensions; portable navigation passes |
| Neutral working vocabulary | Active body/filename checks pass; legal attribution and exact source identity stay in dedicated provenance/history records |

## Completed checks

| Check | Revision / result |
|---|---|
| Full local Python suite | `55f944c`: 72 tests passed in 513.429 seconds; runtime code is unchanged through `0459dbb` |
| Independent focused re-review | `55f944c`: 16 tests passed in 39.835 seconds, plus independent roadmap experiment and canonical regeneration |
| Independent reference/naming addendum | `0459dbb`: all 10 library tests and active navigation passed; no new blocker |
| Worktree advisory hook | 49 checks passed locally |
| Ownership advisory hook | 10 checks passed locally |
| Linux CI | `0459dbb`: full suite passed |
| Windows CI | `0459dbb`: 72 of 73 tests passed; event-reader sharing race described below prevented readiness |

## Windows event-reader correction

The hosted Windows run failed opening a fixture event YAML file while a live
worker atomically replaced it. The full local Windows run passed, and CI reached
the event-polling helper rather than a failed runtime assertion. The fixture
already writes a complete temporary file before replacement.

The test reader now retries only `PermissionError` for at most 40 attempts with
25 ms spacing. It still raises persistent access errors and does not suppress
malformed data or runtime assertions. Regression cases inject one transient
sharing error and a persistent error. The real interrupted-worker tests remain
required alongside both platform suites on the final PR revision.

The corrected fixture passed four focused tests in 19.723 seconds: both injected
sharing-error cases, live-worker resume refusal, and recovery after a lost PID
checkpoint. Portable workflow navigation also passed after adding this record.

## Limits

- Integration tests use real Git repositories, isolated worktrees and subprocess
  workers. The model responses and external GitHub publication boundary are
  deterministic fixtures, not a live autonomous-agent trial.
- Imported specialist methods are complete guidance, not an installed alternate
  runtime. The Python adapter and configured worker commands own execution.
- Decimal phases, an imported Node pre-GREEN gate and a new feature/milestone
  grouping engine are not claimed as implemented. Their supported boundaries
  and the proposed three entry workflows are documented.
- Required human UAT cannot be manufactured by automated test results.

## Delivery gate

The coordinator must observe successful Linux, Windows and aggregate checks for
the final PR head, mark the reviewed PR ready, and perform the user-authorized
merge. Preserve the user's original primary-checkout context edit in its verified
backup before the final fast-forward synchronization. Remove only this task's
clean, merged worktrees and branches.
