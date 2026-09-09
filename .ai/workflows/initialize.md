# Initialize project records

## Purpose

Create or refine the approved operating scaffold without inventing product behavior.

## Inputs

An explicit initialization scope, the target worktree and known project facts.
An existing project also supplies its current records and contracts.

## Gates

Before creating or changing files: [action-approved](../gates/action-approved.md).
Use the user's direct instruction as evidence when no records exist yet.

## Steps

1. The orchestrator inspects the target and identifies existing files to preserve.
   Initialization never implies permission to delete or overwrite an existing project.
2. Create only the approved structure and templates, using the paths in config.
3. Populate state/PROJECT.md with known purpose, users, context and boundaries.
   Keep unknown product facts explicit; point implementation details to the owning SPEC.
4. Populate state/STATE.md with Now / Next / Blockers and link the initial intake/plan.
5. Describe the actual scaffold in its SPEC, link draft decisions, and append the
   initialization event and authority to the journal.
6. Return a decision summary of created/refined records and unresolved choices.

## Output and handoff

A small, reviewable document scaffold and project context. Planning or product work
starts only under its own approved action.

## Stop conditions

Pause on conflicting ownership, unclear overwrite scope or missing project facts.
Do not install dependencies, launch agents or claim executable enforcement exists.
