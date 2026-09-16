# Dimension 8 — Nyquist Compliance (checks 8a–8e)

Use to review feedback quality when the phase has a Validation Architecture in
its research or an explicitly assigned VALIDATION artifact. The Python runtime
has no nyquist feature switch and does not enforce this entire review method.
If neither applies, mark this detailed dimension not applicable; still inspect
required PLAN checks under the local contract. See [failing-direction](failing-direction.md).

## Check 8e — VALIDATION.md Existence (Gate)

Before running checks 8a-8d, verify VALIDATION.md exists:

```bash
ls "${PHASE_DIR}"/*-VALIDATION.md 2>/dev/null
```

**If missing:** **BLOCKING FAIL** — "VALIDATION.md not found for phase {N}. Return the missing assigned artifact to the coordinator/preparer."
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
with `<automated>` verify. 3 consecutive without → **BLOCKING FAIL**.

## Check 8d — prerequisite Completeness

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
prerequisite: {test file} → ✅ present / ❌ MISSING
Failing directions: {stated}/{runnable} → ✅ / ❌
Overall: ✅ PASS / ❌ FAIL
```

If FAIL: return to planner with specific fixes. Same revision loop as other dimensions
until resolved or a concrete blocker requires a decision.
