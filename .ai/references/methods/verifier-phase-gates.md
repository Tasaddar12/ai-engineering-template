# Verifier Phase Gates

These manual review gates support the local verifier; they do not require an
external command dispatcher. Follow the actual assignment and user execution
limits. An instruction to defer tests means inspect their design only and record
that execution evidence remains pending.

## verify_decisions — Decision Coverage (after requirements coverage)

Read each material decision from phase CONTEXT. Map it to PLAN ownership, current
source, documentation and evidence. Record a Decision Coverage section listing
honored, missing, ambiguous and explicitly superseded decisions with references.
A substring match in a summary or commit message is a discovery hint, not proof.
A wording mismatch alone is advisory; evidence that an approved required decision
was not implemented remains a gap. The local runtime has no toggle or SDK handler
for this review, and it cannot silently weaken acceptance.

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

**Rule:** A test comparing output against automatically regenerated values from the same system is circular as correctness evidence. A reviewed, fixed regression baseline may prove stability, but cannot alone prove an external parity requirement.

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
- **Exception — behavior-unverified truths still count.** A truth marked ⚠️ PRESENT_BEHAVIOR_UNVERIFIED (a state transition or a cancellation/cleanup/ordering invariant with no test exercising it) is a behavioral-evidence gap, not an artificial user-facing step. Record it in `behavior_unverified_items` and emit a human-verification item for it **even on an infrastructure/foundation phase** — these invariants are exactly where infra phases hide runtime state leaks. Such a truth drives `human_needed`; the absence-of-UX rationale applies only to the absence of user-facing UX, never to a behavior-unverified invariant. The same carve-out covers an **abstained non-inferable truth** (⚠️ `insufficient_spec`, § Backstop abstention below) — an insufficient-spec gap is an evidence gap, not a user-facing step, so it too still emits its human-verification item and drives `human_needed` on an infrastructure phase.

**How to determine if a phase is infrastructure/foundation:**
- Phase goal or name contains: "foundation", "infrastructure", "schema", "database", "internal API", "data model", "scaffolding", "pipeline", "tooling", "CI", "migrations", "service layer", "backend", "core library"
- Phase success criteria describe only technical artifacts (files exist, tests pass, schema is valid) with no user interaction required
- There is no UI, CLI output visible to end users, or real-time behavior to observe

**If the phase IS infrastructure/foundation:** do not invent manual UX checks, **except any ⚠️ PRESENT_BEHAVIOR_UNVERIFIED or abstained ⚠️ `insufficient_spec` truth (see exception above), which still emits a human-verification item and drives `human_needed`.** Only when no such excepted truth exists, log:

```markdown
## Human Verification

N/A — Infrastructure/foundation phase with no user-facing elements.
All acceptance criteria are verifiable programmatically.
```

**If the phase IS user-facing:** only flag items that genuinely require a human — per the Step 8 always/uncertain lists already in the agent. Do not invent steps.

## Backstop abstention

For an explicitly underspecified (`verification: backstop`) truth, require evidence
that resolves the actual ambiguity. Otherwise record `reason: insufficient_spec`
and route to `human_needed`. This applies to infrastructure too. Continue checking
independent outcomes, but never describe unresolved required checks as complete.
Read [honest verifier](honest-verifier.md) for examples and the evidence distinction.

## Local supporting references

Before artifact verification on an unfamiliar stack, read the applicable sections
of [verification patterns](verification-patterns.md). This complete catalog covers
components, API routes, schemas, hooks, configuration, per-stack checklists and
pre-checkpoint setup; do not substitute the shorter wiring reference for it.
Load only the relevant stack sections.

Use [wiring patterns](verifier-wiring-patterns.md) and the role's stub examples to
trace components, APIs, persistence and returned data. Adapt searches to the actual
language rather than assuming React. Use the complete
[verification report](../../templates/verification-report.md) and
[runtime contract](../../runtime/TEMPLATE-CONTRACT.md). The runtime owns report
capture, source fingerprints and required check receipts. Required UAT always
needs actual human observations; an infrastructure label cannot auto-pass it.
