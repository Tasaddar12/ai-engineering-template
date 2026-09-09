---
tier: plan
authority: agent
id: PLAN-001
owner: orchestrator
created: 2026-09-09
links: [INTAKE-001, INTAKE-002, SPEC-001, ADR-001]
features: [F01, F02, F03, F04, F05]
tasks: [T01, T02, T03, T04, T05, T06, T07, T08, T09, T10, T11]
title: Minimal AI contracts
---
> Plan: revise the proposed route as evidence changes; preserve accepted
> results.

# Minimal AI contracts

## Goal and scope

Provide the user's initial isolated .ai scaffold and requested role/workflow
refinements. F01 covers records; F02 roles; F03 workflows/research;
F04 policies/gates; F05 confirmed fixes and plan commands.

## Depends on

The user's requested isolated worktree and existing Git remote.

## Contract changes

### Specs to create

SPEC-001 describes the available document scaffold and its boundaries.

### Specs to amend

Include the requested roles, workflows, FIX/intake distinction and plan
status/verification interfaces as each draft feature exists.

### Specs to retire

None. Subsequent reference adaptation belongs to PLAN-002.

### Decisions

ADR-001 proposes the Markdown-first design and manual operation.

## Approach and tasks

- [x] T01 (F01): Isolate the worktree and retain its Git link.
- [x] T02 (F01): Create the requested structure and current records.
- [x] T03 (F02): Draft roles, templates and basic workflows.
- [x] T04 (F01, F02): Validate and publish the initial draft.
- [x] T05 (F03): Add workflow and research ownership.
- [x] T06 (F04): Connect firm policies and evidence gates.
- [x] T07 (F03, F04): Check operating-document consistency.
- [x] T08 (F02, F03): Expand named roles and consolidate project context.
- [x] T09 (F05): Add confirmed FIX lifecycle and intake distinction.
- [x] T10 (F05): Add e2e/decoupler and plan-status/plan-verify.
- [x] T11 (F05): Validate and publish the expanded document draft.

## Acceptance and validation

The requested structure, flat templates, role descriptions and procedure
links are available. Read-only document checks and remote-tip verification
were performed during its published revisions; see the dated journal and Git.

## Risks and unknowns

The draft contains manual contracts rather than automatic enforcement.
Acceptance of the final operating wording remains a user decision.

## Decision and delivery

The user authorized local drafting and commit/push to the assigned branch,
with no PR creation or merge. The published draft remains in review.
PLAN-002 owns the later instruction to adapt the reference reconstruction.

## Evidence and notes

The journal preserves initial drafting and publication events. Git retains
all revisions, including fe374d3 for the FIX and plan-command additions.
This record now follows the current plan template; the migration changes
its structure without changing those observed delivery facts.

### Draft publication gates

The original dated evaluations remain in the [published record](https://github.com/Tasaddar12/ai-engineering-template/blob/fe374d3599343bdc7dc7ced67e2ea4635cb3d0bc/.ai/plans/review/PLAN-001-minimal-ai-contracts.md#draft-publication-gates).

### Draft revision 3 publication gates

The revision 3 evaluation remains in the [published record](https://github.com/Tasaddar12/ai-engineering-template/blob/fe374d3599343bdc7dc7ced67e2ea4635cb3d0bc/.ai/plans/review/PLAN-001-minimal-ai-contracts.md#draft-revision-3-publication-gates).
