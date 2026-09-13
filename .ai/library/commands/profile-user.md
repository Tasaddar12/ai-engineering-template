---
name: workflow:profile-user
description: Generate developer behavioral profile and create Claude-discoverable artifacts
argument-hint: "[--questionnaire] [--refresh]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
  - Agent
---

<objective>
Generate a developer behavioral profile from session analysis (or questionnaire) and produce artifacts (USER-PROFILE.md, `workflow-dev-preferences` skill config, CLAUDE.md section) that personalize Claude's responses.

Routes to the profile-user workflow which orchestrates the full flow: consent gate, session analysis or questionnaire fallback, profile generation, result display, and artifact selection.
</objective>

<execution_context>
@.ai/library/workflows/profile-user.md
@.ai/library/references/ui-brand.md
</execution_context>

<context>
Flags from $ARGUMENTS:
- `--questionnaire` -- Skip session analysis entirely, use questionnaire-only path
- `--refresh` -- Rebuild profile even when one exists, backup old profile, show dimension diff
</context>

<process>
Execute the profile-user workflow end-to-end.

The workflow handles all logic including:
1. Initialization and existing profile detection
2. Consent gate before session analysis
3. Session scanning and data sufficiency checks
4. Session analysis (profiler agent) or questionnaire fallback
5. Cross-project split resolution
6. Profile writing to USER-PROFILE.md
7. Result display with report card and highlights
8. Artifact selection (dev-preferences, CLAUDE.md sections)
9. Sequential artifact generation
10. Summary with refresh diff (if applicable)
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
