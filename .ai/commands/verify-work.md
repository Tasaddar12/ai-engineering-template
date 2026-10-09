---
name: verify-work
description: "Verify a phase delivered its goal through goal-backward analysis of the codebase, then close or record gaps."
argument-hint: "<phase>"
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
Establish what is actually true after a phase executed.

**How it works:**

1. Scan the phase's plans and summaries, reporting visible mismatches first
2. Start configured checks, applicable read-only specialists and a provisional
   verifier together against one frozen revision, using valid receipts
3. Join the results and resume the verifier to reconcile bounded shared evidence
4. On a provisional pass, validate the bounded success-record transition and
   revalidate only evidence whose inputs changed
5. Persist the final external verifier report through the coordinator as the
   final local write; close gaps and re-verify when needed
6. Close the phase's requirements in REQUIREMENTS.md only in the one-time
   success-bookkeeping step for a pass

**Output:** `{phase}-VERIFICATION.md` with status, the exact revision examined
by the final verifier, and findings.

Task completion is a claim. Verification is evidence.
</objective>

<execution_context>
Workflow files are loaded on demand in the <process> section below - not upfront.
</execution_context>

<context>
Arguments: $ARGUMENTS
Phase number: $ARGUMENTS (required).

Phase number: $ARGUMENTS (required).
The phase is located with `phase_run query phase.locate` before the workflow loads
`phase_run query init.verify-work` for the selected worktree.
</context>

<process>
Read and execute `~/.ai/workflows/verify-work.md` end to end.

**MANDATORY:** Read the workflow file BEFORE taking any action. The objective and
success criteria here are a summary — the workflow holds the complete step-by-step
process with all required behaviors, runtime calls and interaction patterns. Do not
improvise from the summary.
</process>

<success_criteria>
- Existing verification currentness checked using the exact revision or the
  bounded report-only publication rule
- Configured checks run and passed to the verifier as evidence
- Initial checks and independent specialists join before their evidence is
  reconciled; the verifier judges the codebase, not the summaries
- On a provisional pass, bookkeeping passes deterministic schema/transition
  validation before the report is persisted; any semantic delta gets bounded review
- Unconfirmable criteria abstained rather than passed
- Gaps closed and re-verified, or recorded as todos with the user's agreement
- Roadmap and STATE.md updated only on a pass or an explicit acceptance
- Requirements closed in the Traceability table on a pass, never on recorded gaps
- Record drift reported, warn-only, without blocking the verification
</success_criteria>
