---
name: new-milestone
description: "Start a new milestone cycle - gather the goal, scope requirements, and break it into phases."
argument-hint: "<milestone-name>"
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
Open the next milestone on an existing project.

**How it works:**

1. Check for unfinished phases in the current milestone before opening another
2. Establish with the user what this milestone delivers, and what it does not
3. Research the approach only where it is genuinely unknown
4. Add requirements with continuing REQ ids and an explicit out-of-scope list
5. Declare the milestone and add its phases through the runtime

**Output:** a milestone section in ROADMAP.md with its phases, and updated requirements.
</objective>

<execution_context>
Workflow files are loaded on demand in the <process> section below - not upfront.
</execution_context>

<context>
Arguments: $ARGUMENTS
Milestone name: $ARGUMENTS.

Current milestone, open phases and models are resolved in-workflow through
`phase_run query init.new-milestone`.
</context>

<process>
Read and execute `~/.ai/workflows/new-milestone.md` end to end.

**MANDATORY:** Read the workflow file BEFORE taking any action. The objective and
success criteria here are a summary — the workflow holds the complete step-by-step
process with all required behaviors, runtime calls and interaction patterns. Do not
improvise from the summary.
</process>

<success_criteria>
- Open phases in the current milestone surfaced before starting a new one
- Milestone goal concrete enough to decompose into phases
- Requirements added with continuing ids and an out-of-scope list
- Milestone and phases created through the runtime, numbering continuous
- STATE.md pointed at the first phase, everything committed
</success_criteria>
