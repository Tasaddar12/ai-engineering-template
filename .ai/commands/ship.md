---
name: ship
description: "Publish verified phase work as a pull request - gated on current verification, a clean tree and valid passing check evidence."
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

1. Confirm the phase's verification is `passed` and current under the documented
   exact-revision or validated bounded-transition currentness rule
2. Check the tree is clean, the branch is not the base, and gh is available
3. Commit the truthful pre-publication session status
4. Validate the bounded publication-record transition and revalidate only
   evidence whose inputs changed
5. Compose the PR body from the phase's summaries and current verification report
6. Push and open or update the pull request
7. Wait for its checks with `pr.checks --wait`; fix failing checks and re-verify
   source repairs before another push
8. Ask the merge question; merge, sync the base branch and close the session only
   on the user's instruction

**Output:** a pushed branch and pull request; the preparation status is committed
in STATE.md and the actual PR URL is recorded in session metadata. Merge only on
the user's instruction.

No bypass for unverified work.
</objective>

<execution_context>
Workflow files are loaded on demand in the <process> section below - not upfront.
</execution_context>

<context>
Arguments: $ARGUMENTS
Phase number: $ARGUMENTS (optional; defaults to the current phase).

An omitted phase is inferred only from exactly one open phase session. The phase
is validated with `phase_run query phase.locate` before `phase_run query init.ship`
loads the selected worktree.
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
- Configured checks have valid passing evidence for the shipped inputs
- PR body composed from the phase's own records
- Branch pushed, PR opened or updated
- Check state reported as observed, never assumed
- Merge question asked; merged only on the user's instruction
- Truthful pre-publication status committed and its bounded transition validated
- Actual PR URL recorded by `pr.open` in session metadata; no stale post-push commit
</success_criteria>
