---
tier: plan
authority: agent
id: PLAN-002
owner: orchestrator
created: 2026-09-09
links: [PLAN-001, SPEC-001, ADR-002, AMD-001]
features: [F01, F02, F03]
tasks: [T01, T02, T03, T04, T05, T06]
title: Adopt reference operating contracts
---
> Plan: revise the proposed route as evidence changes; preserve accepted
> results.

# Adopt reference operating contracts

## Goal and scope

Bring this scaffold close to the user-provided AI Orchestration Template
reconstruction, using our chosen .ai layout and user-controlled authority.

F01 covers tiers, contradiction handling, current specs and directory stages.
F02 covers role scopes, record templates and lifecycle operations.
F03 covers dependency waves, contention tracks, evidence and delivery.

## Depends on

The existing scaffold delivered by PLAN-001. No external runtime or package
dependency is required for this documentation adaptation.

## Contract changes

### Specs to create

None; SPEC-001 owns this scaffold's document interfaces.

### Specs to amend

Rewrite SPEC-001 in present tense with these current interface statements:

- A PLAN or FIX receives its lifecycle stage from its directory.
- Roles declare reads/writes and actionable reporting boundaries.
- Plans carry exact future contract wording until implementation lands it.
- FIX proof demonstrates failure before repair and success afterward.
- Commands point to procedure owners; verification grades observed behavior.
- Run documents define dependency waves, contention tracks and reserved IDs.

### Specs to retire

Remove historical narrative from SPEC-001. Preserve rationale and evidence
in ADRs, amendments, journal records and Git.

### Decisions

ADR-001 retains the original scaffold rationale. ADR-002 proposes the
reference adaptation and explicit choices for this repository.
AMD-001 records the changed operating contracts within the user's request.

## Approach and tasks

- [x] T01 (F01): Reconcile rules, policies, config and fact ownership.
- [x] T02 (F01, F02): Migrate templates/records and remove duplicate stages.
- [x] T03 (F02): Expand named roles; add plan-checker and scribe boundaries.
- [x] T04 (F02): Connect lifecycle commands, proof and contract verification.
- [x] T05 (F03): Define wave/track coordination, ID reservations and cleanup.
- [x] T06 (F01, F02, F03): Validate final files and prepare authorized delivery.

## Acceptance and validation

The requested layout remains; intent stays in state/PROJECT.md.
All .ai Markdown documents use tiers except preserved legacy journal content.
PLAN/FIX stage exists only as a directory. Role and command references resolve.
Templates contain the reference's required decision/proof fields.
SPEC-001 describes current document interfaces without historical narrative.

Perform final read-only structural checks, template and ID checks, link and
path inspection, rule consistency inspection and staged Git whitespace checks.
No product runtime, independent agent execution or installed hook is claimed.

## Risks and unknowns

Manual role instructions are not sandbox enforcement. Cold review depends
on a genuinely separate context; its absence must be disclosed.
Runtime-specific prompt installation and dispatch remain outside scope.

## Decision and delivery

The user directly instructed: make our work close to the pasted reference.
The existing instruction authorizes committing and pushing all scaffold
updates to codex/ai-contract-scaffold. Work only in ai-contract-scaffold.
PR creation and merge remain excluded. The resulting draft stays in review.

## Evidence and notes

Read-only document validation passed across 132 files: twelve role contracts,
record/template metadata and sections, eight unique record IDs, configured
paths, 263 internal links and anchors, directory-only PLAN/FIX stages, command
handoffs, current SPEC tense, ignored nested worktrees and unchanged prior
journal content. Git whitespace inspection passed.

Author inspection reconciled scope, amendment authority, review independence,
FIX/PLAN routing and merge/cleanup boundaries. This is a document draft;
no runtime tests, agent dispatch or independent reviewer run were performed.
Final record additions receive the same structural check before commit.

Git owns the observed commit and remote tip. User acceptance is still pending.

### Publication gate evidence

Gate: action-approved.
Subject: PLAN-002 pending draft on codex/ai-contract-scaffold.
Evaluator: orchestrator, using the user's direct adaptation instruction and
the existing instruction to commit/push all scaffold updates.
Result: PASS for this worktree's document adaptation and publication only.

Gate: delivery-ready for draft commit.
Scope/spec evidence: the final document diff and current SPEC-001.
Validation: structural checks and author inspection above.
Acceptance: pending, under the explicit documentation-draft provision.
Message: Adapt PLAN-002 scaffold to reference operating contracts.
Result: PASS subject to final staged whitespace validation.
Merge-only criteria: N/A; no PR creation or merge is authorized.

Next action: commit the staged draft, check the resulting clean branch before
push, publish only that branch and compare remote HEAD. These later Git
observations are reported directly; they are not asserted in advance.
