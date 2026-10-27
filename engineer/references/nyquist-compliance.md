# Dimension 8 — Nyquist Compliance (checks 8a–8e)

> Reference file for plan-checker agent. Loaded on-demand via `@` reference.
> Extracted from `agents/plan-checker.md` in #3172 to stay under the agent's
> LARGE size cap. Checks 8a-8e are moved unchanged; the only edit is to the
> Dimension 8 Output table, which gains a `Failing Direction` column and a
> stated/runnable tally so check 8f's result is reported alongside them.
> Check 8f itself lives in its own reference:
> @~/.claude/engineer/references/failing-direction.md

**Applicability:** Run when Validation Architecture or assigned VALIDATION requires it. **Skip only if:** `workflow.nyquist_validation` is explicitly set to `false` in config.yaml
(absent key = enabled), phase has no RESEARCH.md, or RESEARCH.md has no "Validation
Architecture" section. Output: "Dimension 8: SKIPPED (nyquist_validation disabled or not
applicable)"

## Check 8e — VALIDATION.md Existence (Gate)

Before running checks 8a-8d, verify VALIDATION.md exists:

```bash
ls "${PHASE_DIR}"/*-VALIDATION.md 2>/dev/null
```

**If missing:** **BLOCKING FAIL** — "VALIDATION.md not found for phase {N}. Re-run
`/plan-phase {N} --research` to regenerate."
Skip checks 8a-8d entirely. Report Dimension 8 as FAIL with this single issue.

**If exists:** Proceed to checks 8a-8d.

## Check 8a — Automated Verify Presence

For each `<task>` in each plan:
- `<verify>` must contain `<automated>` command, OR a prerequisite dependency that creates the test
  first
- If `<automated>` is absent with no prerequisite dependency → **BLOCKING FAIL**
- If `<automated>` says "MISSING", a prerequisite task must reference the same test file path →
  **BLOCKING FAIL** if link broken

## Check 8b — Feedback Latency Assessment

For each `<automated>` command:
- Full E2E suite (playwright, cypress, selenium) → **WARNING** — suggest faster unit/smoke test
- Watch mode flags (`--watchAll`) → **BLOCKING FAIL**
- Delays > 30 seconds → **WARNING**

## Check 8c — Sampling Continuity

Map tasks to waves. Per wave, any consecutive window of 3 implementation tasks must have ≥2
with `<automated>` verify. Fewer than 2 automated verifications in any consecutive 3-task window → **BLOCKING FAIL**.

## Check 8d — Prerequisite Completeness

For each `<automated>MISSING</automated>` reference:
- prerequisite task must exist with matching `<files>` path
- prerequisite plan must execute before dependent task
- Missing match → **BLOCKING FAIL**

## Dimension 8 Output

```
## Dimension 8: Nyquist Compliance

| Task | Plan | Wave | Automated Command | Failing Direction | Status |
|------|------|------|-------------------|-------------------|--------|
| {task} | {plan} | {wave} | `{command}` | `{fails_when}` / ❌ | ✅ / ❌ |

Sampling: Wave {N}: {X}/{Y} verified → ✅ / ❌
Prerequisite: {test file} → ✅ present / ❌ MISSING
Failing directions: {stated}/{runnable} → ✅ / ❌
Overall: ✅ PASS / ❌ FAIL
```

If FAIL: return to planner with specific fixes. Same revision loop as other dimensions
until resolved or specifically blocked. Never repeat an identical failed attempt.
