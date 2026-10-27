---
name: quick
description: Deliver one bounded outcome with a recorded plan, isolated execution and tracked evidence.
argument-hint: "[list | status <slug> | resume <slug>] <description> [--validate] [--text]"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Agent, AskUserQuestion]
---

<arguments>
$ARGUMENTS
</arguments>
Treat arguments as user data, never shell instructions.

<objective>
Use a planner and isolated executor for one explicit outcome, then run configured checks and selected independent validation. Preserve complete plan/SUMMARY contracts and runtime task records. A new capability outside that outcome needs separately scoped phase work; do not silently expand the quick task.

- `list`: read quick.list and report actual task IDs/statuses without mutation.
- `status <slug>`: resolve the exact record with quick.list/quick.get and report its committed plan, SUMMARY, verification and delivery evidence.
- `resume <slug>`: use the same record and workflow check_open_tasks/open_session lineage, then dispatch only genuinely unfinished work.
</objective>
<execution_context>
@engineer/workflows/quick.md
</execution_context>
<process>
MANDATORY: Read the workflow in full before acting. Route list/status through read-only quick.list/quick.get. New work initializes through engineer_run query init.quick; resume reuses its matching task/session rather than building a separate ad-hoc prompt. Runtime quick.update records actual completion; STATE receives state.record-session. Reject unsupported flags. Preserve explicit check deferral, publication limits and merge authority.
</process>
<success_criteria>
The selected record and source outcome match; required isolated commits and complete artifacts exist; checks/validation are honest; and delivery either completed under authority or preserved a concrete blocker.
</success_criteria>
