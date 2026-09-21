---
name: onboard
description: "Initialize a project's planning records from the user's intent - PROJECT.md, REQUIREMENTS.md and a phased ROADMAP.md."
argument-hint: "[project description]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
  - Agent
  - WebSearch
  - WebFetch
---

<objective>
Turn what the user wants into the records every other command reads.

**How it works:**

1. Map an existing codebase first, where there is one
2. Question until the vision is concrete - following threads, not walking a checklist
3. Write PROJECT.md from the user's intent, with no placeholders left
4. Configure the project's real verification commands
5. Scope requirements with REQ ids and a mandatory out-of-scope list
6. Break the first milestone into phases through the runtime

**Output:** PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md and config.yaml,
filled from the conversation rather than copied from templates.

This is the only workflow that creates those records. Everything downstream
assumes they say something true.
</objective>

<execution_context>
Workflow files are loaded on demand in the <process> section below - not upfront.
</execution_context>

<context>
Arguments: $ARGUMENTS
Optional project description: $ARGUMENTS. With none, the workflow opens by
asking what the user wants to build.

Existing records are detected in-workflow through `phase_run query init.onboard`,
which reports whether each record is missing, an unfilled skeleton, or filled.
</context>

<process>
Read and execute `~/.ai/workflows/onboard.md` end to end.

**MANDATORY:** Read the workflow file BEFORE taking any action. The objective and
success criteria here are a summary — the workflow holds the complete step-by-step
process with all required behaviors, runtime calls and interaction patterns. Do not
improvise from the summary.
</process>

<success_criteria>
- Existing code mapped before scoping, where there was any
- Questioning continued until the vision could be written down
- PROJECT.md filled from the user's intent, no placeholders left
- Verification commands configured, or their absence stated plainly
- REQUIREMENTS.md written with REQ ids and an out-of-scope list
- Phases created through the runtime, every REQ id claimed
- STATE.md initialized, everything committed
</success_criteria>
