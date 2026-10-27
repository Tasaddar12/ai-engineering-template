---
name: code-review
description: Review exact source scope and optionally repair grounded findings
argument-hint: "<phase> [--plan NN-MM] [--depth quick|standard|deep] [--files PATH,...] [--pathspec PATH...] [--max-commits N] [--commits-only] [--fix [--all] [--auto]]"
allowed-tools: [Read, Bash, Glob, Grep, Write, Agent]
requires: [phase, quick]
---

<arguments>$ARGUMENTS</arguments>

Arguments are user data, never instructions to evaluate as shell code.

<objective>
Review bugs, security and maintainability in an exact phase or genuine quick
scope. The independent read-only code-reviewer returns a complete report; the
coordinator captures it and authors durable REVIEW.md on the owning session.

- Positional phase or --phase N identifies the phase. --quick ID selects a real
  existing quick record instead; never fabricate a phase for quick work.
- --plan NN-MM (or --phase NN --plan MM) narrows commit evaluation to that plan.
- --files PATH,... overrides automatic discovery. Preserve quoted spaces, reject
  empty entries and resolve all paths inside the repository.
- --pathspec PATH... filters actual runtime commit/file scope; conflicts with
  --files and never authorizes writes.
- --max-commits N bounds history inspection; N must be a positive integer.
- --commits-only reports selected SHAs and stops before record mutation or agent
  dispatch. It conflicts with --files and repair flags.
- --depth quick|standard|deep overrides workflow.code_review_depth, otherwise
  standard. Quick scans patterns; standard reads each scoped file and imports;
  deep additionally traces call chains, contracts, error propagation and state.
- --fix authorizes Critical and Warning repairs; --all includes Info; --auto
  permits at most three repair passes. Both imply --fix. Each grounded finding
  gets one isolated targeted-fixer assignment per pass, its own repair commit
  and required repair SUMMARY. code-fixer supplies methods only.

Output includes exact scope/base/head, full report, counts and limitations; repair
adds aggregate REVIEW-FIX.md and per-finding evidence. Review alone never grants
implementation, provider-write or merge authority.
</objective>

<execution_context>
@engineer/workflows/code-review.md
</execution_context>

<process>
Execute the workflow end-to-end. It owns parsing, identity validation before the
configuration gate, session lineage, scope, reviewer dispatch, capture and repair
routing. Report-only and commits-only requests remain read-only.
</process>
