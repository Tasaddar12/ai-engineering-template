---
tier: plan
authority: agent
id: PLAN-{{ nnn }}
owner: {{ owner }}
created: {{ date }}
links: []
features: []
tasks: []
title: {{ title }}
---
> Plan: revise the proposed route as evidence changes; preserve accepted
> results.

# {{ title }}

## Goal and scope

The approved outcome, exclusions, originating records and feature references.
A changed route can be rewritten; a changed outcome needs a user decision.

## Depends on

List prerequisite plans and evidence. Distinguish dependency (needs a result)
from contention (edits the same files). State None when independent.

## Contract changes

### Specs to create

Draft exact present-tense wording to land with working behavior, or None.

### Specs to amend

For each SPEC: current wording, proposed wording and why. Keep proposed
behavior here until implemented. A pure repair keeps valid criteria intact.

### Specs to retire

Name the SPEC or criteria and why they no longer apply, or None.

### Decisions

Name ADRs to create, confirm or supersede, and AMDs needed for corrections.
Only accepted ADRs carry authority; do not treat a proposal as settled.

## Approach and tasks

Explain the approach and bounded slices with task/feature IDs, owned files
and observable results. Steps should be independently understandable.

- [ ] T01 (F01): One coherent slice and its acceptance condition.

## Acceptance and validation

State user-visible outcomes, invariants and commands or repeatable checks.
Use configured checks plus relevant targeted coverage. Grade the result
against current contracts, not whether the predicted steps were followed.

## Risks and unknowns

Name assumptions, unresolved decisions and the work independent of them.

## Decision and delivery

Exact execution and delivery authority, worktree/branch and next decision.
For blocked work, name the question, owner and resume condition here.

## Evidence and notes

Link actual observations, review and verification. Record route changes
without claiming an unrun check passed. Preserve completion evidence.

<!-- PLAN-{nnn}-{slug}.md. Directory owns stage; no status/stage field.
Contract changes contains future wording; specs describe current behavior. -->
