---
component: verifier
version: 2
last_calibrated: 2026-03-25
calibration_source: "Adapted from thinking-partner verification corpus"
---

# Verifier Few-Shot Examples

All paths, counts and outputs below are illustrative examples, not files or test
results in this repository. Apply the methods to actual assigned source paths.
Provenance: [third-party notices](../../../THIRD-PARTY-NOTICES.md).

## Positive Examples

### Example 1: Thorough multi-level artifact verification with real gap discovery

**Input:** Must-have artifact: `example-project/workflows/context-bridge.md: >50 lines`

**Output:**

> **L1 (Existence):** EXISTS -- `example-project/workflows/context-bridge.md` found, 187 lines.
> **L2 (Substantive):** SUBSTANTIVE -- No TODO/FIXME markers, 4 defined sections (`updateContextTier`, `getContextBudget`, `injectContextWarning`, `resetTierState`), non-trivial logic with config reads and threshold calculations.
> **L3 (Wired):** WIRED -- Referenced by `example-project/workflows/execute-phase.md` at step 3. Called by `example-project/agents/executor.md` via @-reference include. Arguments verified: receives planning directory path matching the expected parameter.
> **Status: PASSED**

**Why this is good:** The verifier checked all three levels independently with specific evidence at each level -- file path, line count, exported symbols, import location, and argument verification. It did not stop at "file exists" but traced wiring through to actual usage with correct arguments.

### Example 2: Correct FAILED classification with grep evidence

**Input:** Must-have truth: `validate-commit.js rejects commits missing scope parentheses`

**Output:**

> **Method:** Ran `grep -n "scope" example-project/tools/validate-commit.js` to locate scope validation logic.
> **Evidence:** Lines 34-41 show regex `/^(feat|fix|refactor|test|docs|chore|wip)\(/` which requires opening paren after type. However, no test for MISSING closing paren exists -- the regex accepts `feat(: description` (missing scope content and closing paren).
> **Ran:** `echo "feat(: test" | node example-project/tools/validate-commit.js` -- exit code 0 (accepted).
> **Status: FAILED** -- Commit messages with empty scope `feat(: desc)` are accepted. The truth "rejects commits missing scope parentheses" does not hold for empty-scope edge case.

**Why this is good:** The verifier did not trust the code's intent -- it ran an actual test with an edge case input and reported the specific failure. Evidence includes the regex, the test command, the exit code, and why the truth does not hold.

### Example 3: Catching missing wiring (calibration-derived gap pattern)

**Input:** Must-have key_link: `check-subagent-output.js imports and calls feedback-loop.js extractFeedback()`

**Output:**

> **Method:** Ran `grep -n "feedback-loop\|extractFeedback" example-project/tools/check-subagent-output.js`.
> **Evidence:** Zero matches. The file `feedback-loop.js` exists (172 lines, substantive), and `tests/feedback-loop.test.js` passes (229 lines). But `check-subagent-output.js` never imports or calls it.
> **Cross-check:** `grep -rn "require.*feedback-loop" example-project/tools/` returns zero results across all scripts.
> **Status: FAILED** -- The artifact exists and is tested, but is completely orphaned. The key_link "imports and calls" does not hold. This is a **missing wiring** gap.

**Why this is good:** The verifier caught a common calibration pattern: code that exists, is tested, but is never actually wired into the system. L1 and L2 pass, but L3 (wiring) fails. Trace callers even when a unit test of the isolated module passes.

### Example 4: Catching missing config schema entries (calibration-derived gap pattern)

**Input:** Must-have truth: `Config toggles features.architecture_graph and features.architecture_guard exist with defaults`

**Output:**

> **Method:** Ran `grep "architecture_graph\|architecture_guard" example-project/tools/lib/config-schema.json`.
> **Evidence:** Zero matches in schema. However, `grep "architecture" example-project/tools/lib/config.cjs` shows both flags in CONFIG_DEFAULTS (lines 426, 428).
> **Gap:** Defaults exist in code but schema validation doesn't know about them. `configValidate()` would strip these fields on load, making the defaults unreachable.
> **Status: FAILED** -- Config flags work in code but are invisible to schema validation. This is a **missing wiring** gap between config layers.

**Why this is good:** The verifier checked multiple config layers (schema vs defaults vs code) rather than just one. Config wiring requires schema + defaults + code to agree -- checking only one layer misses layer-mismatch bugs.

### Example 5: Distinguishing planning gaps from execution failures

**Input:** Must-have truth: `All MSYS regex patterns consolidated into shared module`

**Output:**

> **Method:** Ran `grep -rn "\/\[a-zA-Z\]\/" example-project/tools/` to find inline MSYS regex.
> **Evidence:** 2 matches in `example-project/commands/misc.md` (lines 26, 487). These were NOT in the original plan scope -- Phase 148 extracted code into misc.md AFTER Phase 149's plan was written.
> **Assessment:** The executor correctly completed all planned tasks. The gap is a **planning ordering issue**, not an execution failure.
> **Status: gaps_found if current acceptance requires ALL patterns; otherwise advisory.** Compare the approved scope and revision. Correctly executing an incomplete plan does not establish completion of a broader phase goal.

**Why this is good:** The verifier distinguished between what was planned vs what exists now. Code that changed AFTER plan creation is a planning gap, not an executor failure. Worker responsibility and phase completeness are separate questions; required gaps stay gaps.

## Recurring Gap Patterns

- Missing wiring: a file exists and is tested but no consumer calls it.
- Missing test coverage: the only relevant test is disabled or excluded from CI.
- Configuration mismatch: defaults, schema and consumers disagree.

## Negative Examples

### Example 1: Blanket pass with no per-criterion evidence

**Input:** Must-haves: 5 truths, 3 artifacts, 2 key_links from plan frontmatter.

**Output:**

> All must-haves have been verified. The implementation matches the plan requirements. Files exist and are properly connected. Status: PASSED.
> must_haves_checked: 10, must_haves_passed: 10

**Why this is bad:** No individual must-have is listed or checked. No file paths, no line numbers, no grep output, no level-by-level breakdown. The verifier restated the must-haves as passing without showing any evidence. This would miss stubs, orphaned exports, and broken wiring.

### Example 2: File existence check without substance or wiring verification

**Input:** Must-have artifact: `example-project/tools/lib/audit-checks/index.cjs: >100 lines`

**Output:**

> **L1 (Existence):** EXISTS -- File found at `example-project/tools/lib/audit-checks/index.cjs`, 142 lines.
> **Status: PASSED**

**Why this is bad:** The verifier stopped at Level 1. The file has 142 lines but could contain `// TODO: implement all checks` with stub functions returning empty objects. Level 2 (substantive) and Level 3 (wired) were skipped entirely. A file that exists but is never imported or contains only placeholder code should not pass.
