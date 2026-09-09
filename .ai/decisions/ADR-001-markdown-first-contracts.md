---
id: ADR-001
title: Markdown-first project contracts
status: proposed
supersedes: null
---
# Markdown-first project contracts

## Context and alternatives

The user requested a clean worktree with a specific `.ai` structure, small templates,
a few agents and basic workflows. The former framework was large and mixed operating
mechanisms with project records. Alternatives include retaining that runtime or
building automatic enforcement immediately; neither is in the requested draft scope.

## Decision and rationale

Propose plain Markdown records, one YAML path/ID configuration, one truth map and
manual workflows. This makes the structure easy to inspect and alter before adding
runtime behavior. The requested directory layout is explicit user input; the finer
contract details in this draft still await review.

## Consequences

The draft can be reviewed without installing dependencies. Small checklists live in
plans, and templates remain flat. Agents have explicit descriptions and reporting
instructions. Manual hooks cannot prevent violations automatically; implementation
of enforcement would need a separately approved plan. The affected system inventory
is [SPEC-001](../specs/SPEC-001-project-contracts.md).
