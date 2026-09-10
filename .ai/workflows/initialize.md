---
tier: contract
authority: agent
title: Initialize a project
---
> Contract: follow these steps within the approved scope.

# Initialize a project

## Purpose

Establish truthful context without inventing intent or overwriting an existing
project's knowledge.

## Inputs

PROJECT, config, current repository, existing instructions and the user's
initialization scope.

## Gates

Use [action-approved](../gates/action-approved.md) before changes.

## Steps

1. Inspect the assigned repository first. If already initialized, brief yourself
   and restructure nothing unless requested.
2. Read PROJECT and existing instructions; surface contradictory permissions or
   duplicated fact owners.
3. Ask only for missing human purpose, non-goals or constraints. Keep known
   facts in state/PROJECT.md; its location does not make intent freely writable.
4. Adopt existing records by linking or reconciling their owning facts. Keep
   meeting discussion as evidence rather than authoritative requirements.
5. Write specs only for current behavior in the area being adopted. Put
   decided-but-unbuilt changes into plans.
6. Set real verification commands or state that manual checks remain necessary.
   Populate current STATE and journal only observed actions.
7. Return the result and bounded next decision; publication uses its own granted
   scope.

## Output and handoff

A current context, verified record ownership and a decision summary. No empty
project needs invented product specs.

## Stop conditions

Do not infer intent, add a runtime or replace unrelated project files from
initialization alone.
