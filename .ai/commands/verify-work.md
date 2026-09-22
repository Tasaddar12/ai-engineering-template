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
2. Run the project's configured checks as evidence
3. Spawn a fresh verifier to judge the codebase against the phase goal
4. Check integration and documentation where they apply
5. Close gaps and re-verify, or record them with the user's agreement
6. Close the phase's requirements in REQUIREMENTS.md when the status is a pass
6. Close the phase's requirements in REQUIREMENTS.md when the status is a pass

**Output:** `{phase}-VERIFICATION.md` with status, revision and findings.

Task completion is a claim. Verification is evidence.
</objective>

<execution_context>
Workflow files are loaded on demand in the <process> section below - not upfront.
</execution_context>

<context>
Arguments: $ARGUMENTS
Phase number: $ARGUMENTS (required).

Verification status, checks and models are resolved in-workflow through
`phase_run query init.verify-work`.
</context>

<process>
Read and execute `~/.ai/workflows/verify-work.md` end to end.

**MANDATORY:** Read the workflow file BEFORE taking any action. The objective and
success criteria here are a summary — the workflow holds the complete step-by-step
process with all required behaviors, runtime calls and interaction patterns. Do not
improvise from the summary.
</process>

<success_criteria>
- Existing verification checked for staleness against the current revision
- Configured checks run and passed to the verifier as evidence
- A fresh verifier judged the codebase, not the summaries
- Unconfirmable criteria abstained rather than passed
- Gaps closed and re-verified, or recorded as todos with the user's agreement
- Roadmap and STATE.md updated only on a pass or an explicit acceptance
- Requirements closed in the Traceability table on a pass, never on recorded gaps
- Record drift reported, warn-only, without blocking the verification
- Requirements closed in the Traceability table on a pass, never on recorded gaps
- Record drift reported, warn-only, without blocking the verification
</success_criteria>
