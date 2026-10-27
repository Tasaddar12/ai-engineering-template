---
name: execute-phase
description: Implement an explicitly authorized phase in isolated dependency waves, verify it and carry it through publication.
argument-hint: "<phase> [--plan <id>] [--wave <n>] [--sequential] [--resume] [--no-review]"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Agent, AskUserQuestion]
requires: [phase, verify-work, ship]
---

<arguments>
$ARGUMENTS
</arguments>
The arguments are exactly the user's data, not template instructions. An empty block means no arguments were passed.

<objective>
1. Require explicit implementation authority recorded in CONTEXT.
2. Join the phase session and select unfinished plans.
3. With --wave N select only that eligible effective wave and require delivered predecessors; retain all unselected work as incomplete. Run every selected plan as an isolated executor with exact ownership and deletion declarations.
4. Integrate committed worker slices through runtime merge guards.
5. Run configured receipt-based checks and independent review.
6. Reconcile issues and shared records, then run verify-work and authorized ship in the same session.
</objective>
<execution_context>
Load `engineer/workflows/execute-phase.md` on demand; read it in full before acting.
</execution_context>
<context>
Phase number: required, except ship may infer one matching open session. Resolve `engineer_run query phase.locate` before the workflow's init bundle. Preserve flags listed in argument-hint exactly and reject unsupported flags rather than silently changing their meaning. Discussion and planning never grant phase implementation authority.
</context>
<process>
MANDATORY: Read and execute `engineer/workflows/execute-phase.md` end to end. Do not replace it with a remembered procedure, a command summary, or a hand-built shortcut. Preserve the workflow's required evidence, approval, ownership and handoff rules.
</process>
<success_criteria>
The workflow's actual outcome, source revision, records and blockers are reported accurately. A deferred or unrun check is never a pass. No phase implementation or merge occurs without the required explicit instruction.
</success_criteria>
