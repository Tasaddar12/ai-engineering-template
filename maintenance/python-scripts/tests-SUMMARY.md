# Python review regression migration

## Why

The review workflow now dispatches installed Python runtime verbs. Regression tests still
searched for removed JavaScript source snippets and CJS resolver blocks, preventing them
from checking the shipped behavior. The coordinator authorized this bounded test migration
and explicitly authorized preserving genuine source-dependent failures for integration repair.

## Identity and scope

- Root: `D:/Codex Projects/ai-engineering-template/.worktrees/scripts-tests-201409231`
- Branch: `phase-scripts-tests-201409231`
- Input revision: `f383757251565b869495a71fdffec9b1c0a24dd5`
- Owned changes: `tests/test_code_review_pipeline_regression.py` and this summary only.
- Frozen combined document evidence: `901448a60e1c9afeaff5c5d4a058e5afc41f7daf`.

## Changes

- Replace retired JavaScript scope assertions with registered CLI fixtures for SUMMARY
  parsing, section boundaries, root/nested paths, extensionless build files, narrative
  suffixes, and project containment. Preserve the passing pure-helper regression cases.
- Execute shipped Bash fences with actual Python runtime results for critical/blocker
  display, report-status acceptance, and the 50/51-file depth downgrade boundary.
- Execute the shipped identity-checked launcher preamble against copied Python installs:
  explicit launcher, runtime directory, project Claude/Codex, global installation, PATH,
  missing/malformed runtime, shell-function decoys, and symlinks where supported.
- Replace stale Node-only ledger skips with real Python CLI coverage for CRLF/pipe reasons,
  count boundaries/invalid values, directory/symlink/FIFO refusal, iteration precedence,
  literal shell metacharacters, absent review, displaced decision history, and a real
  reachable Git fix receipt. Check canonical finding tiers and reviewer-emitted IDs through
  the parser instead of inspecting JavaScript regular expressions.
- Check the shipped Python adapter invocation against the Windows command-line budget.
  Pure extraction-helper unit cases remain, including historical Node-text parsing fixtures.
- New subprocess fixtures explicitly encode source and captured output as UTF-8.

## Verification

At the input revision with the authored test changes:

- `python -m unittest tests.test_code_review_pipeline_regression -q`: **194 tests in
  55.183 seconds; 7 failing assertions, 30 skips, 5 expected failures, no errors**.
- Targeted launcher plus ledger legend suite: **13 tests, OK, 1 host symlink-permission skip**.
- Targeted review options plus fix reachability: **7 tests, 1 failure** at the legitimate
  51-file depth downgrade regression; the actual Git fix-receipt path passed.
- The adapter budget test, loaded with the disposition document read using `git show`
  from frozen combined revision `901448a60e1c9afeaff5c5d4a058e5afc41f7daf`: **1 test, OK**.
- `git diff --check`: passed.

## Integration-dependent failures

No new failure was converted into a skip or expected failure. The seven assertions are:

1. SUMMARY em-dash/parenthetical stripping: two test methods fail because
   `runtime_tools.py` passes narrative suffixes directly to `safe_path`.
2. The shipped `commit_review` status gate: valid `clean` and `issues_found` subtests fail
   because the captured value contains both the status and the appended `valid` marker.
3. Critical display: the blocker-only subtest reports 0 instead of 8.
4. Effective depth: at 51 files the runtime returns `depth=standard`, but the shipped
   extraction selects `resolvedDepth=deep` and dispatches deep despite logging a downgrade.
5. Adapter invocation: the old input document still embeds Node; this assertion passes
   against the coordinator's already-combined Python adapter document.

The coordinator has the exact source/doc defects for owned repair. Final integrated
verification remains required after those fixes and the converted disposition document
are integrated. Existing five expected failures remain unchanged; residual skips are the
existing Windows slow-shell matrix policy, absent upstream fixtures, and unsupported host
symlink/FIFO capabilities. No source, documentation, planning records, sibling worktrees,
or additional test modules were changed. No publication was performed.
