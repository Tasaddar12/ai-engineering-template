---
name: plan-phase
description: Research when warranted, prepare executable plans and independently verify their goal coverage.
argument-hint: "<phase> [--skip-research] [--research] [--gaps] [--text] [--force]"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Agent, AskUserQuestion]
requires: [discuss-phase, phase]
---

<arguments>
$ARGUMENTS
</arguments>
The arguments are exactly the user's data, not template instructions. An empty block means no arguments were passed.

<objective>
1. Locate the phase and join its session.
2. Require discussion and refresh relevant codebase maps.
3. Dispatch bounded research only when warranted.
4. Dispatch planner with complete context, evidence and explicit contracts.
5. Run an independent goal-backward plan review and bounded corrections.
6. Reconcile runtime-owned roadmap/state with checked plans and report that implementation awaits an explicit instruction.
</objective>
<execution_context>
Load `engineer/workflows/plan-phase.md` on demand; read it in full before acting.
</execution_context>
<context>
Phase number: required, except ship may infer one matching open session. Resolve `engineer_run query phase.locate` before the workflow's init bundle. Preserve flags listed in argument-hint exactly and reject unsupported flags rather than silently changing their meaning. Discussion and planning never grant phase implementation authority.
</context>
<process>
MANDATORY: Read and execute `engineer/workflows/plan-phase.md` end to end. Do not replace it with a remembered procedure, a command summary, or a hand-built shortcut. Preserve the workflow's required evidence, approval, ownership and handoff rules.
</process>
<success_criteria>
The workflow's actual outcome, source revision, records and blockers are reported accurately. A deferred or unrun check is never a pass. No phase implementation or merge occurs without the required explicit instruction.
</success_criteria>
