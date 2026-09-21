---
name: complete-milestone
description: "Close a milestone - audit its phases, record what shipped in MILESTONES.md, and mark it shipped."
argument-hint: "[milestone-version]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

<objective>
Close out a milestone with an honest record of what shipped.

**How it works:**

1. Audit every phase in the milestone for missing plans, summaries and verification
2. Refuse to close while phases are still open - there is no force path
3. Gather stats and the delivered lines from each phase SUMMARY.md
4. Write the MILESTONES.md entry and mark the milestone shipped in the roadmap

**Output:** a MILESTONES.md entry, and a roadmap that shows the milestone shipped.
</objective>

<execution_context>
Workflow files are loaded on demand in the <process> section below - not upfront.
</execution_context>

<context>
Arguments: $ARGUMENTS
Milestone version: $ARGUMENTS (optional; defaults to the milestone in progress).

Milestone membership and readiness are resolved in-workflow through
`phase_run query init.complete-milestone`.
</context>

<process>
Read and execute `~/.ai/workflows/complete-milestone.md` end to end.

**MANDATORY:** Read the workflow file BEFORE taking any action. The objective and
success criteria here are a summary — the workflow holds the complete step-by-step
process with all required behaviors, runtime calls and interaction patterns. Do not
improvise from the summary.
</process>

<success_criteria>
- Artifact audit run and gaps reported before closing
- Every phase in the milestone confirmed complete
- MILESTONES.md entry written by the runtime and its prose reviewed
- No accomplishment claimed that no SUMMARY.md supports
- Roadmap shows the milestone shipped, STATE.md updated and committed
</success_criteria>
