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
| `.ai/RULES.md` | Report/decision gate, mutability tiers, amendment procedure and delivery boundaries. |
| `.ai/truth-map.md` | A single owner for each category of fact; overlapping ownership is reported as drift. |
| `.ai/config.yaml` | Relative paths, record filename formats, ID allocation and journal date conventions. |
| `.ai/intent/INTENT.md` | Desired outcome, users, boundaries and exclusions. |
| `.ai/specs` | Numbered current-behavior documents with bounded ownership. This file is the initial system overview. |
| `.ai/decisions` | Numbered rationale documents; the initial layout ADR is proposed. |
| `.ai/decisions/amendments` | Reserved for numbered contract-change proposals and accepted/rejected amendments. |
| `.ai/decisions/retired` | Reserved for superseded accepted decisions, retaining their original rationale. |
| `.ai/plans/intake` | Numbered reports for bugs, drift, problems and unplanned work. |
| `.ai/plans` lifecycle folders | Backlog, active, review, blocked, abandoned and done; README defines transitions. |
| `.ai/state/STATE.md` | Now / Next / Blockers with links to the owning records. |
| `.ai/state/journal` | Daily Markdown records; new timestamped entries are appended. |
| `.ai/templates` | Flat templates for intake, plan, spec, ADR, amendment, journal, state, intent, agent and decision summary. |
| `.ai/agents` | Coordinator, implementer and reviewer definitions with YAML descriptions and role-specific steps/prohibitions/reports. |
| `.ai/commands` | Report, plan, execute and deliver workflows, expressed as short Markdown procedures. |
| `.ai/hooks` | A manual checkpoint table; no executable hook is installed. |

Record filename details belong to [config](../config.yaml). The initial intake links
to one small plan; the plan embeds its feature/task checklist instead of introducing
separate task and feature directories. Empty requested lifecycle folders contain
`.gitkeep`, allowing Git to preserve the structure when cloned.

## Invariants and boundaries

This spec owns the inventory and implemented document interfaces. [RULES](../RULES.md)
owns obligations; [truth-map](../truth-map.md) owns fact ownership; each linked workflow
owns its step sequence. Those contracts are referenced here rather than redefined.

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
