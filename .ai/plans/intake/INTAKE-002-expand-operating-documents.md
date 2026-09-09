---
id: INTAKE-002
title: Expand operating documents
status: planned
plan: PLAN-001
---
# Expand operating documents

## Report

The user explicitly requested workflows and research folders in the existing scaffold
worktree, with modest detail for review. They then requested policies for firm
requirements and gates for PASS/FAIL conditions before workflows advance.

They then named eight roles: orchestrator, researcher, planner, implementor, reviewer,
tester, bug-reviewer and pr-agent. They requested initialize, planning, implementation,
review and parallel-execution workflows, and replacement of the intent folder with
PROJECT.md beside STATE.md in state.

Previously commands contained the procedures, and hooks listed manual checks. The
requested additions need clear ownership so the same requirement is not defined in
several places.

## Impact and unknowns

These are draft documentation changes only. No investigation, automatic enforcement
or product implementation is being performed. Fine-grained policy and gate wording
remains open for review.

## Proposed next action

Refine the existing [PLAN-001](../review/PLAN-001-minimal-ai-contracts.md) draft under
the user's direct instructions. Add the directories, roles and workflows, consolidate
project context under state, link their owners, and
present the draft for feedback. After drafting, the user explicitly authorized
committing and pushing it to the existing branch. No PR creation or merge is authorized.
