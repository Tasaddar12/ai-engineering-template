# UAT Template

Template for `.planning/phases/XX-name/{phase_num}-UAT.md` — persistent UAT session tracking.

**Producer:** verify-work prepares the protocol from committed SUMMARY evidence; the coordinator records actual human responses.
**Consumers:** verify-work, validate-phase, audit-uat and gap planning read results without inventing acceptance.

## Authoring contract

1. Read every source SUMMARY in full and inspect the actual delivered entry points and controls. Cite at least one existing source path for every acceptance obligation; do not invent product behavior.
2. Give each acceptance obligation a stable ID and one-sentence observable result. Link each obligation to its source SUMMARY deliverable ID (`D1`, `D2`, etc.) where available.
3. Write an exact, runnable human action for every test: actual full delivered URL (including required trailing slash), or the supplied launcher and exact keys/steps; name fixtures, preconditions, safe cleanup and the expected visible result. Verify these against the delivered UI before publication.
4. Keep a numbered test index that links obligations to the test numbers and source deliverables. Record action results only in those linked tests; do not add duplicate index-row results or a second acceptance checklist that can contradict the tests.
5. Use only `N PASS`, `N FAIL <observation>`, and `N BLOCKED <reason>` for human action replies. Capture the user's actual words verbatim for failures and final acceptance; never invent an observation.
6. Keep pending actions explicit, require a reason for skips and blocks, and recalculate accurate counters after each response. A skipped, not-testable, blocked or pending required action does not pass.
7. Diagnosis may add supported root cause, artifact, missing-behavior and investigation evidence while the record remains `partial`; diagnosis never changes an action result or supplies acceptance.
8. Reconcile a historical issue only through an executed resolving plan and matching committed SUMMARY, preserving the original failure, stable gap ID, `resolved_at`, and any required human retest. A regression receives a new gap ID.
9. Complete only when every required current action passes and Human acceptance records an actual explicit decision from the human. Until then preserve `PENDING HUMAN acceptance` and partial status. Link defects to the canonical [UAT issue format](issue.md#uat) with action, expected/actual result, source, revision and evidence. The maintainer records build, provenance, access, fixtures and bundle details in a separate maintainer-owned preparation record; the human performs the acceptance actions and owns the acceptance decision. Never claim a run based on a prepared protocol.

---

### Prepare the delivered entry point and evidence

Copy only the File Template into a phase session. Fill the visible placeholders at their stated size and remove unused fields and authoring prompts. Do not put hidden comments or authoring rationale into the delivered human protocol. The [UAT issue variant](issue.md#uat) is the canonical provider body; its saved-issue readback and publication-repair duties still apply.

Start with one exact accessible delivered URL, including the full path and required trailing slash, or a directly runnable supplied launcher. Verify that it opens the selected build and expected startup screen. A homepage, package name or guessed route is insufficient. For a Windows launcher, give the actual sequence: `Win+R`, paste the full prepared path, then press `Enter`; identify the startup screen the human should see. The maintainer selects the source and build before handoff, rather than asking the human to choose.

Use two to four observable outcomes, each mapped to approved acceptance IDs and numbered actions. Every action names the actual visible screen, button, field or object, exact click/key sequence and concrete safe fixture values. Give each action its own visible expected result. Inspect labels and key behavior against the delivered UI before publication. An unavailable function or unverified entry point is BLOCKED with its missing prerequisite, and dependent actions remain unresolved. Do not edit the protocol to hide a genuine product failure.

### Keep maintainer preparation separate from human acceptance

The AI/maintainer selects and prepares the build, credentials or test session, data and extracted packages; records hashes, versions and provenance; runs technical checks; gathers evidence; and prepares bundles. Never assign those engineering preparation tasks to the human reviewer.

Link one separate, accessible maintainer-owned record containing:

| Preparation fact | Required record |
|---|---|
| Build identity | Exact build/version and full source commit |
| Artifacts | Actual artifact hashes, versions and prepared bundle reference |
| Environment | Relevant platform, configuration and actual ready/blocked state |
| Access and fixtures | Prepared safe session/data references, without publishing secrets |
| UI inspection | Evidence for the delivered entry point, controls, labels and key behavior |
| Technical checks | Exact executed commands, results, revision and limitations |

The human need not read or compare this preparation record. A successful maintainer check supplies preparation evidence, never the human's acceptance. Keep `PENDING HUMAN acceptance` until the actual decision is recorded. Silence, skips and source inspection do not imply PASS.

### Use a linked-test index without duplicate reporting

When tests need an index, provide a numbered run order with descriptive linked test names and exact opening actions, not bare issue numbers. Use the same UAT issue variant for a provider index, preserving its headings, order, step table and Human acceptance fields. Each row's Actual outcome / evidence directs reporting to the linked test.

Replace the standalone reply sentence with: "Record action results only in each linked test; no separate index-row replies." Record each reply once in that test. The index decision/evidence references actual linked-test decisions, with no second acceptance action at the index. Verify saved test links and launch instructions after provider readback, repair authoring/publication errors, and recover uncertain creation by exact intent before retrying.

For each action within a test, request `N PASS`, `N FAIL <short observation>`, or `N BLOCKED <reason>`. Preserve the actual human response. Technical diagnosis can append evidence while status remains partial; it cannot manufacture a response or replace required retesting.

## File Template

```markdown
---
status: testing | partial | complete
phase: XX-name
source: ["XX-01-SUMMARY.md"] # One or more existing SUMMARY paths
started: [ISO timestamp]
updated: [ISO timestamp]
---

## Delivered build and preparation

Entry point: [Exact verified delivered URL or full supplied launcher plus keys]
Build: [Selected build/version and full source commit]
Maintainer record: [Accessible separate preparation/provenance/check/bundle record]

## Current Test

<!-- OVERWRITE each test - shows where we are -->

number: [N]
name: [test name]
expected: [One sentence stating the observable result]
entry_point: [Exact delivered full URL including required trailing slash, or supplied launcher plus exact keys/steps]
fixtures: [Required account, data and setup]
awaiting: user response or final human acceptance decision

## Test index

| Acceptance ID | Delivered outcome | Source SUMMARY / deliverable | Linked test numbers |
|---------------|-------------------|-----------------------------|---------------------|
| A1 | [One-sentence observable outcome] | [XX-NN-SUMMARY.md, D1] | [1, 2] |

The numbered tests below are the sole action-result records. The index links outcomes to tests; it has no separate result or acceptance rows. Do not create a second acceptance checklist. Human acceptance is recorded once in the dedicated section below.

## Tests

### 1. [Acceptance / action name]

acceptance: [Acceptance ID]
action: [Exact action the human performs]
entry_point: [Exact delivered full URL including required trailing slash, or supplied launcher plus exact keys/steps]
fixtures: [Required data]

expected: [observable behavior - what user should see]
result: pending

### 2. [Acceptance / action name]

acceptance: [Acceptance ID]
action: [Exact action; include the delivered controls and sequence]
entry_point: [Exact delivered full URL including required trailing slash, or supplied launcher plus exact keys/steps]
fixtures: [Required data, setup and safe cleanup]
expected: [One-sentence observable result]
result: pending

### 3. [Acceptance / action name]

acceptance: [Acceptance ID]
action: [Exact action]
entry_point: [Exact delivered full URL including required trailing slash, or supplied launcher plus exact keys/steps]
fixtures: [Required data, setup and safe cleanup]
expected: [One-sentence observable result]
result: issue
reported: "[verbatim user response]"
severity: major

### 4. [Acceptance / action name]

acceptance: [Acceptance ID]
action: [Exact action]
entry_point: [Exact delivered full URL including required trailing slash, or supplied launcher plus exact keys/steps]
fixtures: [Required data, setup and safe cleanup]
expected: [One-sentence observable result]
result: skipped
reason: [Required reason; skipped actions remain not passed]

### 5. [Acceptance / action name]

acceptance: [Acceptance ID]
action: [Exact action]
entry_point: [Exact delivered full URL including required trailing slash, or supplied launcher plus exact keys/steps]
fixtures: [Required data, setup and safe cleanup]
expected: [One-sentence observable result]
result: blocked
blocked_by: [actual prerequisite category]
reason: [Required concrete blocker and dependent scope]

...

## Human acceptance

status: PENDING HUMAN acceptance
accepted_by: ""
accepted_at: ""
decision: ""

Record the actual human's final acceptance words and identity. Automated checks, source inspection, a resolving plan, maintainer smoke checks, silence and mode flags do not fill this block. The maintainer does not accept on behalf of the human.

## Maintainer preparation reference

Preparation is a separate maintainer-owned record, not a human test result. Link the exact record that identifies the build and tested commit, provenance, access/readiness, bundle or launcher, fixture setup and cleanup, and any technical smoke-check evidence. The maintainer verifies the build is the delivered build, the actual URL or launcher/key sequence works, and the fixtures are safe and ready; the human then performs the linked UAT tests and makes the final acceptance decision. If the exact entry point, access, build or fixture is unavailable, mark only the dependent action `blocked` with its reason. Do not convert a missing prerequisite into a product failure or claim maintainer preparation as user acceptance.

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
- After diagnosis: fill `root_cause`, `artifacts`, `missing`, `debug_session`; keep stable `gap_id` values and source/revision evidence.
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

**While status is partial, if gaps need diagnosis:**

1. The coordinator preserves the failed UAT action and stable gap IDs, then uses `/audit-uat` to inventory actual outstanding UAT records and determine which gaps need investigation. The audit is read-only and does not diagnose or pass a test.
2. The coordinator routes each bounded gap to the existing `debugger` role with the exact repository, branch, revision, source paths, original report and relevant artifacts. There is no `diagnose-issues` workflow in this template.
3. A debugger investigates the assigned gap and returns cited observations, examined paths, likely root cause or unresolved alternatives, affected artifacts, missing behavior and the first next action. Partial findings remain explicitly partial; do not fabricate completion or relaunch finished investigations.
4. After the debugger stops, the coordinator records supported diagnosis evidence in that gap's `root_cause`, `artifacts`, `missing` and `debug_session` fields, preserving the original report and `status: failed`. The UAT session remains `partial`.
5. Once diagnosis is sufficient, the coordinator may route the gap to `/plan-phase --gaps` under the applicable phase authority. Planning, diagnosis and a fix plan do not grant implementation permission or acceptance.
6. After an authorized fix executes, verify the matching committed SUMMARY and gap-specific evidence before reconciling `resolved_by` / `resolved_at`. Retest when required; only the actual human can supply final acceptance.

**After diagnosis:**

```yaml
## Gaps

- truth: "Comment appears immediately after submission"
  status: failed
  reason: "User reported: works but doesn't show until I refresh the page"
  severity: major
  test: 2
  gap_id: "GAP-04-comments-02" # Preserve the actual stable ID assigned to this gap.
  root_cause: "useEffect in CommentList.tsx missing commentCount dependency"
  artifacts:
    - path: "src/components/CommentList.tsx"
      issue: "useEffect missing dependency"
  missing:
    - "Add commentCount to useEffect dependency array"
  debug_session: ".planning/debug/comment-not-refreshing.md"
  resolved_by: ""
  resolved_at: ""
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

## Test index

| Acceptance ID | Delivered outcome | Source SUMMARY / deliverable | Linked test numbers |
|---------------|-------------------|-----------------------------|---------------------|
| A1 | Viewer sees the comment list and accurate count | 04-01-SUMMARY.md, D1 | 1, 6 |
| A2 | Author can create and reply to comments, and the result appears immediately | 04-02-SUMMARY.md, D2 | 2, 3 |
| A3 | Viewer can inspect nested-comment layout and remove their own comment | 04-02-SUMMARY.md, D3 | 4, 5 |

## Tests

### 1. View Comments on Post

acceptance: A1
action: Open the delivered post page and inspect its comments section.
entry_point: https://staging.example.invalid/posts/123/ # Fictional example; replace with the verified delivered URL.
fixtures: Maintainer-prepared test account and post; cleanup documented in the maintainer preparation record.
expected: Comments section expands, shows count and comment list
result: pass

### 2. Create Top-Level Comment

acceptance: A2
action: Open the delivered comments view, create a top-level comment with the prepared fixture, and observe the new comment in the list without refreshing.
entry_point: https://staging.example.invalid/posts/123/ # Fictional example; replace with the verified delivered URL.
fixtures: Maintainer-prepared test account and post; cleanup documented in the maintainer preparation record.
expected: The submitted comment appears in the list immediately with its author information.
result: issue
reported: "works but doesn't show until I refresh the page"
severity: major

### 3. Reply to a Comment

acceptance: A2
action: Use the delivered Reply control on the prepared comment, submit a nested reply, and inspect the thread.
entry_point: https://staging.example.invalid/posts/123/ # Fictional example; replace with the verified delivered URL.
fixtures: Maintainer-prepared test account, post and parent comment; cleanup documented in the maintainer preparation record.
expected: Click Reply, inline composer appears, submit shows nested reply
result: pass

### 4. Visual Nesting

acceptance: A3
action: Open a thread with at least three comment levels and inspect indentation, borders and the maximum depth.
entry_point: https://staging.example.invalid/posts/123/ # Fictional example; replace with the verified delivered URL.
fixtures: Maintainer-prepared three-level comment thread; cleanup documented in the maintainer preparation record.
expected: 3+ level thread shows indentation, left borders, caps at reasonable depth
result: pass

### 5. Delete Own Comment

acceptance: A3
action: Use the delivered delete control on a comment owned by the prepared test account.
entry_point: https://staging.example.invalid/posts/123/ # Fictional example; replace with the verified delivered URL.
fixtures: Maintainer-prepared owned comment with replies; cleanup documented in the maintainer preparation record.
expected: Click delete on own comment, removed or shows [deleted] if has replies
result: pass

### 6. Comment Count

acceptance: A1
action: Compare the displayed comment count with the prepared thread, then create one comment and observe the count update.
entry_point: https://staging.example.invalid/posts/123/ # Fictional example; replace with the verified delivered URL.
fixtures: Maintainer-prepared test account and post; cleanup documented in the maintainer preparation record.
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
  gap_id: "GAP-04-comments-02"
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
  resolved_by: ""
  resolved_at: ""

## Maintainer preparation reference

`.planning/phases/04-comments/04-UAT-PREPARATION.md` (fictional path for this example) records the exact build SHA and provenance, staging access, delivered URL, test account/post fixture, cleanup procedure, and maintainer smoke-check evidence. The human action result above remains `issue`; maintainer preparation is not acceptance.
```

</good_example>

## Historical gap reconciliation and final human evidence

A historical `result: issue` may stop blocking only through the preserved resolved-gap path: valid stable gap_id, resolved_by and resolved_at; an executed resolving PLAN; a complete matching committed SUMMARY with specific evidence for that gap; and final actual Human acceptance of the covered build. Every remaining required current action must pass. Skipped, not-testable, blocked and pending required actions remain blocking.

If explicit human retest is required, record that actual retest pass; never assume it from a SUMMARY. Diagnosis, a relabeled status, a checked item or a resolving commit alone is insufficient. This narrow historical effective-resolution path preserves the original issue evidence and does not manufacture final human acceptance.
