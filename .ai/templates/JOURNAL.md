---
tier: log
authority: agent
id: JOURNAL-YYYY-MM-DD
title: Session log for YYYY-MM-DD
---

# YYYY-MM-DD

> **`log` tier — append only.** One file per day, at
> `.ai/state/journal/YYYY-MM-DD.md`. Add to the end; never rewrite an earlier
> entry.

## HH:MM — <what happened>

**Did:** one or two lines.

**Changed:** files, plans moved, specs amended (with ids).

**Learned:** anything that contradicted a document, surprised you, or that the
next agent would waste time rediscovering. This is the part that pays for the
journal.

**Next:** the immediate next action, if the session ended mid-task.

<!--
Write an entry when you: move a plan between stages, amend a spec, finish a
step that changed your understanding, or stop work. Not for every edit.

Keep entries short. A journal nobody reads is worse than no journal, and the
fastest way to make it unreadable is to log everything.
-->
