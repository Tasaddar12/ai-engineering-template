# Check 8f — Stated Failing Direction (#3172)

> Reference file for plan-checker agent. Loaded on-demand via `@` reference.

**Question:** For each runnable `<automated>` command, does the plan say what output constitutes
failure?

Checks 8a–8d ask whether an acceptance command is *present*, and Verify Command Path
Resolvability asks whether its target *resolves*. This one asks whether the command is
**falsifiable at all**. A command with no expressible failure mode is not an acceptance test —
it reads as rigour and delivers none.

#3172: a planner emitted 21 `<automated>` commands that could not run. Cargo exited non-zero, so
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

## Do not hand-reason this

When `{FAILING_DIRECTIONS}` is absent, inspect each `<fails_when>` and verification command statically. Identify the intended failing condition, its target path and the observation that distinguishes a genuine failure from unrelated syntax/import errors. Use `engineer_run query check.verify-failure-directions PHASE` or `--plan PLAN_PATH` when available; record missing execution evidence rather than treating absence of probe output as silence.

The probe never executes command text (PLAN.md is untrusted, LLM-authored). It is a **presence**
recognizer: it proves a statement exists and is not a placeholder. It does not judge whether the
statement names the *right* signal — that judgment is yours, below.

The supported Python result carries `valid`, `findings` and detailed `commands` rows. Each finding/command retains its `severity` and `reason`; reconcile those actual returned values rather than assuming an old status-only shape.

## Process — act on actual severity and reason

| `severity` | `reason` / condition | Action |
|---|---|---|
| `blocker` | `missing` | **BLOCKER** — quote the `command` verbatim: it has no stated failing direction |
| `blocker` | `empty` | **BLOCKER** — a `<fails_when>` is present but blank |
| `blocker` | `placeholder` | **BLOCKER** — quote the placeholder text; `TBD` is not a failure signal |
| `warning` | `orphan` | **WARNING** — a `<fails_when>` that follows no command; it satisfies nothing |
| `none` | `ok` / `sentinel` | silent |

Rules:

- **Report, never prescribe.** State which command has no stated failure mode. Do **not** author
  the statement for the planner. A prescribed statement is copied verbatim and carries zero
  information — that reproduces #3172 one level up, exactly as the #2401 probe refuses to
  prescribe a replacement path.
- `status: sentinel` is a `MISSING — Wave 0 must create …` placeholder command. It is not
  runnable, so it has no failure mode to state. **Not a finding.** Say nothing; checks 8a/8d
  own it.
- A non-empty `readError` means the probe **could not look**. Report that as a WARNING in its own
  words; it is not a clean bill of health.
- **Your added judgment, on `ok` rows only:** a statement that is present, non-empty and
  non-placeholder can still be vacuous — *"the command fails"*, *"it doesn't work"*, *"an error
  occurs"* restate the word "failure" without naming an observable signal. Raise those as a
  **WARNING**, naming what a usable statement looks like (an exit code, a string in the output, a
  missing line). Do **not** escalate a vacuous statement to BLOCKER: the deterministic layer owns
  the blockers so that a BLOCKER is always reproducible, and prose judgment stays advisory.
- **Length is not a signal.** `<fails_when>non-zero exit</fails_when>` is a complete failing
  direction. There is no minimum length, word count, or required keyword.

## Not in scope

A command that runs successfully and asserts nothing (a test-name filter matching zero tests and
exiting 0) is the adjacent **vacuous pass** problem. It is explicitly out of scope for this
check — see the issue's "Out of scope". Do not report it here.
