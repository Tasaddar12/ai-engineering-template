---
name: milestone-summary
description: "Generate a human-readable summary of a milestone from its phase artifacts, written for onboarding."
argument-hint: "[milestone-version] [--write]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
---

<objective>
Explain a milestone to someone who was not there.

**How it works:**

1. Resolve the milestone from the argument, the current one, or the newest shipped
2. Read its phase contexts, summaries and verification reports
3. Compose a summary that leads with the delivered capability, not with process
4. Report verification honestly, including known gaps

**Output:** the summary in the response, and on disk with `--write`.
</objective>

<execution_context>
Workflow files are loaded on demand in the <process> section below - not upfront.
</execution_context>

<context>
Arguments: $ARGUMENTS
Milestone version: $ARGUMENTS (optional).

Milestone membership is resolved in-workflow through `phase_run query milestone.list`
and `phase_run query init.complete-milestone`.
</context>

<process>
Read and execute `~/.ai/workflows/milestone-summary.md` end to end.

**MANDATORY:** Read the workflow file BEFORE taking any action. The objective and
success criteria here are a summary — the workflow holds the complete step-by-step
process with all required behaviors, runtime calls and interaction patterns. Do not
improvise from the summary.
</process>

<success_criteria>
- Milestone resolved and its artifacts read
- Delivered capability explained in plain language
- Key decisions traced to where they show up in the code
- Verification and known gaps reported honestly
- Written and committed when --write was passed
</success_criteria>
