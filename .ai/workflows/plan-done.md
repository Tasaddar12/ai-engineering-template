---
tier: contract
authority: agent
title: Close accepted work
---
> Contract: follow these steps within the approved scope.

# Close accepted work

## Purpose

Close on demonstrated outcomes and authorized delivery rather than checkbox
completion.

## Inputs

A selected PLAN/FIX, current verification, user acceptance and delivery
evidence.

## Gates

Use [completion-ready](../gates/completion-ready.md).

## Steps

1. Confirm the current contract and approved outcome pass verification with no
   unresolved required checks.
2. Walk Contract changes or FIX proof against actual records and code.
3. Confirm required independent review, user acceptance and completion of the
   delivery that was authorized.
4. Move the record to done, retain its ID/slug and repair live references.
5. Update STATE and append the outcome. Keep follow-up work in linked records;
   use delivery cleanup only after an actual merge.

## Output and handoff

An accepted done record and accurate current coordination.

## Stop conditions

Push-only draft publication is not acceptance. Do not close missing proof or
overwrite historical outcomes.
