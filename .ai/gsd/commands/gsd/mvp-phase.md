---
name: gsd:mvp-phase
description: Plan a phase as a vertical MVP slice — user story, SPIDR splitting, then plan-phase
argument-hint: "<phase-number>"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
requires: [new-project, phase, plan-phase]
---
<objective>
Guide the user through MVP-mode planning for a phase. The command:

1. Prompts for an "As a / I want to / So that" user story (three structured questions)
2. Runs SPIDR splitting check — if the story is too large, walks through Spike/Paths/Interfaces/Data/Rules and offers to split into multiple phases
3. Writes `**Mode:** mvp` and the reformatted `**Goal:**` to the phase's ROADMAP.md section
4. Delegates to `/gsd plan-phase <N>` which auto-detects MVP mode via the roadmap field

Phase 1 of the vertical-mvp-slice PRD shipped the planner-side machinery; this command is the user entry point for it.
</objective>

<execution_context>
@.ai/gsd/workflows/mvp-phase.md
@.ai/gsd/references/spidr-splitting.md
@.ai/gsd/references/user-story-template.md
</execution_context>

<runtime_note>
**Copilot (VS Code):** Use `vscode_askquestions` wherever this workflow calls `AskUserQuestion`. Equivalent API.
</runtime_note>

<context>
Phase number: $ARGUMENTS (required — integer or decimal like `2.1`)

The phase must already exist in ROADMAP.md (created via `/gsd new-project`, `/gsd add-phase`, or `/gsd insert-phase`). This command does not create new phases — it converts an existing phase to MVP mode.
</context>

<process>
Execute the mvp-phase workflow from @.ai/gsd/workflows/mvp-phase.md end-to-end.
Preserve all gates: phase existence, status guard (refuse in_progress/completed), user-story format validation, SPIDR splitting check, ROADMAP write confirmation, plan-phase delegation.
</process>


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

The complete upstream body above is retained from GSD-Core at
`c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977`; only recorded reference substitutions
and explicit local conflict corrections have been made. See
`.ai/gsd/PROVENANCE.json` for exact source hashes and changes.

Read `.ai/gsd/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/gsd-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The upstream `config.json`, `/gsd:*` commands, tool
names, hooks, and Node CLI examples describe GSD's system; this import does not
install or activate that system. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
