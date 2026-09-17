# Check 8f — Stated Failing Direction

> Reference file for phase-checker agent. Loaded on-demand via `@` reference.

**Question:** For each runnable `<automated>` command, does the plan say what output constitutes
failure?

Checks 8a–8d ask whether an acceptance command is *present*, and Verify Command Path
Resolvability asks whether its target *resolves*. This one asks whether the command is
**falsifiable at all**. A command with no expressible failure mode is not an acceptance test —
it reads as rigour and delivers none.

A prior failure: a planner emitted 21 `<automated>` commands that could not run. Cargo exited non-zero, so
that instance failed loudly — luck, not design. The same class of error with a command that
exits 0 on a no-op passes green and silently. Requiring a stated failing direction is the only
shape that catches the silent case, because it forces the plan to name the failure signal rather
than assume the command has one.

## The contract

```xml
<verify>
  <automated>npm --prefix apps/api test -- auth.spec.ts</automated>
  <fails_when>non-zero exit, or "0 passed" in the summary line</fails_when>
</verify>
```

Within one `<task>`, each `<fails_when>` binds to the nearest **preceding** `<automated>`; a
command's binding statement is the **first** one that follows it. N runnable commands need N
statements.

## Inspect the stated failure signal

Read each command and its nearest following `<fails_when>` within the same task.
No probe is automatically supplied by this runtime. Inspect presence and content
statically; do not execute plan text during preparation review. For native TDD
feature plans, inspect the behavior and verification sections for the corresponding
assertion/failure signal rather than demanding artificial task wrappers.

## Process — classify the observed statement

| `severity` | `status` | Action |
|---|---|---|
| `blocker` | `missing` | **BLOCKER** — quote the `command` verbatim: it has no stated failing direction |
| `blocker` | `empty` | **BLOCKER** — a `<fails_when>` is present but blank |
| `blocker` | `placeholder` | **BLOCKER** — quote the placeholder text; `TBD` is not a failure signal |
| `warning` | `orphan` | **WARNING** — a `<fails_when>` that follows no command; it satisfies nothing |
| `none` | `ok` / `sentinel` | silent |

Rules:

- **Report, never prescribe.** State which command has no stated failure mode. Do **not** author
  the statement for the planner. A prescribed statement is copied verbatim and carries zero
  information — that can copy an unexamined assertion into the plan.
- `status: sentinel` is a `MISSING — Wave 0 must create …` placeholder command. It is not
  runnable, so it has no failure mode to state. **Not a finding.** Say nothing; checks 8a/8d
  own it.
- A read error means the checker **could not look**. Report that as a WARNING in its own
  words; it is not a clean bill of health.
- **Your added judgment, on `ok` rows only:** a statement that is present, non-empty and
  non-placeholder can still be vacuous — *"the command fails"*, *"it doesn't work"*, *"an error
  occurs"* restate the word "failure" without naming an observable signal. Raise those as a
  **WARNING**, naming what a usable statement looks like (an exit code, a string in the output, a
  missing line). Do **not** escalate a vacuous statement to BLOCKER: missing or empty statements are reproducible structural findings, while
  judgments about prose quality stay advisory.
- **Length is not a signal.** `<fails_when>non-zero exit</fails_when>` is a complete failing
  direction. There is no minimum length, word count, or required keyword.

## Not in scope

A command that runs successfully and asserts nothing (a test-name filter matching zero tests and
exiting 0) is the adjacent **vacuous pass** problem. It is outside this dimension. Report a demonstrated no-op under verification quality.
