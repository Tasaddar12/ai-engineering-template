# References and templates retirement summary

## Why

Retire the confirmed legacy reference/template procedures in this assigned slice
after the full-source review recorded in `REVIEW.md`. Keep reusable methods and
the template registry aligned with the retained workflow. This is a documentation
retirement slice; integrated callers and runtime behavior remain for the coordinator
to validate after joining all worker branches.

## Changes

- Deleted the ten authorized legacy references: `agent-skills-bootstrap.md`,
  `continuation-format.md`, `execute-phase-context-guard.md`,
  `git-planning-commit.md`, `mandatory-initial-read.md`,
  `model-profile-resolution.md`, `offer-next.md`, `phase-argument-parsing.md`,
  `phase-id-convention.md`, and `project-skills-discovery.md`.
- Deleted `engineer/templates/DEBUG.md` and
  `engineer/templates/milestone-archive.md`. Kept `milestone.md` as the completed
  milestone entry contract.
- Replaced MemPalace setup and indexing with offline knowledge-base search and
  explicit semantic comparison. Kept coordinator-owned writes, evidence checks,
  and secret redaction (R-RF-23).
- Reworked context budgeting around assigned roles, evidence-led read depth,
  coherent outcome sizing, and explicit handoff capacity. Removed retired context
  guard settings, MCP-specific setup, mandatory estimator/calibration, and fixed
  task-count rules (R-RF-14 through R-RF-17).
- Removed retired external-review ordering and convergence references from the
  retained planner methods; kept the review-dispositions ledger and its
  feedback-led process (R-RF-02, R-RF-38).
- Updated `agent-contracts.md` to remove the retired debug-session-manager and
  plan-review-convergence consumers while preserving the retained capability
  roster, including `dom-verifier`.
- Updated `debugger-fix-acceptance.md` to describe the active session record
  directly, without a link to the deleted DEBUG template or the retired session
  manager.
- Updated the template registry to remove the retired Windows ledger, AI-SPEC,
  DEBUG, and milestone-archive entries/links (R-TP-44, R-TP-53). The separate
  `milestone.md` entry template remains listed.

## Applicable retirement rows

| Row | Result |
|---|---|
| R-RF-02 | Kept the planner review-ledger method; removed its obsolete workflow and capability-registry dependencies. |
| R-RF-14–17 | Removed legacy context control and estimation procedures; retained practical context selection and outcome sizing. |
| R-RF-23 | Replaced MemPalace with local search plus full semantic comparison. |
| R-RF-38 | Removed the retired external-review ordering block. |
| R-TP-44 / R-TP-53 | Removed registry entries for retired templates. |
| Section 10; R-AG-008/011 | Removed the exact authorized shared bootstrap, continuation, model, phase, and template helpers. |

## Verification

- Confirmed repository root, branch `phase-legacy-references`, and HEAD
  `734ecc2cb80e1b72041f0e823802530ce3ed8541` before editing.
- `git diff --check` passed.
- The authorized deletion set matched exactly 12 paths.
- Static local-link parsing checked the changed Markdown files. It found no new
  broken targets versus HEAD; four pre-existing example includes in
  `planner-antipatterns.md` still point at illustrative phase summaries absent
  from this template repository.
- Searches of retained references/templates found no imports to the twelve
  deleted files and no remaining MemPalace, `WINDOWS.md`, context-guard,
  estimator/calibration, external-review, or `ENGINEER_WS` surfaces. The retained
  Batch B `revision-loop.md` remains unchanged by explicit scope and still mentions
  `/plan-review-convergence`; that retained-reference reconciliation is outside
  this slice.
- No runtime tests were run: this slice changes references and templates only.
  Full caller, static-link, and runtime validation remains an integration check
  after the other assigned slices are joined.
