# UAT Template

Template for `.planning/phases/XX-name/{phase_num}-UAT.md` — persistent UAT session tracking.

**Producer:** verify-work prepares the protocol from committed SUMMARY evidence; the coordinator records actual human responses.
**Consumers:** verify-work, validate-phase, audit-uat and gap planning read results without inventing acceptance.

## Authoring contract

1. Read every source SUMMARY and the actual delivered entry points. Include at least one existing source path; do not generate speculative product features.
2. Give each acceptance obligation an ID and concrete action. State a one-sentence expected result, exact entry point, fixtures and cleanup/preconditions.
3. Separate acceptance obligations from actions. Several actions can support one acceptance obligation; passing one action does not pass unrelated obligations.
4. Present the reply format `N PASS`, `N FAIL <observation>`, `N BLOCKED <reason>`. Record the human's observed words verbatim for failures and acceptance.
5. Record pending without brackets. Require a reason for skips and blocks; preserve unresolved actions and accurate counters.
6. Diagnosis adds root cause and repair evidence while the record stays partial. Do not treat diagnosis as acceptance.
7. Reconcile a resolved gap only when `resolved_by` names an executed plan with an existing matching SUMMARY. Preserve history, `resolved_at` and stable gap IDs. A later regression receives a fresh ID.
8. Complete only when every required action passes and Human acceptance contains an actual explicit human acceptance decision. Until then show `PENDING HUMAN acceptance` and preserve partial status.
9. Link failures to the canonical [UAT issue format](issue.md#uat), preserving action, expected/actual result, source, revision and evidence. Do not claim tests were run when this file is only a prepared protocol.

---

## File Template

```markdown
---
status: testing | partial | complete
phase: XX-name
source: ["XX-01-SUMMARY.md"] # One or more existing SUMMARY paths
started: [ISO timestamp]
updated: [ISO timestamp]
---

## Current Test

<!-- OVERWRITE each test - shows where we are -->

number: [N]
name: [test name]
expected: [One sentence stating the observable result]
entry_point: [URL, route or exact entry command]
fixtures: [Required account, data and setup]
awaiting: user response or final human acceptance decision

## Acceptance checklist

- [ ] [Acceptance ID and observable outcome linked to source SUMMARY]
- [ ] [Required human judgment and reason]

## Tests

### 1. [Acceptance / action name]

acceptance: [Acceptance ID]
action: [Exact action the human performs]
entry_point: [URL / route / command]
fixtures: [Required data]

expected: [observable behavior - what user should see]
result: pending

### 2. [Test Name]

expected: [observable behavior]
result: pass

### 3. [Test Name]

expected: [observable behavior]
result: issue
reported: "[verbatim user response]"
severity: major

### 4. [Test Name]

expected: [observable behavior]
result: skipped
reason: [why skipped]

### 5. [Test Name]

expected: [observable behavior]
result: blocked
blocked_by: server | physical-device | release-build | third-party | prior-phase
reason: [why blocked]

...

## Human acceptance

status: PENDING HUMAN acceptance
accepted_by: ""
accepted_at: ""
decision: ""

Record the actual human's final acceptance words and identity. Automated checks, source inspection, a resolving plan, silence and mode flags do not fill this block.

## Summary

total: [N]
passed: [N]
issues: [N]
pending: [N]
skipped: [N]
blocked: [N]

## Gaps

<!-- YAML diagnosis and gap-planning input; preserve stable gap IDs. -->

- truth: "[expected behavior from test]"
  status: failed | resolved
  reason: "User reported: [verbatim response]"
  severity: blocker | major | minor | cosmetic
  test: [N]
  root_cause: "" # [diagnosis pending]
  artifacts: [] # [diagnosis pending]
  missing: [] # [diagnosis pending]
  debug_session: "" # [diagnosis pending]
  resolved_by: "" # Written by verify-work's reconcile_gaps (#1921) when # an executed gap-closure plan resolves this gap — # never author this directly. Plan basename.
  resolved_at: "" # Written alongside resolved_by (#1921).
```

---

<section_rules>

**Frontmatter:**

- `status`: OVERWRITE - "testing", "partial", or "complete"
- `phase`: IMMUTABLE - set on creation
- `source`: IMMUTABLE - SUMMARY files being tested
- `started`: IMMUTABLE - set on creation
- `updated`: OVERWRITE - update on every change

**Current Test:**

- OVERWRITE entirely on each test transition
- Shows which test is active and what's awaited
- On completion: "[testing complete]"

**Tests:**

- Each test: OVERWRITE result field when user responds
- `result` values: pending, pass, issue, skipped, blocked
- If issue: add `reported` (verbatim) and `severity` (inferred)
- If skipped: require `reason`; skipping does not pass the action
- If blocked: require `blocked_by` (tag) and `reason`; stop only dependent actions

**Summary:**

- OVERWRITE counts after each response
- Tracks: total, passed, issues, pending, skipped, blocked

**Gaps:**

- APPEND only when issue found (YAML format)
- After diagnosis: fill `root_cause`, `artifacts`, `missing`, `debug_session`
- This section feeds `/plan-phase` gap correction alongside Findings and Acceptance
- `status: resolved` (#1921, #4983): when `/verify-work`'s `reconcile_gaps`
  step finds an executed gap-closure plan (a `*-PLAN.md` naming this entry's
  `gap_id` with a matching `*-SUMMARY.md`), it updates the entry IN PLACE —
  `status: failed` → `status: resolved` — and adds `resolved_by` (the
  resolving plan's basename) and `resolved_at` (the date). A resolved entry
  is no longer surfaced as an open gap, and its matching `### N.` test's
  `result: issue` no longer blocks `phase uat-passed` — but only when
  `resolved_by` names a plan that actually exists in the phase directory with
  a matching SUMMARY; a hand-written `status: resolved` with no valid
  `resolved_by` still blocks (the Python runtime UAT completion predicate).
  A later regression against the same test gets a fresh `gap_id`, never a
  reopened resolved one.

</section_rules>

<diagnosis_lifecycle>

**While status is partial, if gaps exist:**

1. User runs diagnosis (from verify-work offer or manually)
2. diagnose-issues workflow spawns parallel debug agents
3. Each agent investigates one gap, returns root cause
4. UAT.md Gaps section updated with diagnosis:
   - Each gap gets `root_cause`, `artifacts`, `missing`, `debug_session` filled
5. status remains "partial"
6. Ready for /plan-phase --gaps with root causes

**After diagnosis:**

```yaml
## Gaps

- truth: "Comment appears immediately after submission"
  status: failed
  reason: "User reported: works but doesn't show until I refresh the page"
  severity: major
  test: 2
  root_cause: "useEffect in CommentList.tsx missing commentCount dependency"
  artifacts:
    - path: "src/components/CommentList.tsx"
      issue: "useEffect missing dependency"
  missing:
    - "Add commentCount to useEffect dependency array"
  debug_session: ".planning/debug/comment-not-refreshing.md"
```

</diagnosis_lifecycle>

<lifecycle>

**Creation:** When /verify-work starts new session

- Extract tests from SUMMARY.md files
- Set status to "testing"
- Current Test points to test 1
- All tests have result: pending

**During testing:**

- Present test from Current Test section
- User responds `N PASS`, `N FAIL <observation>`, or `N BLOCKED <reason>`
- Update the identified action result (pass/issue/blocked; skipped needs an explicit reason)
- Update Summary counts
- If issue: append to Gaps section (YAML format), infer severity
- Move Current Test to next pending test

**On completion:**

- Set status to "complete" only when every required action passes and Human acceptance records the actual human decision; otherwise retain "partial"
- Current Test → "[testing complete]"
- Commit file
- Present summary with next steps

**Partial completion:**

- status → "partial" (if pending, blocked, or unresolved skipped tests remain)
- Current Test → "[testing paused — {N} items outstanding]"
- Commit file
- Present summary with outstanding items highlighted

**Resuming partial session:**

- `/verify-work {phase}` picks up from first pending/blocked test
- When all items resolved, status advances to "complete" only after all actions pass and actual human acceptance is recorded

**Resume after /clear:**

1. Read frontmatter → know phase and status
2. Read Current Test → know where we are
3. Find first pending result → continue from there
4. Summary shows progress so far

</lifecycle>

<severity_guide>

Severity is INFERRED from user's natural language, never asked.

| User describes                                         | Infer    |
| ------------------------------------------------------ | -------- |
| Crash, error, exception, fails completely, unusable    | blocker  |
| Doesn't work, nothing happens, wrong behavior, missing | major    |
| Works but..., slow, weird, minor, small issue          | minor    |
| Color, font, spacing, alignment, visual, looks off     | cosmetic |

Default: **major** (safe default, user can clarify if wrong)

</severity_guide>

<good_example>

```markdown
---
status: partial
phase: 04-comments
source: ["04-01-SUMMARY.md", "04-02-SUMMARY.md"]
started: 2025-01-15T10:30:00Z
updated: 2025-01-15T10:45:00Z
---

## Current Test

awaiting: final human acceptance decision
[Action 2 remains failed; repair and retest before acceptance.]

## Tests

### 1. View Comments on Post

expected: Comments section expands, shows count and comment list
result: pass

### 2. Create Top-Level Comment

expected: Submit comment via rich text editor, appears in list with author info
result: issue
reported: "works but doesn't show until I refresh the page"
severity: major

### 3. Reply to a Comment

expected: Click Reply, inline composer appears, submit shows nested reply
result: pass

### 4. Visual Nesting

expected: 3+ level thread shows indentation, left borders, caps at reasonable depth
result: pass

### 5. Delete Own Comment

expected: Click delete on own comment, removed or shows [deleted] if has replies
result: pass

### 6. Comment Count

expected: Post shows accurate count, increments when adding comment
result: pass

## Summary

total: 6
passed: 5
issues: 1
pending: 0
skipped: 0
blocked: 0

## Human acceptance

status: PENDING HUMAN acceptance
accepted_by: ""
accepted_at: ""
decision: ""

## Gaps

- truth: "Comment appears immediately after submission in list"
  status: failed
  reason: "User reported: works but doesn't show until I refresh the page"
  severity: major
  test: 2
  root_cause: "useEffect in CommentList.tsx missing commentCount dependency"
  artifacts:
  - path: "src/components/CommentList.tsx"
    issue: "useEffect missing dependency"
    missing:
  - "Add commentCount to useEffect dependency array"
    debug_session: ".planning/debug/comment-not-refreshing.md"
```

</good_example>

## Historical gap reconciliation and final human evidence

A historical `result: issue` may stop blocking only through the preserved resolved-gap path: valid stable gap_id, resolved_by and resolved_at; an executed resolving PLAN; a complete matching committed SUMMARY with specific evidence for that gap; and final actual Human acceptance of the covered build. Every remaining required current action must pass. Skipped, not-testable, blocked and pending required actions remain blocking.

If explicit human retest is required, record that actual retest pass; never assume it from a SUMMARY. Diagnosis, a relabeled status, a checked item or a resolving commit alone is insufficient. This narrow historical effective-resolution path preserves the original issue evidence and does not manufacture final human acceptance.
