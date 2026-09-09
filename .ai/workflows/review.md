# Review a proposal or result

## Purpose

A proposal, recommendation or implementation is ready for inspection.

## Inputs

The subject, review type, exact commit or identified draft revision, and available evidence.

## Gates

Before inspection: [review-ready](../gates/review-ready.md).
Running additional checks also needs authority under [action-approved](../gates/action-approved.md).

## Steps

1. Confirm the subject and revision. For implementation, use a reviewer independent
   of the implementor.
2. Inspect scope, acceptance, fact ownership and documentation. For implementation,
   inspect the entire diff and actual validation evidence.
3. Return one PASS or CHANGES_REQUIRED report using the review template. Each issue
   needs a location, impact and remedy; state the review's limits.
4. The orchestrator records or links the report in the selected PLAN or FIX validation
   section, or appends to the journal for a historical done record. Journal the
   observation and present a user decision summary.
5. Changed content requires a fresh review of the revised subject.

## Output and handoff

One review report and a bounded repair, acceptance or delivery decision. A small review can live in its PLAN or FIX; no extra tracker is needed.

## Stop conditions

Do not edit implementation, run unapproved checks or treat PASS as user approval. Missing evidence or an unstable revision must be reported.
