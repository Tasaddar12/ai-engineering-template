---
id: SPEC-001
title: Project contracts
status: current
scope: Document layout, available artifacts and the interfaces of this scaffold.
---
# Project contracts

## Current implementation

This revision is a Markdown/YAML scaffold. The previous Python framework and its
project records are removed from this branch. No executable product is implemented.

| Surface | Implemented content |
| --- | --- |
| Root | AGENTS.md routes agents to the rules; README.md provides navigation. |
| `.ai/RULES.md` | Engagement entry point linking the owning policies, gates and workflows. |
| `.ai/truth-map.md` | A single owner for each category of fact; overlapping ownership is reported as drift. |
| `.ai/config.yaml` | Relative paths, record filename formats, ID allocation and journal date conventions. |
| `.ai/state/PROJECT.md` | Stable purpose, users, desired outcome, background, boundaries and system links. |
| `.ai/specs` | Numbered current-behavior documents with bounded ownership. This file is the initial system overview. |
| `.ai/decisions` | Numbered rationale documents; the initial layout ADR is proposed. |
| `.ai/decisions/amendments` | Reserved for numbered contract-change proposals and accepted/rejected amendments. |
| `.ai/decisions/retired` | Reserved for superseded accepted decisions, retaining their original rationale. |
| `.ai/plans/intake` | Numbered reports for bugs, drift, problems and unplanned work. |
| `.ai/plans` lifecycle folders | Backlog, active, review, blocked, abandoned and done; README defines transitions. |
| `.ai/state/STATE.md` | Now / Next / Blockers with links to the owning records. |
| `.ai/state/journal` | Daily Markdown records; new timestamped entries are appended. |
| `.ai/templates` | Flat templates for project/state, records, agent assignments/completions, test results, PR summaries, workflows, commands, policies and gate definitions/results. |
| `.ai/agents` | Orchestrator, researcher, planner, implementor, reviewer, tester, bug-reviewer and pr-agent definitions, with YAML descriptions, workflow/report references and bounded responsibilities. |
| `.ai/commands` | Thin entry points for initialize, report, research, planning, implementation, review, parallel-execution and deliver. |
| `.ai/workflows` | Procedure owners with purpose, inputs, linked gates, steps, output/handoff and stop conditions. |
| `.ai/research` | Record conventions for bounded investigations; no completed research is fabricated. |
| `.ai/policies` | Firm approval, record, execution and parallel-assignment requirements, with evidence expectations. |
| `.ai/gates` | Manual PASS/FAIL definitions for action approval, parallel readiness, review readiness, delivery and retirement. |
| `.ai/hooks` | Event-to-gate links; no executable hook is installed. |

Record filename details belong to [config](../config.yaml). The initial intake links
to one small plan; the plan embeds its feature/task checklist instead of introducing
separate task and feature directories. Empty requested lifecycle folders contain
`.gitkeep`, allowing Git to preserve the structure when cloned.

## Invariants and boundaries

This spec owns the inventory and implemented document interfaces. [RULES](../RULES.md)
is the engagement entry point; [policies](../policies/README.md) own obligations,
[gates](../gates/README.md) own transition criteria, [truth-map](../truth-map.md) owns
fact ownership, and each workflow owns its step sequence. These contracts are linked
here rather than redefined.

Gate results are recorded with the gate-result template in a subject plan or intake;
the journal records the evaluation event. Research has a question, consulted sources,
findings, limits and a next decision. Neither a recommendation nor a gate result is
an implementation or a new user approval.

Initialization prepares known project records. Planning produces a bounded proposal;
implementation hands an assigned result from implementor to tester, then independent
review. Parallel execution describes fixed, nonoverlapping assignments and combined
validation; it does not launch any workers. The pr-agent prepares delivery reports
and performs Git writes only under an authorized assignment. The orchestrator retains
shared-state ownership and coordination.

Project context now lives with live state under state; the earlier intent folder has
been removed. Historical journal entries remain unchanged.

A SPEC describes the revision containing it. A draft branch's SPEC does not claim
its contents have merged into main. Git and the host own revision/merge facts.

## Evidence and limitations

Evidence is the tracked document tree and [PLAN-001](../plans/review/PLAN-001-minimal-ai-contracts.md).
Documentation checks and their results are recorded there and in the journal.
No application tests, automated enforcement, provider integration or CI exist in this
draft. The user must review proposed contract details before accepting them.

## Change references

- [INTAKE-001](../plans/intake/INTAKE-001-minimal-contract-scaffold.md): requested reset and target layout.
- [PLAN-001](../plans/review/PLAN-001-minimal-ai-contracts.md): bounded scaffold drafting and push-only delivery.
- [ADR-001](../decisions/ADR-001-markdown-first-contracts.md): proposed rationale and tradeoffs.
- [INTAKE-002](../plans/intake/INTAKE-002-expand-operating-documents.md): requested workflow, research, policy and gate refinements.
