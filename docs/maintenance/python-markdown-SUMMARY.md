---
phase: maintenance
plan: python-markdown
status: complete
subsystem: workflow-documentation
requirements-completed: []
acceptance: []
documentation: ["engineer/bin/README.md"]
issue_refs: []
plan_head_before: "7723b2d1ce2b0d698613639547c35e2b98688a70"
completed: 2026-10-28
---

# Python Markdown maintenance summary

Executable Node examples in tracked Markdown now use working Python snippets or
Python runtime verbs. This is template maintenance; the adopting project's
identity and all planning records remain unfilled and unchanged.

## Accomplishments

- Migrated JSON extraction, validation, review frontmatter, commit formatting,
  worktree manifests, recovery sentinels, HTTP checks, module/package inspection
  and specification probes. Removed obsolete CJS resolver/build instructions.
- Added thin `review.parse-flags` and `review.resolve-depth` adapters over the
  existing canonical Python ports. They preserve equals-form flags, unrelated
  reviewer-lane flags, `paths[]` rules, strongest matching depth and downgrade
  behavior. `review.evidence-lines` preserves external reviewer warnings.
- Routed disposition construction through the existing `review.reconcile`
  implementation and retained its behavioral regression suite. Updated obsolete
  tests of embedded JavaScript source to identify the current Python owner.
- Added `scripts/check_markdown_python.py`, covering every Git-tracked Markdown
  path, hidden directories, case-insensitive `.md`/`.markdown` suffixes, inline
  and fenced commands, eval/print/test/heredoc forms, executable paths, wrappers,
  continuations and retired helper invocations. Its regression test runs during
  ordinary unittest discovery. No path allowlist hides direct invocations.
- Retained generic JavaScript application examples and adopting-project npm/npx
  commands. Node names in prose, ecosystem identifiers and guard matcher data
  remain where they describe actual concepts rather than invoke the executable.
  Historical invocation cells now describe retired helpers. Windows process
  cleanup uses an explicitly owned PID rather than a runtime-wide process kill.

## Checks

All commands ran from the assigned isolated checkout on `codex/python-markdown-129`.

| Command | Observed result |
|---|---|
| `python scripts/check_markdown_python.py` | Baseline inventory: 560 Markdown files, zero findings. Final staged inventory including this summary: 561 files, zero findings. |
| `python -m unittest discover -s tests -p test_markdown_python.py` | 14 tests passed. Actual documented snippets exercised against fixtures, including 24 distinct migrated inline Python forms, an actual Bash flag/depth pipeline, malformed input, status codes, quoting, spaces, Unicode and HTTP responses. |
| `python -m unittest discover -s tests -p test_spec_probes.py -v` | 2 tests passed, including all bundled edge-probe oracle fixtures. |
| `python -m unittest discover -s tests -p test_code_review_flags.py -v` | 16 tests passed. |
| `python -m unittest discover -s tests -p test_code_review_depth.py -v` | 55 tests passed. |
| `python -m unittest discover -s tests -p test_runtime_launcher_parity.py` | 59 tests: passed with 5 existing skips and 2 expected failures. |
| `python -m unittest discover -s tests -p test_code_review_pipeline_regression.py` | 172 tests: passed with 39 existing skips and 5 expected failures; includes the actual Python disposition ledger behavior. |
| `python -m unittest discover -s tests -p test_agent_sources.py -k SkillMirror` | 3 tests passed; command/skill mirrors preserved. |
| `git diff --check` | No whitespace errors. |

The launcher and pipeline suites used a PowerShell process-local PATH prefix:
`$env:PATH = 'C:\Program Files\Git\usr\bin;' + $env:PATH`. The initial launcher
run failed one standalone-launcher fixture because its inherited Git Bash PATH
lacked `dirname`; the unchanged launcher passed after supplying that directory.

## Remaining and limits

No required migration gap remains in the scanned Markdown inventory. Independent
review and publication belong to the coordinator. The entire repository test
suite was not run; checks above target the changed behavior and its existing
regression suites. Existing skips and expected failures remain explicit.
Unrelated parent link/layout debt and historical prose references were not
expanded into a general cleanup. No new dependency was introduced.

## Threat surface

None identified beyond the assigned existing JSON/file/HTTP helper surfaces.
The migration retains quoted argv and stdin boundaries, malformed-input guards,
regular-file checks and the existing runtime's disposition safeguards.
