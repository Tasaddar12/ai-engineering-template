# Captured todos

Ideas, tasks and issues that surfaced mid-session and are not yet scoped into a
phase. [capture](../../.ai/commands/capture.md) writes them; the runtime owns
the filename, frontmatter and the move between states.

| Directory | Holds |
|---|---|
| `pending/` | Captured and not yet acted on. Written by `todo.add` |
| `completed/` | Folded into a phase, a quick task or otherwise resolved. Moved by `todo.complete` |

Each file is `YYYY-MM-DD-slug.md` with `created`, `title`, `area`, `severity`
and `files` frontmatter over `## Problem` and `## Solution` sections. Do not
hand-name files or hand-edit the STATE.md "Pending Todos" section; both are
derived by the runtime from what is on disk.

A todo records that something was noticed. It is not authorization to change
anything: fold it into a phase through [discussion](../../.ai/commands/discuss-phase.md)
or run it as a [quick task](../../.ai/commands/quick.md).

`capture --list` reviews pending todos and routes one into work. See
[phase artifacts](../../.ai/references/phase-artifacts.md) for what a folded-in
todo has to become before anything is built.
