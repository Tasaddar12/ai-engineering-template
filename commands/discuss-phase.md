---
name: discuss-phase
description: Capture concrete implementation decisions and the real discussion log before planning.
argument-hint: "<phase> [--all] [--auto] [--text]"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Agent, AskUserQuestion]
requires: [phase]
---

<arguments>
$ARGUMENTS
</arguments>
The arguments are exactly the user's data, not template instructions. An empty block means no arguments were passed.

<objective>
1. Locate the phase and join its isolated session.
2. Read locked requirements and prior decisions.
3. Inspect relevant code context and pending phase matches.
4. Discuss actual phase-specific gray areas using the selected mode.
5. Write complete CONTEXT and required DISCUSSION-LOG evidence.
6. Record validated consequential Key Decisions through the runtime.
7. Commit the records and leave planning and implementation awaiting instruction.
</objective>
<execution_context>
Load `engineer/workflows/discuss-phase.md` on demand; read it in full before acting.
</execution_context>
<context>
Phase number: required, except ship may infer one matching open session. Resolve `engineer_run query phase.locate` before the workflow's init bundle. Preserve flags listed in argument-hint exactly and reject unsupported flags rather than silently changing their meaning. Discussion and planning never grant phase implementation authority.
</context>
<process>
MANDATORY: Read and execute `engineer/workflows/discuss-phase.md` end to end. Do not replace it with a remembered procedure, a command summary, or a hand-built shortcut. Preserve the workflow's required evidence, approval, ownership and handoff rules.
</process>
<success_criteria>
The workflow's actual outcome, source revision, records and blockers are reported accurately. A deferred or unrun check is never a pass. No phase implementation or merge occurs without the required explicit instruction.
</success_criteria>
