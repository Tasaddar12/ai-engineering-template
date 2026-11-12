# Coding standards — task-scoped reading

> Required before planning, implementing, fixing, investigating, verifying or
> reviewing code. Start at the [standards index](../standards/README.md).
> Standards files are references, not skills — never register or invoke them as skills.

## What to read

Read only the files matching the task's language, framework and design concerns.
Domains may combine; unrelated languages and topics are not required reading.
Apply the selected references within the assigned scope and project instructions.

| Step | Read |
|---|---|
| 1 | [Standards index](../standards/README.md) — pick the domains |
| 2 | Matching routing sections of each domain index — use its heading outline to skip unrelated tables |
| 3 | Only the sections those rows select, using the bounded reads below |

## Bounded reads

1. **Pick targets.** Choose a routing ID and the applicable targets in its row.
   IDs are stable reading aliases, not runtime queries. A row listing several
   sections is a menu, not a checklist: a link plus §N or named-child selectors
   offers alternatives within that document. Read focused rules marked **whole**
   completely — instructions, bad/good examples and notes.
2. **Find the boundary.** Resolve the actual heading text and level with a
   heading-only search or outline — do not load the whole document to find it.
   Ignore apparent headings inside fenced code examples.
3. **Read the range.** Use the file reader's offset/limit or a shell line range
   from the current file: the selected heading through the line before the next
   actual heading of equal or higher level, or EOF. Keep nested subsections and
   complete examples. An anchor alone does not bound a read.
4. **Add context.** Include document applicability and enclosing introductory
   rules needed to interpret the selection. Follow prerequisite or reference
   sections when the task needs their instructions. Expand when new concerns
   arise; never truncate instructions to meet a token target.
5. **Reuse.** Don't re-read sections already current in your context; merge
   overlapping reads. Record routing IDs in handoffs rather than copying whole
   standards into every prompt. Each independent agent reads its own applicable
   sections.

Line offsets are found at read time, never stored in indexes.

## Gaps and conflicts

- Missing or ambiguous heading → report a routing gap; do not silently read an
  unrelated document whole.
- No coverage, or a conflict with an explicit project decision → report it; do
  not invent a standard.
