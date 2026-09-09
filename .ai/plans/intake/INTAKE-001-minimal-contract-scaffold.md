---
id: INTAKE-001
title: Minimal contract scaffold
status: planned
plan: PLAN-001
fix: null
---
# Minimal contract scaffold

## Report

The user requested a new Git worktree, removal of its existing project contents,
a precise `.ai` folder layout, draft rules/truth map/config/state, compact templates,
and basic agents/workflows. The user explicitly authorized pushing that worktree's
branch to GitHub and explicitly prohibited merging it.

The expected result is an isolated, reviewable draft. The original checkout must
remain unchanged. The linked worktree's `.git` administrative file is retained so
Git can track and push the requested branch.

## Impact and unknowns

The new branch replaces the old framework with a documentation scaffold. Detailed
contracts and future executable behavior still require user review. The other
project mentioned by the user was not inspected or copied; only the supplied
structure and instructions inform this draft.

## Proposed next action

The explicit scaffold-and-push action is tracked by
[PLAN-001](../review/PLAN-001-minimal-ai-contracts.md). After pushing, present the draft
for user review and wait for requested alterations. No merge is authorized.
