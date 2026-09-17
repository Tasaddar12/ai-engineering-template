# UAT Template

Template for `.planning/phases/XX-name/{phase_num}-UAT.md` — persistent UAT session tracking.

---

## File Template

```markdown
---
status: testing | partial | complete
phase: XX-name
source: [list of SUMMARY.md files tested]
started: [ISO timestamp]
updated: [ISO timestamp]
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: [N]
name: [test name]
expected: |
  [what user should observe]
awaiting: user response

## Tests

### 1. [Test Name]
expected: [observable behavior - what user should see]
result: [pending]

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

## Summary

total: [N]
passed: [N]
issues: [N]
pending: [N]
skipped: [N]
blocked: [N]

## Gaps

<!-- YAML evidence for phase-prepare assignments with mode: gap_closure -->
- truth: "[expected behavior from test]"
  status: failed
  reason: "User reported: [verbatim response]"
  severity: blocker | major | minor | cosmetic
  test: [N]
  root_cause: ""     # Filled by diagnosis
  artifacts: []      # Filled by diagnosis
  missing: []        # Filled by diagnosis
  debug_session: ""  # Filled by diagnosis
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
- `result` values: [pending], pass, issue, skipped, blocked
- If issue: add `reported` (verbatim) and `severity` (inferred)
- If skipped: record the user's explicit decision in `reason` and the CLI `--note`.
- If blocked: record the prerequisite in `blocked_by` and the reason in `reason` and `--note`.

**Summary:**
- OVERWRITE counts after each response
- Tracks: total, passed, issues, pending, skipped, blocked

**Gaps:**
- APPEND only when issue found (YAML format)
- After diagnosis: fill `root_cause`, `artifacts`, `missing`, `debug_session`
- This section feeds directly into phase-prepare with the recorded verification gaps

</section_rules>

<diagnosis_lifecycle>

**When an observed failure creates a gap, diagnose it while `status: partial`:**

1. Coordinator routes the observed failure to bounded debugger diagnosis within the authorized scope
2. Coordinator assigns bounded investigations using the local debugger role
3. Each agent investigates one gap, returns root cause
4. UAT.md Gaps section updated with diagnosis:
   - Each gap gets `root_cause`, `artifacts`, `missing`, `debug_session` filled
5. Retain `status: partial`; store diagnosis in Gaps, not in a new session status
6. Return the diagnosed gaps to `phase-prepare` for repair planning

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

**Creation:** When phase-uat starts new session
- Derive one case per CONTEXT acceptance ID; use SUMMARY files as implementation evidence.
- Set status to "testing"
- Current Test points to test 1
- All tests have result: [pending]

**During testing:**
- Present test from Current Test section
- User responds with pass confirmation or issue description
- Update test result (pass/issue/skipped)
- Update Summary counts
- If issue: append to Gaps section (YAML format), infer severity
- Current Test names the first nonpassing case; select a different remaining case explicitly with `--case N`.

**On completion:**
- Set `status: complete` only when every case result is `pass`.
- Current Test → "[testing complete]"
- Commit file
- Present summary with next steps

**Partial completion:**
- After any recorded response, set `status: partial` while any case is pending, issue/failed, blocked or skipped.
- Keep Current Test on the first nonpassing case with its expected result and `awaiting: user response`.
- Commit file
- Present summary with outstanding items highlighted

**Resuming partial session:**
- Run `python .ai/runtime/phase.py uat PHASE`; inspect the first nonpassing case and preserve prior observations.
- Set `status: complete` only after every case records `pass`.

**Resume after /clear:**
1. Read frontmatter → know phase and status
2. Read Current Test → know where we are
3. Inspect the first nonpassing result and its prior observations; record a new outcome only from fresh user feedback.
4. Summary shows progress so far

</lifecycle>

<severity_guide>

Severity is INFERRED from user's natural language, never asked.

| User describes | Infer |
|----------------|-------|
| Crash, error, exception, fails completely, unusable | blocker |
| Doesn't work, nothing happens, wrong behavior, missing | major |
| Works but..., slow, weird, minor, small issue | minor |
| Color, font, spacing, alignment, visual, looks off | cosmetic |

Default: **major** (safe default, user can clarify if wrong)

</severity_guide>

<good_example>
```markdown
---
status: partial
phase: 04-comments
source: 04-01-SUMMARY.md, 04-02-SUMMARY.md
started: 2025-01-15T10:30:00Z
updated: 2025-01-15T10:45:00Z
---

## Current Test

number: 2
name: Create Top-Level Comment
expected: Comment appears immediately after submission
awaiting: correction and user retest

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


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

Read this complete authoring guide, including its examples and methods.
Source attribution is available in `.ai/THIRD-PARTY-NOTICES.md`.

Read `.ai/agents/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/template-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. Only the documented local runtime commands are installed. Tool names and product
examples do not establish that a tool is available; inspect the actual project
configuration and host capabilities before using them. Bundled supporting methods provide local guidance for explicit assignments;
they do not install additional runtime features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
