---
name: capture
description: "Capture an idea, task or issue as a structured todo, or list and act on pending todos with --list."
argument-hint: "<description> | --list [area]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

<objective>
Keep a thought without losing the thread of the current work.

Mode routing:
- **default**: capture a new todo -> add-todo workflow
- **--list [area]**: list pending todos, load one and act on it -> check-todos workflow

<routing>

| Flag | Action | Workflow |
|------|--------|----------|
| (none) | Capture a new todo | add-todo |
| --list | Review pending todos and route one | check-todos |

</routing>

**Output:** `.planning/todos/pending/{date}-{slug}.md`, and a refreshed STATE.md section.
</objective>

<execution_context>
@~/.ai/workflows/add-todo.md
@~/.ai/workflows/check-todos.md
</execution_context>

<context>
Arguments: $ARGUMENTS
Parse the first token of $ARGUMENTS:
- `--list`: strip the flag, pass the remainder (an optional area filter) to check-todos
- otherwise: pass all of $ARGUMENTS as the todo title to add-todo. With no arguments,
  add-todo extracts the todo from the recent conversation.

Todo state is resolved in-workflow through `phase_run query init.todos`.
</context>

<process>
1. Parse the leading flag, if any, from $ARGUMENTS.
2. Read and execute the matching workflow end to end.

**MANDATORY:** Read the workflow file BEFORE taking any action. The objective and
success criteria here are a summary — the workflow holds the complete step-by-step
process with all required behaviors, runtime calls and interaction patterns. Do not
improvise from the summary.
</process>

<success_criteria>
- Todo written by the runtime with valid frontmatter
- Severity confirmed with the user, never silently assigned
- Duplicates checked and resolved
- STATE.md pending todos refreshed from disk
- Change committed
</success_criteria>
