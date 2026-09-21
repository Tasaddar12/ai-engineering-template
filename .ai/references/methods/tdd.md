# Test-driven development

Adapted supporting method; attribution is in [third-party notices](../../THIRD-PARTY-NOTICES.md).
The [local TDD contract](../../runtime/TEMPLATE-CONTRACT.md#native-tdd-feature-plans)
owns executable plan fields and evidence. This method provides the design and
review procedure; it does not introduce an SDK or an automatic pre-GREEN gate.
Follow the user's validation limits. If tests are explicitly deferred, report
that evidence as pending rather than claiming a completed TDD cycle.

<overview>
TDD is about design quality, not coverage metrics. The red-green-refactor cycle forces you to think about behavior before implementation, producing cleaner interfaces and more testable code.

**Principle:** If you can describe the behavior as `expect(fn(input)).toBe(output)` before writing `fn`, TDD improves the result.

**Key insight:** TDD work is fundamentally heavier than standard tasks—it requires 2-3 execution cycles (RED → GREEN → REFACTOR), each with file reads, test runs, and potential debugging. TDD features get dedicated plans to ensure full context is available throughout the cycle.
</overview>

<when_to_use_tdd>
## When TDD Improves Quality

**TDD candidates (create a TDD plan):**
- Business logic with defined inputs/outputs
- API endpoints with request/response contracts
- Data transformations, parsing, formatting
- Validation rules and constraints
- Algorithms with testable behavior
- State machines and workflows
- Utility functions with clear specifications

**Skip TDD (use standard plan with `type="auto"` tasks):**
- UI layout, styling, visual components
- Configuration changes
- Glue code connecting existing components
- One-off scripts and migrations
- Simple CRUD with no business logic
- Exploratory prototyping

**Heuristic:** Can you write `expect(fn(input)).toBe(output)` before writing `fn`?
→ Yes: Create a TDD plan
→ No: Use standard plan, add tests after if needed
</when_to_use_tdd>

<tdd_plan_structure>
## TDD Plan Structure

Each TDD plan implements **one feature** through the full RED-GREEN-REFACTOR cycle.

```markdown
---
phase: XX-name
plan: "NN"
type: tdd
# Include the remaining ownership, requirements, acceptance, documentation and checks
# fields required by the local contract; this excerpt only illustrates the feature body.
---

<objective>
[What feature and why]
Purpose: [Design benefit of TDD for this feature]
Output: [Working, tested feature]
</objective>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@relevant/source/files.ts
</context>

<feature>
  <name>[Feature name]</name>
  <files>[source file, test file]</files>
  <behavior>
    [Expected behavior in testable terms]
    Cases: input → expected output
  </behavior>
  <implementation>[How to implement once tests pass]</implementation>
</feature>

<verification>
[Test command that proves feature works]
</verification>

<success_criteria>
- Failing test written and committed
- Implementation passes test
- Refactor complete (if needed)
- All 2-3 commits present
</success_criteria>

<output>
After completion, create SUMMARY.md with:
- RED: What test was written, why it failed
- GREEN: What implementation made it pass
- REFACTOR: What cleanup was done (if any)
- Commits: List of commits produced
</output>
```

**One feature per TDD plan.** If features are trivial enough to batch, they're trivial enough to skip TDD—use a standard plan and add tests after.
</tdd_plan_structure>

<execution_flow>
## Red-Green-Refactor Cycle

**RED - Write failing test:**
1. Create test file following project conventions
2. Write test describing expected behavior (from `<behavior>` element)
3. Run test - it MUST fail **intentionally**: the TARGET test you named must be the test that fails, on an assertion for the planned behavior. A nonzero exit alone is NOT RED — syntax errors, zero-test discovery, fixture crashes, parser errors, and unrelated assertions are INVALID_RED and must not authorize GREEN.
4. Record the command, exit code, named failing test, expected result and actual assertion. Inspect that evidence before GREEN. A setup error, unrelated failure or zero-test run does not establish RED. Preserve the observations in SUMMARY TDD Evidence; the local runtime reruns final checks, not a pre-GREEN SDK gate.
5. If test passes: feature exists or test is wrong. Investigate.
6. Commit: `test({phase}-{plan}): add failing test for [feature]`

**GREEN - Implement to pass:**
1. Write minimal code to make test pass
2. No cleverness, no optimization - just make it work
3. Run test - it MUST pass
4. Commit: `feat({phase}-{plan}): implement [feature]`

**REFACTOR (if needed):**
1. Refactor assigned changed code only to remove duplication, simplify control flow, improve names, extract constants/helpers or meet project conventions; preserve behavior and do not clean up unrelated code.
2. Run tests - MUST still pass
3. Only commit if changes made: `refactor({phase}-{plan}): clean up [feature]`

**Result:** Each TDD plan produces 2-3 atomic commits.
</execution_flow>

<test_quality>
## Good Tests vs Bad Tests

**Test behavior, not implementation:**
- Good: "returns formatted date string"
- Bad: "calls formatDate helper with correct params"
- Tests should survive refactors

**One concept per test:**
- Good: Separate tests for valid input, empty input, malformed input
- Bad: Single test checking all edge cases with multiple assertions

**Descriptive names:**
- Good: "should reject empty email", "returns null for invalid ID"
- Bad: "test1", "handles error", "works correctly"

**No implementation details:**
- Good: Test public API, observable behavior
- Bad: Mock internals, test private methods, assert on internal state
</test_quality>

<framework_setup>
## Test Framework Setup (If None Exists)

First inspect the existing project tooling and reuse its configured runner.
If no framework is available, setup belongs in the assigned plan with ownership
of its manifest/configuration files. Only perform installation when that setup is
authorized; otherwise report the missing capability to the coordinator. The
following are examples for an authorized setup, not default package choices or
permission to install globally. Honor any instruction to defer tests.

**1. Detect project type:**
```bash
# JavaScript/TypeScript
if [ -f package.json ]; then echo "node"; fi

# Python
if [ -f requirements.txt ] || [ -f pyproject.toml ]; then echo "python"; fi

# Go
if [ -f go.mod ]; then echo "go"; fi

# Rust
if [ -f Cargo.toml ]; then echo "rust"; fi
```

**2. Select the project-approved framework (installation only when authorized):**
| Project | Framework | Install |
|---------|-----------|---------|
| Node.js | Jest | `npm install -D jest @types/jest ts-jest` |
| Node.js (Vite) | Vitest | `npm install -D vitest` |
| Python | pytest | `pip install pytest` |
| Go | testing | Built-in |
| Rust | cargo test | Built-in |

**3. Create config if needed:**
- Jest: `jest.config.js` with ts-jest preset
- Vitest: `vitest.config.ts` with test globals
- pytest: `pytest.ini` or `pyproject.toml` section

**4. Verify setup:**
```bash
# Inspect discovery and setup; an empty suite is not behavior evidence.
npm test  # Node
pytest    # Python
go test ./...  # Go
cargo test    # Rust
```

**5. Create first test file:**
Follow project conventions for test location:
- `*.test.ts` / `*.spec.ts` next to source
- `__tests__/` directory
- `tests/` directory at root

Framework setup is a one-time cost included in the first TDD plan's RED phase.
</framework_setup>

<error_handling>
## Error Handling

**Test doesn't fail in RED phase:**
- Feature may already exist - investigate
- Test may be wrong (not testing what you think)
- Fix before proceeding

**Test doesn't pass in GREEN phase:**
- Debug implementation
- Don't skip to refactor
- Keep iterating until green

**Tests fail in REFACTOR phase:**
- Undo refactor
- Commit was premature
- Refactor in smaller steps

**Unrelated tests break:**
- Stop and investigate
- May indicate coupling issue
- Fix before proceeding
</error_handling>

<commit_pattern>
## Commit Pattern for TDD Plans

TDD plans produce 2-3 atomic commits (one per phase):

```
test(08-02): add failing test for email validation

- Tests valid email formats accepted
- Tests invalid formats rejected
- Tests empty input handling

feat(08-02): implement email validation

- Regex pattern matches RFC 5322
- Returns boolean for validity
- Handles edge cases (empty, null)

refactor(08-02): extract regex to constant (optional)

- Moved pattern to EMAIL_REGEX constant
- No behavior changes
- Tests still pass
```

**Comparison with standard plans:**
- Standard plans: 1 commit per task, 2-4 commits per plan
- TDD plans: 2-3 commits for single feature

Both follow same format: `{type}({phase}-{plan}): {description}`

**Benefits:**
- Each commit independently revertable
- Git bisect works at commit level
- Clear history showing TDD discipline
- Consistent with overall commit strategy
</commit_pattern>

<gate_enforcement>
## Gate Enforcement Rules

For an assigned `type: tdd` plan, follow RED/GREEN/REFACTOR and preserve observable evidence. Plan metadata and the local contract govern the assignment; no separate JSON mode flag is required.

### Gate Definitions

| Gate | Required | Commit Pattern | Validation |
|------|----------|---------------|------------|
| RED | Yes | `test({phase}-{plan}): ...` | Test exists AND fails before implementation — intentionally: the named target test fails on an assertion for the planned behavior, with the actual command and result recorded |
| GREEN | Yes | `feat({phase}-{plan}): ...` | Test passes after implementation |
| REFACTOR | No | `refactor({phase}-{plan}): ...` | Tests still pass after cleanup |

### Fail-Fast Rules

1. **Unexpected GREEN in RED phase:** If the test passes before any implementation code is written, STOP. The feature may already exist or the test is wrong. Investigate before proceeding.
2. **INVALID_RED in RED phase:** A nonzero exit is not RED by itself. Zero-test discovery, fixture/load crashes, nonzero exits with no failing test, unrelated failing tests, and unexpected greens all classify as INVALID_RED. STOP and fix the RED phase — do NOT proceed to GREEN.
3. **Missing RED commit:** If no `test(...)` commit precedes the `feat(...)` commit, the TDD discipline was violated. Flag in SUMMARY.md.
4. **REFACTOR breaks tests:** Undo the refactor immediately. Commit was premature — refactor in smaller steps.

### Executor Gate Validation

After completing a `type: tdd` plan, inspect the assigned branch's commit history
and the recorded commands/results. Verify that the named RED commit precedes
GREEN and that the assertion failed for the planned reason. Commit-message
prefixes alone do not prove a test ran. Include the exact commit IDs, command
outputs and refactor outcome in SUMMARY's `## TDD Evidence`; disclose missing
steps without inventing retrospective RED evidence.
</gate_enforcement>

<end_of_phase_review>
## End-of-phase TDD review checkpoint

After the assigned TDD plans are integrated and before final phase verification,
the coordinator gathers a per-plan review. This is an explicit coordinator step;
the Python runtime does not synthesize the checkpoint or invoke a TDD SDK gate.

```text
### TDD REVIEW — Phase {X}
TDD Plans: {count} | Gate violations: {count} | Unverified: {count}

| Plan | RED commit/result | GREEN commit/result | REFACTOR | Status |
|------|-------------------|---------------------|----------|--------|
| {id} | {hash, command, intended failure} | {hash, command, pass/fail} | {result or not needed} | {status} |
```

Review gate order, intentional RED (not setup failure), minimal GREEN without
premature optimization, and passing checks after any refactor. Show violations
and missing evidence explicitly; preserve previous commits. Obtain any assigned
human review using the checkpoint procedure, including `blocking-human` when
specified. Do not invent an automatic approval or defer a required human gate.
Discipline observations are advisory unless they violate assigned acceptance;
missing required behavioral evidence still prevents a verified completion.

## Independent TDD evidence review

During [phase verification](../../commands/verify-work.md), compare each assigned
TDD plan's behavior with the implemented result and its recorded evidence:

| Item | Evidence to inspect |
|---|---|
| RED | Named target assertion failed for the planned behavior before implementation |
| GREEN | Same behavior passed after implementation at the named revision |
| REFACTOR | If performed, checks still pass; otherwise explicitly not needed |
| Regression value | The assertion would catch the original defect or missing behavior |

The verifier independently assesses this evidence. A missing required result is
a gap, not an advisory that can silently pass. Human acceptance follows the
local UAT/checkpoint procedure for every assigned human review; preserve explicit
`blocking-human` gates even when automated evidence is conclusive.
</end_of_phase_review>

<context_budget>
## Context Budget

TDD plans target **~40% context usage** (lower than standard plans' ~50%).

Why lower:
- RED phase: write test, run test, potentially debug why it didn't fail
- GREEN phase: implement, run test, potentially iterate on failures
- REFACTOR phase: modify code, run tests, verify no regressions

Each phase involves reading files, running commands, analyzing output. The back-and-forth is inherently heavier than linear task execution.

Single feature focus ensures full quality throughout the cycle.
</context_budget>
