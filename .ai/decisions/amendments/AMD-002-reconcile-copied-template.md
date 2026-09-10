---
tier: log
authority: agent
id: AMD-002
title: Reconcile copied contracts with this repository
date: 2026-09-09
amends: [AI-README, TRUTH-MAP]
raised_by: coordinator
links: [PLAN-004, SPEC-002]
---

# AMD-002: Reconcile copied contracts with this repository

> Log tier. Preserve this record; append a successor for later corrections.

## What the document said

At `5967dbe`, the copied operating material locates roles under `.claude/`,
intent under `.ai/intent/`, and refers to an executor, a roadmap/roadmapper,
MEETING.md and ADOPTING.md that are absent. Config enables background dispatch
without a launcher. The previous scaffold says workflows own procedures while
the copied commands themselves contain those procedures. Old review plans cite
SPEC-001 and decisions removed by the user's replacement.

## What is actually true

Git's tracked tree contains `.ai/agents/`, `.ai/commands/`, root AGENTS.md and
`.ai/state/PROJECT.md`. The role filename is implementor.md. Optional shell
scripts exist without hook registration or a dispatcher. Origin is GitHub and
this session has an authenticated GitHub CLI. The user explicitly authorized
reconciling all content, removing obsolete files, and delivering through a PR.

## Why they diverged

A detailed working template was copied from another project over earlier
scaffolding. Some source-project paths and claims, plus duplicate and obsolete
scaffold documents, remained in the merged tree.

## What I changed it to

PROJECT and STATE share `.ai/state/`. AGENTS.md routes to RULES and the
approval policy; commands own their procedures, workflows compose those
commands, roles own their scopes, and policies/gates own cross-cutting
requirements and transitions. Indexes and flat templates match the retained
files. The missing meeting template and adoption guide support commands that
are present. Unsupported roadmap/full-mode claims are removed; manual dispatch
is the configured operating posture, with optional host integration documented
as unregistered. Current template interfaces are recorded in SPEC-002.

Obsolete PLAN-001/002 and INTAKE-001/002 scaffold records, duplicate workflow
bodies/command aliases, and unused scaffolding templates are removed. Prior
journal entries remain byte-for-byte intact, including their historical
references; Git retains the records those events originally described.
