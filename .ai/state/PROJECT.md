# Project context

## Purpose and users

This project is a small Markdown/YAML operating scaffold for the project owner and
agents carrying out explicitly approved engineering work. It keeps project knowledge
and action boundaries understandable before any automation is introduced.

## Desired outcome

Use clear fact ownership, compact templates, explicit policies and evidence-based
PASS/FAIL gates. Capture requests as reports, present a summary and obtain the user's
decision before any action that has not already been explicitly authorized.

## Context and boundaries

The owner requested this fresh draft in an isolated worktree after finding the earlier
framework unnecessarily complex. Keep refinements small and reviewable. The eight
agent roles and manual workflows describe responsibilities and handoffs; they do not
start provider processes, install software or automatically execute commands.

Live work, current authority and next decisions belong to [STATE](STATE.md), rather
than this background document.

## System overview

- [SPEC-001](../specs/SPEC-001-project-contracts.md) owns current implementation details.
- [Truth map](../truth-map.md) assigns one owner per fact.
- [Policies](../policies/README.md) own firm requirements.
- [Workflows](../workflows/README.md) describe operations; [commands](../commands/README.md) select them.
- [Gates](../gates/README.md) evaluate transitions; [hooks](../hooks/README.md) identify checkpoints.
- [Agents](../agents/README.md) define roles; [research](../research/README.md) retains investigation evidence.
- [ADR-001](../decisions/ADR-001-markdown-first-contracts.md) holds the proposed design rationale.

## Open decisions

The draft contracts, role boundaries and workflow/gate wording remain available for
user review. Automatic enforcement, provider integration, application code and CI are
outside this draft. Merge authority has not been granted.
