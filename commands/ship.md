---
name: ship
description: Publish verified phase-session work and merge only with explicit user authorization.
argument-hint: "[phase] [--draft] [--review] [--no-push] [--no-merge]"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Agent, AskUserQuestion]
requires: [verify-work]
---

<arguments>
$ARGUMENTS
</arguments>
The arguments are exactly the user's data, not template instructions. An empty block means no arguments were passed.

<objective>
1. Resolve the existing phase session; infer a phase only from one unambiguous open session.
2. Require ready handoff, passed current verification, closed threats and a clean session.
3. Reuse valid check receipts and optionally request independent review.
4. Prepare the full canonical PR template and provider-confirmed issue links.
5. Push the session branch without force and open or update its draft PR.
6. Refresh the independent issue-link audit against the actual published head/body.
7. Wait for checks, repair authorized failures and re-verify changed source.
8. Merge and close the session only on an explicit instruction; --no-merge leaves the PR open.
</objective>
<execution_context>
Load `engineer/workflows/ship.md` on demand; read it in full before acting.
</execution_context>
<context>
Phase number: required, except ship may infer one matching open session. Resolve `engineer_run query phase.locate` before the workflow's init bundle. Preserve flags listed in argument-hint exactly and reject unsupported flags rather than silently changing their meaning. Discussion and planning never grant phase implementation authority.
</context>
<process>
MANDATORY: Read and execute `engineer/workflows/ship.md` end to end. Do not replace it with a remembered procedure, a command summary, or a hand-built shortcut. Preserve the workflow's required evidence, approval, ownership and handoff rules.
</process>
<success_criteria>
The workflow's actual outcome, source revision, records and blockers are reported accurately. A deferred or unrun check is never a pass. No phase implementation or merge occurs without the required explicit instruction.
</success_criteria>
