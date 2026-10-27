<purpose>
Generate unit and E2E tests for a completed phase based on its SUMMARY.md, CONTEXT.md, and implementation. Classifies each changed file into TDD (unit), E2E (browser), or Skip categories, presents a test plan for user approval, then generates tests following RED-GREEN conventions.

Users currently hand-craft `/quick` prompts for test generation after each phase. This workflow standardizes the process with proper classification, quality gates, and gap reporting.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<authority>
Only an explicit user invocation of `/add-tests N`, or an already recorded instruction covering this exact bounded test work, authorizes writing tests. Read CONTEXT and preserve locked acceptance; this command does not authorize product fixes or another phase. Classification/test-plan approvals already supplied remain valid. Inherently human acceptance is not supplied by generated tests. Honor user test ordering throughout; deferred runs remain pending.
</authority>

<step name="parse_arguments">
Parse `$ARGUMENTS` for:
- Phase number (integer, decimal, or letter-suffix) → store as `$PHASE_ARG`
- Remaining text after phase number → store as `$EXTRA_INSTRUCTIONS` (optional)

Example: `/add-tests 12 focus on edge cases` → `$PHASE_ARG=12`, `$EXTRA_INSTRUCTIONS="focus on edge cases"`

If no phase argument provided:

```
ERROR: Phase number required
Usage: /add-tests <phase> [additional instructions]
Example: /add-tests 12
Example: /add-tests 12 focus on edge cases in the pricing module
```

Exit.
</step>

<step name="init_context">
Load phase operation context:

Read and execute engineer/workflows/_runtime-launcher.snippet.sh, then run `engineer_run query phase.locate "${PHASE_ARG}"`. Require found=true and enter its quoted worktree. Reuse its actual matching phase session; otherwise open with `session.open phase N` or adopt only an established owned isolated checkout with `session.adopt phase N`. Retain root/branch/base/session/caller identity and initialize there:

```bash
INIT=$(engineer_run query init.phase-op "${PHASE_ARG}")
```

Require phase_found=true. No --ws or overflow-file protocol is supported.

Extract from init JSON: `phase_dir`, `phase_number`, `phase_name`, `response_language`.

**If `response_language` is set:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated.

Verify the phase directory exists. If not:
```
ERROR: Phase directory not found for phase ${PHASE_ARG}
Ensure the phase exists in .planning/phases/
```
Exit.

Read the phase artifacts (in order of priority):
1. `${phase_dir}/*-SUMMARY.md` — what was implemented, files changed
2. `${context_path}` (the actual prefixed phase CONTEXT) — acceptance criteria, decisions
3. `${uat_path}` and `${verification_path}` — actual human UAT observations and independent verification; verification alone is not human acceptance

If no SUMMARY.md exists:
```
ERROR: No SUMMARY.md found for phase ${PHASE_ARG}
This command works on completed phases. Run /execute-phase first.
```
Exit.

Present banner:
```
### ENGINEER ► ADD TESTS — Phase ${phase_number}: ${phase_name}
```
</step>

<step name="analyze_implementation">
Extract the list of files modified by the phase from SUMMARY.md ("Files Changed" or equivalent section).

For each file, classify into one of three categories:

| Category | Criteria | Test Type |
|----------|----------|-----------|
| **TDD** | Pure functions where `expect(fn(input)).toBe(output)` is writable | Unit tests |
| **E2E** | UI behavior verifiable by browser automation | Playwright/E2E tests |
| **Skip** | Not meaningfully testable or already covered | None |

**TDD classification — apply when:**
- Business logic: calculations, pricing, tax rules, validation
- Data transformations: mapping, filtering, aggregation, formatting
- Parsers: CSV, JSON, XML, custom format parsing
- Validators: input validation, schema validation, business rules
- State machines: status transitions, workflow steps
- Utilities: string manipulation, date handling, number formatting

**E2E classification — apply when:**
- Keyboard shortcuts: key bindings, modifier keys, chord sequences
- Navigation: page transitions, routing, breadcrumbs, back/forward
- Form interactions: submit, validation errors, field focus, autocomplete
- Selection: row selection, multi-select, shift-click ranges
- Drag and drop: reordering, moving between containers
- Modal dialogs: open, close, confirm, cancel
- Data grids: sorting, filtering, inline editing, column resize

**Skip classification — apply when:**
- UI layout/styling: CSS classes, visual appearance, responsive breakpoints
- Configuration: config files, environment variables, feature flags
- Glue code: dependency injection setup, middleware registration, routing tables
- Migrations: database migrations, schema changes
- Simple CRUD: basic create/read/update/delete with no business logic
- Type definitions: records, DTOs, interfaces with no logic

Read each file to verify classification. Don't classify based on filename alone. These Skip examples are discovery heuristics, not exemptions: migrations, CRUD, routing, configuration and layout may carry required behavior, security boundaries or acceptance. Cite existing meaningful coverage or a genuine human-only reason for every Skip. Never silently omit a requirement because its implementation fits a Skip label.

Read every UAT action's actual result and evidence, unresolved gaps and historical resolved_by/resolved_at links. Derive cases from accepted behavior in CONTEXT/SPEC and SUMMARY claims; preserve failed/skipped/blocked scenarios as open findings. A diagnosis or planned resolution does not convert them to accepted behavior.
</step>

<step name="present_classification">
Present the classification to the user for confirmation before proceeding:

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex) where `AskUserQuestion` is not available.

```
AskUserQuestion(
  header: "Test Classification",
  question: |
    ## Files classified for testing

    ### TDD (Unit Tests) — {N} files
    {list of files with brief reason}

    ### E2E (Browser Tests) — {M} files
    {list of files with brief reason}

    ### Skip — {K} files
    {list of files with brief reason}

    {if $EXTRA_INSTRUCTIONS: "Additional instructions: ${EXTRA_INSTRUCTIONS}"}

    How would you like to proceed?
  options:
    - "Approve and generate test plan"
    - "Adjust classification (I'll specify changes)"
    - "Cancel"
)
```

If user selects "Adjust classification": apply their changes and re-present.
If user selects "Cancel": exit gracefully.
</step>

<step name="discover_test_structure">
Before generating the test plan, discover the project's existing test structure:

```bash
# Find existing test directories
find . -type d -name "*test*" -o -name "*spec*" -o -name "*__tests__*" 2>/dev/null | head -20
# Find existing test files for convention matching
find . -type f \( -name "*.test.*" -o -name "*.spec.*" -o -name "*Tests.fs" -o -name "*Test.fs" \) 2>/dev/null | head -20
# Check for test runners
ls package.json *.sln 2>/dev/null || true
```

Identify:
- Test directory structure (where unit tests live, where E2E tests live)
- Naming conventions (`.test.ts`, `.spec.ts`, `*Tests.fs`, etc.)
- Test runner commands (how to execute unit tests, how to execute E2E tests)
- Test framework (xUnit, NUnit, Jest, Playwright, etc.)

If test structure is ambiguous, ask the user:
```
AskUserQuestion(
  header: "Test Structure",
  question: "I found multiple test locations. Where should I create tests?",
  options: [list discovered locations]
)
```
</step>

<step name="generate_test_plan">
For each approved file, create a detailed test plan.

**For TDD files**, plan tests following RED-GREEN-REFACTOR:
1. Identify testable functions/methods in the file
2. For each function: list input scenarios, expected outputs, edge cases
3. Note: since code already exists, tests may pass immediately — that's OK, but verify they test the RIGHT behavior

**For E2E files**, plan tests following RED-GREEN gates:
1. Identify user scenarios from CONTEXT.md/VERIFICATION.md
2. For each scenario: describe the user action, expected outcome, assertions
3. Note: RED gate means confirming the test would fail if the feature were broken

Present the complete test plan:

```
AskUserQuestion(
  header: "Test Plan",
  question: |
    ## Test Generation Plan

    ### Unit Tests ({N} tests across {M} files)
    {for each file: test file path, list of test cases}

    ### E2E Tests ({P} tests across {Q} files)
    {for each file: test file path, list of test scenarios}

    ### Test Commands
    - Unit: {discovered test command}
    - E2E: {discovered e2e command}

    Ready to generate?
  options:
    - "Generate all"
    - "Cherry-pick (I'll specify which)"
    - "Adjust plan"
)
```

If "Cherry-pick": ask user which tests to include.
If "Adjust plan": apply changes and re-present.
</step>

<step name="dispatch_test_generation">
The coordinator dispatches generation rather than writing tests inline. Resolve `engineer_run query resolve-model executor --raw` and `resolve-effort executor --raw`, and pass both concrete non-inherit values inline. Resolve `dispatch-isolation --phase N --plan P`; use its mandatory harness-worktree or orchestrator-worktree strategy. For orchestrator ownership, create the worker with `worktree.create P --phase N --base SHA --files PATH...`; for native harness isolation, pass isolation="worktree" and record actual path/branch/base/owned files with worktree.record-agent. Verify assignment identities before writes; no opt-out exists.

Prepare a real bounded phase PLAN and exact SUMMARY destination from the complete templates, with approved requirements/acceptance/check argv/documentation/issue_refs and enumerated owned tests/fixtures; coordinator retains shared records and VALIDATION. Dispatch `Agent(subagent_type="executor", model=<resolved>, effort=<resolved>, prompt=<full concrete packet>)`, omitting inherit. Supply the complete approved classification/test plan, UAT/CONTEXT/SPEC/SUMMARY/source, test conventions, exact checks/cwd/timeouts/resources, user test ordering and both full worker methods below. Exclude product source changes and child dispatch.

Wait for the terminal result before touching owned paths. Require committed owned tests plus schema-valid SUMMARY, base/head/hashes, per-case generated/pass/fail/pending evidence and Remaining. The worker preserves failing test evidence and reports product bugs; it cannot weaken approved expectations to get green. A deferred run stays pending/blocked; preserve its branch and resume after permission rather than bypassing complete-summary integration gates. Integrate a valid complete return through `engineer_run query worktree.merge-wave --phase N`. Confirm actual merged scope and run configured `verification.run-checks` on the integrated revision when permitted, reusing only current passing receipts.

Retrofitted tests may pass immediately: report characterization evidence accurately, never claim a historical RED. For a true TDD repair, use the full TDD resolution/RED contract in execute-phase/steps/tdd-applicability-resolution.md; require a proven assertion RED test commit ancestor before GREEN. Deliberate broken/known-bad fixture checks must also retain a clean control; do not modify production source merely to fabricate history.
</step>

<worker_method name="execute_tdd_generation">
For each approved TDD test:

1. **Create test file** following discovered project conventions (directory, naming, imports)

2. **Write test** with clear arrange/act/assert structure:
   ```
   // Arrange — set up inputs and expected outputs
   // Act — call the function under test
   // Assert — verify the output matches expectations
   ```

3. **Run the test**:
   ```bash
   {approved exact argv}
   ```

4. **Evaluate result:**
   - **Test passes**: Good — the implementation satisfies the test. Verify the test checks meaningful behavior (not just that it compiles).
   - **Test fails with assertion error**: This may be a genuine bug discovered by the test. Flag it:
     ```
     ⚠️ Potential bug found: {test name}
     Expected: {expected}
     Actual: {actual}
     File: {implementation file}
     ```
     Do NOT fix the implementation — this is a test-generation command, not a fix command. Record the finding.
   - **Test fails with error (import, syntax, etc.)**: This is a test error. Fix the test and re-run.
</worker_method>

<worker_method name="execute_e2e_generation">
For each approved E2E test:

1. **Check for existing tests** covering the same scenario:
   ```bash
   grep -r "{scenario keyword}" {e2e test directory} 2>/dev/null || true
   ```
   If found, extend rather than duplicate.

2. **Create test file** targeting the user scenario from CONTEXT.md/VERIFICATION.md

3. **Run the E2E test**:
   ```bash
   {approved exact E2E argv}
   ```

4. **Evaluate result:**
   - **GREEN (passes)**: Record success
   - **RED (fails)**: Determine if it's a test issue or a genuine application bug. Flag bugs:
     ```
     ⚠️ E2E failure: {test name}
     Scenario: {description}
     Error: {error message}
     ```
   - **Cannot run**: Report blocker. Do NOT mark as complete.
     ```
     🛑 E2E blocker: {reason tests cannot run}
     ```

**No-skip rule:** If E2E tests cannot execute (missing dependencies, environment issues), report the blocker and mark the test as incomplete. Never mark success without actually running the test.
</worker_method>

<step name="summary_and_commit">
Create a test coverage report and present to user:

```
### ENGINEER ► TEST GENERATION COMPLETE

## Results

| Category | Generated | Passing | Failing | Blocked |
|----------|-----------|---------|---------|---------|
| Unit     | {N}       | {n1}    | {n2}    | {n3}    |
| E2E      | {M}       | {m1}    | {m2}    | {m3}    |

## Files Created/Modified
{list of test files with paths}

## Coverage Gaps
{areas that couldn't be tested and why}

## Bugs Discovered
{any assertion failures that indicate implementation bugs}
```

Read actual state without inventing progress:
```bash
engineer_run query state.get
```

The worker already committed its assigned tests and SUMMARY. Commit only actual coordinator record changes with `engineer_run query commit MESSAGE --files PATH...`; never restage worker paths. Report generated, passing, failing and pending separately. "All tests passing" requires actual current checks and complete approved scope, not just generated counts.

Route discovered bugs by stable finding IDs using engineer/references/git-workflow.md and its full Bug/UAT variants. Within authorized publication use phase.issue-declare with the expected digest, phase.issue-preview with exact `--variant Bug` or `--variant UAT`, an explicit reviewed existing-issue/no-match disposition, phase.issue-publish with the same bound token and provider readback. Preserve unresolved human acceptance. Product repairs require already covering implementation authority or a concrete reported dependent decision; generation alone cannot authorize them. Follow canonical draft tracking for authorized delivery and leave merge to the human. Return concrete coverage, hashes, revision, receipts, gaps, issue URLs and session/caller identity; do not replace these with next-command prompts.
</step>

</process>

<success_criteria>
- [ ] Phase artifacts loaded (SUMMARY.md, CONTEXT.md, optionally VERIFICATION.md)
- [ ] All changed files classified into TDD/E2E/Skip categories
- [ ] Classification presented to user and approved
- [ ] Project test structure discovered (directories, conventions, runners)
- [ ] Test plan presented to user and approved
- [ ] TDD tests generated with arrange/act/assert structure
- [ ] E2E tests generated targeting user scenarios
- [ ] Required executions actually pass, or remain explicitly pending under user ordering; no untested pass claims
- [ ] Bugs discovered by tests flagged (not fixed)
- [ ] Test files committed with proper message
- [ ] Coverage gaps documented
- [ ] Complete evidence and remaining obligations returned to the user/caller
</success_criteria>
