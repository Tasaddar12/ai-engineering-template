---
name: ship
description: "Publish verified phase work as a pull request - gated on passing verification, a clean tree and passing checks."
argument-hint: "[phase] [--draft] [--review] [--no-push]"
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
Publish work that verification actually passed.

**How it works:**

1. Confirm the phase's verification is `passed` and current for this revision
2. Check the tree is clean, the branch is not the base, and gh is available
3. Run the project's configured checks
4. Compose the PR body from the phase's summaries and verification report
5. Push and open or update the pull request

**Output:** a pushed branch and a pull request, recorded in STATE.md.

Shipping publishes. It does not merge, it does not move the base branch, and it
has no bypass for unverified work.
</objective>

<execution_context>
Workflow files are loaded on demand in the <process> section below - not upfront.
</execution_context>

<context>
Arguments: $ARGUMENTS
Phase number: $ARGUMENTS (optional; defaults to the current phase).

Verification status, check configuration and git state are resolved in-workflow
through `phase_run query init.ship`.
</context>

<process>
Read and execute `~/.ai/workflows/ship.md` end to end.

**MANDATORY:** Read the workflow file BEFORE taking any action. The objective and
success criteria here are a summary — the workflow holds the complete step-by-step
process with all required behaviors, runtime calls and interaction patterns. Do not
improvise from the summary.
</process>

<success_criteria>
- Verification confirmed passed and current for the shipped revision
- Working tree clean, branch not the base, remote and gh available
- Configured checks run and passing
- PR body composed from the phase's own records
- Branch pushed, PR opened or updated
- Check state reported as observed, never assumed
- Publication recorded in STATE.md and committed
</success_criteria>
