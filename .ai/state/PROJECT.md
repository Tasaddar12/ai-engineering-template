---
tier: intent
authority: human
id: PROJECT
title: AI engineering orchestration template
---

# AI engineering orchestration template

## Why this exists

This repository is a reusable operating structure for engineering agents. It
keeps project context, current specifications, proposed work, defect reports,
decisions and evidence in Git alongside the project they describe. The user's
copied material supplies the detailed command and role guidance.

The project is the template itself. There are no project-specific specs,
decisions, amendments or delivery records for this repository. Navigation
starts at [AGENTS.md](../../AGENTS.md); adoption into a different codebase uses
[ADOPTING.md](../../docs/ADOPTING.md) and a newly completed PROJECT template.

## What success looks like

A person can understand the project, ask for a report or plan, approve a
bounded change, and follow its evidence through verification and Git delivery.
Agents can find the relevant instructions and fact owners without interpreting
obsolete scaffolding or guessing which competing document is current.

## Non-goals

Building an application or a new orchestration runtime in this repository.
Restoring the removed Python framework, deleted project history as live
requirements, or source-project configuration that is not used here.

## Hard constraints

The [approval policy](../policies/approval.md) owns the user's report, summary
and decision requirement. The chosen structure keeps PROJECT beside STATE,
flat templates, detailed role files, command procedures, policies and gates.
Worktree ownership and authorized publication follow the
[execution policy](../policies/execution.md). Record guidance for projects
adopting the template is in the [record policy](../policies/records.md).

## Out of bounds for agents

Inventing project purpose or broadening the approved outcome. Treating copied
examples as installed tools or proof of a completed run. Touching unrelated
checkouts or deleting files outside the assigned cleanup scope.

## Stakeholders

The repository owner sets intent and action authority. People and agents
adopting the template need accurate instructions, usable reports and clear
limits. No additional stakeholder roles have been specified.
