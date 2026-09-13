<purpose>
Generate unit and E2E tests for a completed phase based on its SUMMARY.md, CONTEXT.md, and implementation. Classifies each changed file into TDD (unit), E2E (browser), or Skip categories, presents a test plan for user approval, then generates tests following RED-GREEN conventions.

Users currently hand-craft `/workflow:quick` prompts for test generation after each phase. This workflow standardizes the process with proper classification, quality gates, and gap reporting.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="parse_arguments">
Parse `$ARGUMENTS` for:
- Phase number (integer, decimal, or letter-suffix) → store as `$PHASE_ARG`
- Remaining text after phase number → store as `$EXTRA_INSTRUCTIONS` (optional)

Example: `/workflow:add-tests 12 focus on edge cases` → `$PHASE_ARG=12`, `$EXTRA_INSTRUCTIONS="focus on edge cases"`

If no phase argument provided:

```
ERROR: Phase number required
Usage: /workflow:add-tests <phase> [additional instructions]
Example: /workflow:add-tests 12
Example: /workflow:add-tests 12 focus on edge cases in the pricing module
```

Exit.
</step>

<step name="init_context">
Load phase operation context:

```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
INIT=$(workflow_run query init.phase-op "${PHASE_ARG}")
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
```

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
2. `${phase_dir}/CONTEXT.md` — acceptance criteria, decisions
3. `${phase_dir}/*-VERIFICATION.md` — user-verified scenarios (if UAT was done)

If no SUMMARY.md exists:
```
ERROR: No SUMMARY.md found for phase ${PHASE_ARG}
This command works on completed phases. Run /workflow:execute-phase first.
```
Exit.

Present banner:
```
### Workflow ► ADD TESTS — Phase ${phase_number}: ${phase_name}
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

Read each file to verify classification. Don't classify based on filename alone.
</step>

<step name="present_classification">
Present the classification to the user for confirmation before proceeding:

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex, Gemini CLI, etc.) where `AskUserQuestion` is not available.

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

<step name="execute_tdd_generation">
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
   {discovered test command}
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
</step>

<step name="execute_e2e_generation">
For each approved E2E test:

1. **Check for existing tests** covering the same scenario:
   ```bash
   grep -r "{scenario keyword}" {e2e test directory} 2>/dev/null || true
   ```
   If found, extend rather than duplicate.

2. **Create test file** targeting the user scenario from CONTEXT.md/VERIFICATION.md

3. **Run the E2E test**:
   ```bash
   {discovered e2e command}
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
</step>

<step name="summary_and_commit">
Create a test coverage report and present to user:

```
### Workflow ► TEST GENERATION COMPLETE

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

Record test generation in project state:
```bash
workflow_run query state-snapshot
```

If there are passing tests to commit:

```bash
git add {test files}
git commit -m "test(phase-${phase_number}): add unit and E2E tests from add-tests command" -- {test files}
```

Present next steps:

```
---

## ▶ Next Up — [${PROJECT_CODE}] ${PROJECT_TITLE}

{if bugs discovered:}
**Fix discovered bugs:** `/workflow:quick fix the {N} test failures discovered in phase ${phase_number}`

{if blocked tests:}
**Resolve test blockers:** {description of what's needed}

{otherwise:}
**All tests passing!** Phase ${phase_number} is fully tested.

---

**Also available:**
- `/workflow:add-tests {next_phase}` — test another phase
- `/workflow:verify-work {phase_number}` — run UAT verification

---
```
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
- [ ] All tests executed — no untested tests marked as passing
- [ ] Bugs discovered by tests flagged (not fixed)
- [ ] Test files committed with proper message
- [ ] Coverage gaps documented
- [ ] Next steps presented to user
</success_criteria>


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

This complete authoring guide retains its source content, examples, and methods.
Only recorded namespace/reference substitutions and explicit local conflict
corrections have been made. Source attribution and exact original hashes are
isolated in `.ai/library/THIRD-PARTY-NOTICES.md` and `PROVENANCE.json`.

Read `.ai/library/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/template-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The retained `config.json`, `/workflow:*` commands, tool
names, hooks, and Node CLI examples describe supporting source capabilities;
this import does not install or activate them. Source catalog pointers in examples
identify provenance, not executable command arguments. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
