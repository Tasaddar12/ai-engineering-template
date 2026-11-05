# Verifier Phase Gates

> Loaded eagerly by `agents/verifier.md` (`<required_reading>`). Carries the three
> verification-time gates that lived in the retired `verify-phase` workflow
> ( / epic F7): decision-coverage validation, the test-quality audit,
> and infrastructure-phase human-verification scoping — plus the backstop-abstention
> reporting contract. Run each gate at its named
> agent step; `engineer_run` is the launcher shim defined in the agent's own Step 1 block.

## verify_decisions — Decision Coverage Gate (run after writing report evidence, before fingerprinting and delivery)

<step name="verify_decisions">
**Decision coverage validation gate.**

Independently assess implementation compliance with each trackable decision
while collecting verification evidence. Write those actual findings, including
decision IDs and supporting evidence or gaps, into VERIFICATION.md with the
truthful Step 9 status. Then run this structural check on the written report,
before the final fingerprint and delivery. Do not invent citations to make the
check pass.

The handler collects explicit `D-<digits>` IDs anywhere in the phase's
`*-CONTEXT.md` files and checks their presence in `*-VERIFICATION.md` text.
It does not inspect plans, SUMMARY.md, source files or commit subjects for
verification evidence, and it does not judge whether implementation honors a
decision. An ID cited alongside a failed or unverified finding still satisfies
structural presence; that finding remains a separate verification gap.

**Skip if** `workflow.context_coverage_gate` is explicitly set to `false`
(absent key = enabled). The handler performs this skip itself. Missing context
is blocking. Context with no tracked IDs still requires a verification report;
absence of a `<decisions>` block is not a skip condition.

```bash
DECISION_RESULT=$(engineer_run query check.decision-coverage-verify "${PHASE_NUM}" --dir "${PHASE_DIR}") && DECISION_EXIT=0 || DECISION_EXIT=$?
```

For a report citing both tracked IDs, the native result is:

```json
{"passed": true, "block": false, "structuralOnly": true, "decisions": ["D-01", "D-02"], "uncovered": [], "files": ["${PHASE_DIR}/${PHASE_NUM}-VERIFICATION.md"]}
```

`decisions` and `uncovered` contain sorted unique IDs; `files` lists the
verification reports examined. A missing report yields `files: []`,
`passed: false`, `block: true` and all tracked IDs in `uncovered`. Any uncovered
ID also yields `passed: false` and `block: true`. Missing context returns
`{"passed": false, "block": true, "uncovered": [], "reason": "Decision context is missing", "structuralOnly": true}`.
The disabled gate returns only
`{"passed": true, "skipped": true, "uncovered": []}`.

Passes and skips exit `0`; blocking coverage results exit `1`. Runtime/caller
errors can emit an error diagnostic on stderr without coverage JSON. Preserve
the actual diagnostic and nonzero exit status; record coverage as not evaluated
when no coverage result was produced. Do not reinterpret an error or missing
evidence as zero decisions or successful verification.

**Reporting:** Add a narrative `### Decision Coverage` section recording the
actual structural result, tracked/uncovered IDs and examined report paths, or
the skip/error diagnostic. Keep the independently assessed implementation
findings and their evidence. The handler does not return a Markdown message or
honored/total counts; do not add unsupported `decision_coverage` frontmatter.

**Status impact:** Respect `block: true` as an unresolved verification gap and
retain the nonzero result for remediation before reporting overall `passed`.
A structural pass alone does not establish implementation compliance or
override `gaps_found` / `human_needed` findings from the other checks. After any
report correction, rerun the gate before the final fingerprint and delivery.
</step>

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

**Rule:** A test comparing system output against values generated by the same system is circular. It proves consistency, not correctness.

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
- **Exception — behavior-unverified truths still count.** A truth marked ⚠️ PRESENT_BEHAVIOR_UNVERIFIED (a state transition or a cancellation/cleanup/ordering invariant with no test exercising it) is a behavioral-evidence gap, not an artificial user-facing step. Record it in `behavior_unverified_items` and emit a human-verification item for it **even on an infrastructure/foundation phase** — these invariants are exactly where infra phases hide runtime state leaks. Such a truth drives `human_needed`; the auto-pass-UAT shortcut applies only to the absence of user-facing UX, never to a behavior-unverified invariant. The same carve-out covers an **abstained non-inferable truth** (⚠️ `insufficient_spec`, § Backstop abstention below) — an insufficient-spec gap is an evidence gap, not a user-facing step, so it too still emits its human-verification item and drives `human_needed` on an infrastructure phase.

**How to determine if a phase is infrastructure/foundation:**
- Phase goal or name contains: "foundation", "infrastructure", "schema", "database", "internal API", "data model", "scaffolding", "pipeline", "tooling", "CI", "migrations", "service layer", "backend", "core library"
- Phase success criteria describe only technical artifacts (files exist, tests pass, schema is valid) with no user interaction required
- There is no UI, CLI output visible to end users, or real-time behavior to observe

**If the phase IS infrastructure/foundation:** auto-pass UAT — skip the human verification items list entirely, **except any ⚠️ PRESENT_BEHAVIOR_UNVERIFIED or abstained ⚠️ `insufficient_spec` truth (see exception above), which still emits a human-verification item and drives `human_needed`.** Only when no such excepted truth exists, log:

```markdown
## Human Verification

N/A — Infrastructure/foundation phase with no user-facing elements.
All acceptance criteria are verifiable programmatically.
```

**If the phase IS user-facing:** only flag items that genuinely require a human — per the Step 8 always/uncertain lists already in the agent. Do not invent steps.

## Backstop abstention — reporting contract (companion to agent Step 3 item 5b)

When a non-inferable (`verification: backstop`) truth abstains for lack of explicit evidence:

- **Never silent, never a hard halt.** *Interactive:* the abstained item routes to the end-of-phase
  human checkpoint. *Autonomous (AFK):* it produces a prominent `unverified — held-out test
  recommended` flag and the completion line reads "complete with N unverified non-inferable checks";
  the run neither silently passes the blind spot nor hard-halts.
- **Distinguishable reason.** The abstain disposition carries `reason: insufficient_spec` so its
  `human_needed` outcome is never conflated with an ordinary manual-UAT `human_needed`.
- **Infrastructure phases included.** This rides the same carve-out as ⚠️ PRESENT_BEHAVIOR_UNVERIFIED
  in the infrastructure-phase gate above: an abstention is an evidence gap, not a user-facing step,
  so the infra auto-pass-UAT shortcut never absorbs it.

Full protocol and rationale: `engineer/references/honest-verifier.md`.

## Lazy references

- **Per-stack verification patterns:** before Step 4 (artifact verification) on an unfamiliar stack, Read `engineer/references/verification-patterns.md` — the grep catalog for React/Next.js components, API routes, database schema, and the universal stub patterns. Read it lazily (only the sections for the stack under verification); it is too large to load wholesale on every run.
- **Canonical report shape:** the emitted VERIFICATION.md follows `@~/.claude/engineer/templates/verification-report.md` — the template whose Guidelines and row shapes `src/uat.cts` treats as canonical when consuming verification output.
