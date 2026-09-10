---
tier: contract
authority: agent
title: Verify current behavior
---
> Contract: follow these steps within the approved scope.

# Verify current behavior

## Purpose

Determine whether the result satisfies current contracts and the approved
outcome, not whether a prediction's boxes are all checked.

## Inputs

The selected plan or FIX, exact revision/environment, relevant specs and agreed
verification commands.

## Gates

Use [action-approved](../gates/action-approved.md) for checks. Before delivery apply [delivery-ready](../gates/delivery-ready.md).

## Steps

1. Identify the revision, base and pending diff. Read current specs and the
   approved outcome; treat the plan's route as revisable evidence.
2. Walk each contract criterion and invariant against observed behavior. An
   obsolete predicted step is not itself a product failure; a silently dropped
   approved outcome is.
3. Run configured and relevant targeted checks. With no configured commands,
   identify actual manual checks and limits; an empty list is not a pass.
4. Use tester and e2e as needed. For FIX, prove the guard failed before and
   passed after, the cause was addressed and no unapproved behavior changed.
5. Walk Contract changes against the repository: every create, amendment,
   retirement and decision must be delivered or explicitly reconciled.
6. Check record drift, tense, duplicated ownership and signatures of a
   stale-spec workaround. Record drift is a finding, not a footnote.
7. Return PASS, FAIL or CANNOT_VERIFY with per-criterion evidence. Missing
   required evidence prevents a passing delivery gate.
8. Store authorized evidence in the selected record; append evidence for
   historical done records to the journal. A report-only request changes no
   files.

## Output and handoff

A plan-verification.md report linking current behavior, contract reconciliation,
actual checks and limits. A relevant change invalidates affected evidence.

## Stop conditions

Do not repair code/specs or merge from verification. Preserve incomplete checks
and return the precise missing action.
