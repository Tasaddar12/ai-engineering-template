---
name: workflow-workflow
description: "workflow | discuss plan execute verify phase progress"
argument-hint: ""
allowed-tools:
  - Read
  - Skill
requires: [discuss-phase, spec-phase, plan-phase, execute-phase, verify-work, phase, progress, next, ultraplan-phase, plan-review-convergence, add-tests, ai-integration-phase, autonomous, fast, mvp-phase, quick, quick-batch]
---

Route to the appropriate phase-pipeline skill based on the user's intent.
Sub-skill names below are post-#2790 consolidated targets — `workflow-phase`
absorbs the former add/insert/remove/edit-phase commands and `workflow-progress`
absorbs the former next/do workflow-advance commands. The reclaimed
`workflow-next` target is the state-aware smart-entry launcher, not the retired
workflow-advance command.

| User wants | Invoke |
|---|---|
| Gather context before planning | workflow-discuss-phase |
| Clarify what a phase delivers | workflow-spec-phase |
| Create a PLAN.md | workflow-plan-phase |
| Execute plans in a phase | workflow-execute-phase |
| Verify built features through UAT | workflow-verify-work |
| Add / insert / remove / edit a phase | workflow-phase |
| Advance to the next logical step | workflow-progress |
| Open the state-aware smart-entry launcher | workflow-next |
| Offload planning to the ultraplan cloud | workflow-ultraplan-phase |
| Cross-AI plan review convergence loop | workflow-plan-review-convergence |
| Generate tests for a completed phase | workflow-add-tests |
| Design an AI-integration phase | workflow-ai-integration-phase |
| Run all remaining phases autonomously | workflow-autonomous |
| Execute a trivial task inline | workflow-fast |
| Plan a phase as a vertical MVP slice | workflow-mvp-phase |
| Execute a quick task with Workflow guarantees | workflow-quick |
| Batch several quick-shaped tasks together | workflow-quick-batch |

Invoke the matched skill directly using the Skill tool.


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

This complete authoring guide retains its source content, examples, and methods.
Only recorded namespace/reference substitutions and explicit local conflict
corrections have been made. Source attribution and exact original hashes are
isolated in `.ai/library/THIRD-PARTY-NOTICES.md` and `PROVENANCE.json`.

Read `.ai/library/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/template-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The retained `config.json`, `/workflow:*` commands, tool
names, hooks, and Node CLI examples describe supporting source capabilities;
this import does not install or activate them. Source catalog pointers in examples
identify provenance, not executable command arguments. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
