---
tier: contract
authority: agent
title: Correct a contract
---
> Contract: follow these steps within the approved scope.

# Correct a contract

## Purpose

Give stale documentation a supported correction route inside approved work.

## Inputs

The contradiction, owning contract, evidence and existing action authority.

## Gates

Use [action-approved](../gates/action-approved.md); human intent or changed outcome needs the corresponding
decision.

## Steps

1. Identify which side is wrong. Code that violates a valid requirement goes to
   FIX.
2. For a stale contract, draft the AMD with old wording, evidence, reason and
   exact replacement or deletion.
3. Rewrite the SPEC to supported present truth. Do not annotate it with obsolete
   requirements or future promises.
4. For an accepted ADR replacement, create a new accepted decision and preserve
   the superseded rationale under records policy.
5. Follow downstream references, update the plan's Contract changes and land
   related code/contracts together.
6. Journal the correction and resolve the linked drift record only when its
   evidence is addressed.

## Output and handoff

A concise amendment and a truthful contract, or an explicit unresolved decision.

## Stop conditions

Do not redefine success to match a defect or infer human intent from working
code.
