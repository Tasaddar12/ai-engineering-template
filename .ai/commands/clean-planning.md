---
name: clean-planning
description: "Review planning records against current templates and evidence, repair safe structural drift, and archive explicitly selected retired records."
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - Agent
---

<objective>
Make planning records consistent, usable and traceable while preserving project
intent, authored prose, unfinished work and historical decisions. Review is read
only; an authorized cleanup applies the reviewed mechanical repairs and returns
unresolved semantic conflicts with their evidence.
</objective>

<process>
Arguments: `review`, `repair`, or `archive <phase|adr|quick> <selector>`.

Read and execute `~/.ai/workflows/clean-planning.md` end to end before acting.
The workflow owns dispatch, runtime operations, repair and archive safeguards.
</process>
