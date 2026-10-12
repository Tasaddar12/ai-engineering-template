---
maintenance: issue-validation
status: complete
acceptance: []
requirements-completed: []
documentation:
  - .ai/templates/issue.md
  - .ai/templates/UAT.md
  - .ai/workflows/add-todo.md
  - .ai/workflows/check-todos.md
  - .ai/workflows/verify-work.md
  - .ai/references/git-workflow.md
  - .ai/runtime/README.md
plan_head_before: 04880c2f89533ff44d9620637e965e9b3ea135c5
---

# Issue structural validation and UAT lifecycle corrections

## Scope and identity

Standalone authorized template maintenance in
`D:/Codex/2026-10-12/task-15/validation-worker`, branch
`codex/issue-validation-worker`, base
`04880c2f89533ff44d9620637e965e9b3ea135c5`.
No adoption identity, phase/quick task or shared planning records changed.
Context usage: unavailable. The assignment supplied the exact worker root/branch
but no executable root-pin block; repository identity was checked directly.

## Changes

- `issue_format.py` derives canonical variant names, required ordered headings,
  UAT table columns and Human acceptance field names from the existing
  `templates/issue.md` beside its own runtime namespace. Source `.ai` and
  installed `.codex`/`.claude` resolve independently of the caller's directory.
  Missing or malformed schemas and missing/unknown variants fail closed.
- `todo.issue-publish` requires explicit `--variant` and calls validation before
  provider access or create-attempt persistence. Existing body marker,
  freshness/duplicate/intent/recovery/readback guards remain intact. Fenced or
  indented code, block quotes and HTML comments cannot supply required headings
  or the UAT table. UAT requires a canonical contiguous table with sequential
  numbered nonempty rows and the ordered acceptance fields.
- Read-only `issue.validate --variant VARIANT --body-file PATH` provides the
  same check before separately authorized direct writes. Consumers document
  the exact canonical names and the supported-path boundary. Direct `gh`/API
  writes bypass this runtime gate. No semantic deduplication, URL/UI validation,
  content-quality review or actual human-decision verification is claimed.
- CR-01: all required actions passing with the final human decision pending is
  explicitly `partial`, with only `awaiting: final human acceptance decision`
  in Current Test and no invented test. Completion/resume require the same
  passing-actions AND actual-decision predicate; pending reviewer/date/decision/
  evidence remain pending until actual final feedback. PASS replies alone do
  not supply that decision.
- CR-02: issue indexes preserve the canonical issue UAT headings/table and Human
  acceptance fields, replace the standalone reply sentence, and collect results
  only in linked tests. Index decision/evidence references actual linked-test
  decisions; no separate row replies or duplicate acceptance action.
- `issue.md` remains the canonical issue body; existing `UAT.md` remains phase
  session tracking. Canonical readiness guidance requires successful saving,
  actual issue-body readback, and saved links/launch-entry checks against the
  prepared UI. Authoring/publication errors need repair; missing prerequisites
  stay BLOCKED and real product failures stay FAIL/unresolved. Structural PASS
  or a local draft never supplies readiness; uncertain creates retain recovery.
- The older actionable-UAT summary labels its no-validator findings historical
  and links this slice without changing its historical check results.

## Checks

Initial-slice evidence for `3a6bf5af227853073109798256094f313022eb82`;
the later review correction and its fresh checks are recorded below.

Python 3.13.14; evidence is the assigned base plus owned working-tree changes.
Final observed check results are recorded below before the commit.

- `python -m compileall -q .ai/runtime`: PASS.
- `python -m unittest discover -s tests -p test_issue_format.py -v`: PASS,
  8 tests covering all five variants; missing/unknown variants; missing,
  out-of-order, duplicate and literal headings; UAT columns/rows/acceptance;
  malformed/missing/derived schema; installed namespace ownership.
- `python -m unittest discover -s tests -p test_todo_issues.py -v`: PASS,
  32 tests, 1 Windows symlink skip. This run contained all 31 prior safety tests
  plus the structural publication regression. The later added schema regression
  was run separately rather than repeating the full safety suite.
- `python -m unittest discover -s tests -p test_todo_issues.py -k schema -v`:
  PASS, 1 test for missing/malformed installed schema before mutation.
- `python -m unittest discover -s tests -p test_todo_issues.py -k structural
  -k schema -v`: PASS, 2 final regressions asserting no new provider calls or
  TODO/attempt persistence on structural/schema failures. Together these runs
  cover all 33 TODO tests in the initial-slice source (the two focused tests repeat).
- `python -m unittest discover -s tests -p test_workflow_links.py -v`: PASS,
  3 tests on the completed navigation tree.
- `python C:/Users/killi/AppData/Local/Temp/issue-validation-export-check.py
  D:/Codex/2026-10-12/task-15/validation-worker`: PASS. The transient check uses
  the existing InstallerTests fixture copied from this working tree and actual
  installer calls for Codex and Claude. Nine relevant exported runtime/template/
  consumer files match the generated payload with LF normalization; each host's
  installed CLI accepts all five variants and rejects a malformed draft.
- `git diff --check`: PASS; exact owned paths and empty pre-stage index inspected.

## Decisions and deviations

Explicit canonical `--variant` was selected over inferred compatibility, so
missing/unknown variants cannot silently choose a schema. The only additional
owned path was the coordinator-authorized historical summary clarification.
The first structural test run exposed greedy multiline variant extraction;
newline-bounded extraction corrected it, and the focused rerun passed.
An interim navigation run found the new summary link before this summary existed;
the final navigation run verifies the completed tree.
The first transient installer comparison encountered Git checkout CRLF
normalization of Python files; the corrected check compares LF-normalized
content and executes both installed CLIs, without claiming byte identity.

## Review correction: literal HTML and mixed indentation

Independent review of integrated `21cbe48` found a structural bypass: canonical
Bug/UAT bodies inside `<pre>` and UAT table lines prefixed by space-plus-tab
were accepted even though the rendered headings/table were literal code.
The correction started from worker commit
`3a6bf5af227853073109798256094f313022eb82`; `git diff --stat 21cbe48 HEAD`
was empty before the correction, confirming identical source trees.

`visible_lines` now tracks `pre`, `script`, `style` and `textarea` raw HTML
blocks case-insensitively through their closing tag and computes leading
indentation using four-column tab stops. Literal-only headings/tables cannot
supply the required shape. Fenced examples do not activate raw-block tracking;
canonical content, ordinary lists/tables and one-to-three-space table indentation
remain accepted. This is a bounded structural parser correction, with no new
dependency, competing schema, publication-state changes or universal enforcement
claim. Direct writes and author/UI/content verification retain their stated
limitations.

Fresh correction evidence on that worker commit plus the four owned changes:

- RED: `python -m unittest discover -s tests -p test_issue_format.py -k
  html_literal -k mixed_indent -v` exited 1 before the repair: 2 tests with
  12 failure reports reproduced accepted literal shapes.
- `python -m compileall -q .ai/runtime`: PASS.
- `python -m unittest discover -s tests -p test_issue_format.py -v`: PASS,
  11 tests, including direct Bug/UAT raw-block rejection, mixed-indentation
  rejection and preserved actual structure/code/list/table examples.
- `python -m unittest discover -s tests -p test_todo_issues.py -k literal
  -k structural -k schema -v`: PASS, 3 focused tests. The new publication test
  verifies 11 literal drafts (Bug/UAT across four raw tags and UAT across three
  mixed-indent prefixes); every draft returns `issue-format` with exit status 1,
  leaves the TODO and prepared attempt metadata byte-identical, adds no provider
  calls and creates no issue.
- `git diff --check`: PASS. Only `issue_format.py`, the two assigned test files
  and this summary changed. The full TODO safety suite was not repeated because
  no publication-state/safety logic changed; the coordinator owns its integrated
  frozen-revision suite and fresh independent review.

This correction is committed separately from the initial slice. Its exact hash
is returned in the worker handoff; no push, publication, merge or branch switch.

## Review correction: multiline/raw HTML boundaries

The next independent review of frozen integrated `ba33cc2` found that a raw
literal tag name ending its line (`<pre` followed by `>` or attributes on the
next line) bypassed the opening-tag condition. The reviewer subsequently
identified raw `div`/`table` wrappers around the canonical UAT table and asked
for direct checks of comment-prefix removal and PI/declaration/CDATA blocks.
Correction base: `500ca344bcb4935bbbaeb634e2884d8aedfbbc77`;
`git diff --stat ba33cc2 HEAD` was empty before editing.

The tag-name lookahead now includes end-of-line. Delimiter-ended raw blocks
retain their closing-boundary handling; other line-start HTML tag blocks are
conservatively ignored through the next blank line. Comments are handled as raw
blocks rather than globally deleted, so comment prefixes cannot manufacture
headings/table rows. Processing instructions, declarations and CDATA use their
own terminators. Canonical Markdown, ordinary code/list/table content, unrelated
tags before a separated canonical body, and the existing runtime recovery
marker remain accepted. This remains a bounded structural gate, with no
dependency/schema duplication, provider-state changes, content/UI-quality check
or universal HTML enforcement claim.

Fresh evidence on that correction base plus the four owned changes:

- RED: `python -m unittest discover -s tests -p test_issue_format.py -k
  html_literal -v` exited 1 with 16 multiline-opening failures before repair.
- RED: `python -m unittest discover -s tests -p test_issue_format.py -k
  raw_html_tables -k comment_prefixes -v` exited 1 with 11 failure reports.
  A follow-up `-k comment_prefixes` run, allowing every case to execute,
  independently confirmed all six comment/PI/declaration/CDATA bypasses.
- `python -m compileall -q .ai/runtime`: PASS.
- `python -m unittest discover -s tests -p test_issue_format.py -v`: PASS,
  13 tests covering final boundary handling and preserved actual structure.
- `python -m unittest discover -s tests -p test_todo_issues.py -k literal
  -k structural -k schema -v`: PASS, 3 focused tests. The literal publication
  regression covers 41 drafts, including multiline literal tags, raw div/table
  wrappers, comment-prefixed headings/rows and PI/declaration/CDATA wrappers.
  Every rejected draft returns `issue-format` and exit 1, leaves prepared TODO
  metadata/body byte-identical, adds no provider call and creates no issue.
- `python -m unittest discover -s tests -p test_issue_format.py -k
  literal_examples -v`: PASS, 1 focused positive test after strengthening the
  unrelated-tag example; the subsequent full 13-test run includes that check.
- `git diff --check`: PASS. Only the helper, two assigned test files and this
  summary changed. No full safety-suite repeat: provider-state logic was not
  changed, and the coordinator owns final frozen-suite/review reconciliation.

This correction is committed separately; its full hash is returned in the
handoff. No worker push, publication, merge or branch switch.

## Remaining and handoff

No product UAT performed: this is an unfilled workflow template with no adopting
UI. Actual entry points, visible controls, safe content and human decisions
remain author/coordinator verification. Coordinator owns independent review,
integration and PR #71 publication. No worker push, remote issue edits, merge,
branch switches or broad benchmark. Commit hash is returned in the handoff.
