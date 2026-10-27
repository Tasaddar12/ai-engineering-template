# Verifier Phase Gates

> Loaded eagerly by `agents/verifier.md` (`<required_reading>`). Carries the three
> verification-time gates that lived in the retired `verify-phase` workflow
> (#1892 / epic #1891 F7): decision-coverage validation (#2492), the test-quality audit,
> and infrastructure-phase human-verification scoping (#2504) — plus the backstop-abstention
> reporting contract (#3206). Run each gate at its named
> agent step; `engineer_run` is the launcher shim defined in the agent's own Step 1 block.

## Decision Coverage

Read the phase's trackable CONTEXT decisions and PROJECT Key Decisions that constrain the outcome. Run the supported gate:

```bash
engineer_run query check.decision-coverage-verify "$PHASE" --dir "$PHASE_DIR"
```

The result contains `passed`, `decisions`, `uncovered` and `files`; uncovered IDs exit nonzero. A command failure is not "no decisions". Inspect each uncovered decision semantically against the delivered artifacts and behavioral evidence. Record a Decision Coverage table with exact ID, owning source, delivered obligation, evidence and disposition.

The verifier cannot abandon a decision, defer scope or fill missing evidence with a substring match. Return an evidenced violation or a specific missing check to the coordinator. If the decision changed legitimately, the coordinator reconciles its owning record; optional ADR rationale does not supersede PROJECT ownership.

## audit_test_quality (run after Step 7b, alongside anti-patterns)

<step name="audit_test_quality">
**Verify that tests PROVE what they claim to prove.**

This step catches test-level deceptions that pass all prior checks: files exist, are substantive, are wired, and tests pass — but the tests don't actually validate the requirement.

**1. Identify requirement-linked test files**

From PLAN and SUMMARY files, map each requirement to the test files that are supposed to prove it.

**2. Disabled test scan**

For ALL test files linked to requirements, search for disabled/skipped patterns:

```bash
grep -rn -E "it\.skip|describe\.skip|test\.skip|xit\(|xdescribe\(|xtest\(|@pytest\.mark\.skip|@unittest\.skip|#\[ignore\]|\.pending|it\.todo|test\.todo" "$TEST_FILE"
```

**Rule:** A disabled test linked to a requirement = requirement NOT tested.
- 🛑 BLOCKER if the disabled test is the only test proving that requirement
- ⚠️ WARNING if other active tests also cover the requirement

**3. Circular test detection**

Search for scripts/utilities that generate expected values by running the system under test:

```bash
grep -rn -E "writeFileSync|writeFile|fs\.write|open\(.*w\)" "$TEST_DIRS"
```

For each match, check if it also imports the system/service/module being tested. If a script both imports the system-under-test AND writes expected output values → CIRCULAR.

**Circular test indicators:**
- Script imports a service AND writes to fixture files
- Expected values have comments like "computed from engine", "captured from baseline"
- Script filename contains "capture", "baseline", "generate", "snapshot" in test context
- Expected values were added in the same commit as the test assertions

Record exact test-quality evidence and limitations; no source-presence check substitutes for exercising the claimed behavior.

**4. Expected value provenance** (for comparison/parity/migration requirements)

When a requirement demands comparison with an external source ("identical to X", "matches Y", "same output as Z"):

- Is the external source actually invoked or referenced in the test pipeline?
- Do fixture files contain data sourced from the external system?
- Or do all expected values come from the new system itself or from mathematical formulas?

**Provenance classification:**
- VALID: Expected value from external/legacy system output, manual capture, or independent oracle
- PARTIAL: Expected value from mathematical derivation (proves formula, not system match)
- CIRCULAR: Expected value from the system being tested
- UNKNOWN: No provenance information — treat as SUSPECT

**5. Assertion strength**

For each test linked to a requirement, classify the strongest assertion:

| Level | Examples | Proves |
|-------|---------|--------|
| Existence | `toBeDefined()`, `!= null` | Something returned |
| Type | `typeof x === 'number'` | Correct shape |
| Status | `code === 200` | No error |
| Value | `toEqual(expected)`, `toBeCloseTo(x)` | Specific value |
| Behavioral | Multi-step workflow assertions | End-to-end correctness |

If a requirement demands value-level or behavioral-level proof and the test only has existence/type/status assertions → INSUFFICIENT.

**6. Coverage quantity**

If a requirement specifies a quantity of test cases (e.g., "30 calculations"), check if the actual number of active (non-skipped) test cases meets the requirement.

**Reporting — add to VERIFICATION.md:**

```markdown
### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|

**Disabled tests on requirements:** {N} → {BLOCKER if any req has ONLY disabled tests}
**Circular patterns detected:** {N} → {BLOCKER if any}
**Insufficient assertions:** {N} → {WARNING}
```

**Impact on status:** Any BLOCKER from test quality audit → overall status = `gaps_found` (Step 9 rule 1), regardless of other checks passing.
</step>

## identify_human_verification — infrastructure/foundation scoping (apply at Step 8)

**First: determine if this is an infrastructure/foundation phase.**

Infrastructure and foundation phases — code foundations, database schema, internal APIs, data models, build tooling, CI/CD, internal service integrations — have no user-facing elements by definition. For these phases:

- Do NOT invent artificial manual steps (e.g., "manually run git commits", "manually invoke methods", "manually check database state").
- Mark human verification as **N/A** with rationale: "Infrastructure/foundation phase — no user-facing elements to test manually."
- Set `human_verification: []` and do **not** produce a `human_needed` status solely due to lack of user-facing features.
- Only add human verification items if the phase goal or success criteria explicitly describe something a user would interact with (UI, CLI command output visible to end users, external service UX).
Apply human-verification scoping to actual acceptance obligations and delivered entry points, not a phase label.

**How to determine if a phase is infrastructure/foundation:**
- Phase goal or name contains: "foundation", "infrastructure", "schema", "database", "internal API", "data model", "scaffolding", "pipeline", "tooling", "CI", "migrations", "service layer", "backend", "core library"
- Phase success criteria describe only technical artifacts (files exist, tests pass, schema is valid) with no user interaction required
- There is no UI, CLI output visible to end users, or real-time behavior to observe

**Infrastructure/foundation phases:** do not invent UX checks when there is no user-facing behavior. Record the actual applicable automated acceptance evidence. Required human judgment, PRESENT_BEHAVIOR_UNVERIFIED and insufficient_spec remain pending regardless of infrastructure framing. "No UI" is an applicability statement, never an automatic UAT pass.

**If the phase IS user-facing:** only flag items that genuinely require a human — per the Step 8 always/uncertain lists already in the agent. Do not invent steps.

## Backstop abstention and supporting references

A `verification: backstop` truth without explicit behavioral evidence routes to `human_needed` with `reason: insufficient_spec` in every mode. An unattended run preserves the prominent unverified item and pending acceptance; it never reports a passing obligation because no human is present.

Read [honest verifier](honest-verifier.md) for normalization and incidental-success handling, [verification evidence](verification-evidence.md) for frozen revision/receipt rules, [verification patterns](verification-patterns.md) for stack-specific discovery and [the complete report template](../templates/verification-report.md) before writing the report. These methods do not waive required acceptance.
