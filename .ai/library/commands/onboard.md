---
name: workflow:onboard
description: Guide existing codebase onboarding through mapping, doc ingest, and planning setup
argument-hint: "[--fast] [--text]"
allowed-tools:
  - Read
  - Bash
  - Write
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
requires: [config, new-project, map-codebase, ingest-docs, manager]
---
<runtime_note>
**Copilot (VS Code):** Use `vscode_askquestions` wherever this workflow calls `AskUserQuestion`. They are equivalent — `vscode_askquestions` is the VS Code Copilot implementation of the same interactive question API.
</runtime_note>

<objective>
Guide brownfield onboarding for an existing codebase by routing through the existing Workflow primitives in the safe order: codebase map → docs ingest → project initialization → onboarding summary.

**Creates or confirms:**
- `.planning/codebase/` — evidence-backed codebase map from `/workflow:map-codebase`
- `.planning/PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md` — project setup from `/workflow:new-project` or `/workflow:ingest-docs`
- `.planning/onboarding/SUMMARY.md` — lightweight index of what was learned and the next command

**Non-goals:** This command does not execute phases, ship work, or overwrite existing planning artifacts without an explicit gate.
</objective>

<execution_context>
@.ai/library/workflows/onboard.md
@.ai/library/references/ui-brand.md
@.ai/library/references/gate-prompts.md
</execution_context>

<context>
Arguments: $ARGUMENTS

Flags:
- `--fast` — prefer `/workflow:map-codebase --fast` for the mapping handoff; the complete map is still required before `/workflow:new-project`.
- `--text` — use plain-text numbered lists instead of TUI menus.
</context>

<process>
Execute the onboard workflow end-to-end. Preserve all safety gates, text-mode fallbacks, idempotency checks, and top-level handoff rules for nested interactive commands.
</process>


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
