---
tier: log
authority: agent
id: AMD-001
amends: RULES and operating contracts
raised_by: orchestrator
links: [PLAN-002, SPEC-001, ADR-002]
title: Reference contract adaptation
---
> Log: preserve evidence; append corrections.

# Reference contract adaptation

## What the document said

The earlier draft required PLAN/FIX status metadata to agree with lifecycle
folders and routed all accepted-contract amendments through a separate user
approval. Plans referenced specs without exact Contract changes wording.

## What is supported now

The user explicitly instructed adaptation to the supplied reconstruction.
The resulting documents use directory stages, exact proposed contract
wording, positive role scopes and evidence-led repair/verification.

## Why they diverged

This was an authorized redesign of an unaccepted documentation scaffold.
The user's existing layout and report-before-new-work boundary remained
binding while the implementation of the document contracts changed.

## Replacement and effect

Records policy now permits evidenced stale-contract correction inside an
already approved outcome, with an AMD, while human intent and scope changes
still require a user decision. PLAN/FIX stage metadata was removed; templates,
roles, workflows, gates and SPEC-001 were reconciled together in PLAN-002.
