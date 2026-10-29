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

## Independent-review corrections

The first independent batch found two required corrections in the initial
maintenance slice. Windows' legacy pipe encoding could corrupt non-Latin paths
before review-depth matching, and the scanner missed executable tokens with an
extensionless argument or stdin-only input. The correction slice:

- Makes every migrated inline Python boundary request `-X utf8`; the isolated
  CLI explicitly configures stdin/stdout/stderr as UTF-8. The shared test harness
  now decodes this protocol explicitly, preserving all oracle assertions.
- Tests the actual Bash payload and isolated CLI without UTF-8 environment
  overrides. `src/café/漢.py` stays unchanged and selects the deep `src/café`
  override over the quick default. JSON, raw output, stdin, file input and error
  diagnostics retain Unicode. Scanner diagnostics also retain `café/漢.MD`.
- Parses shell command positions rather than assuming script extensions or
  command flags. Extensionless, redirected-stdin, bare pipeline and quoted
  command-substitution forms are rejected; prose identifiers, browser JavaScript,
  graph-node prose and quoted grep/printf data remain valid.
- Replaces the 30-attempt readiness loop with one monotonic 30-second budget,
  bounding each request and sleep by its remaining time. Deterministic timeout,
  HTTP-error, non-2xx and eventual-success fixtures check the aggregate budget;
  the actual local-HTTP success fixture remains in place.
- Restores quick-review empty/malformed JSON fallback behavior under
  `set -euo pipefail`; labels the Python CLI/module and version-probe examples;
  marks hypothetical verifier results as illustrations; and points the No Node
  check in PLANNED-UPDATES.md at the comprehensive scanner.

Correction checks (same command forms as above, after the corrections):

| Test module / check | Result |
|---|---|
| `test_markdown_python.py` | 19 tests passed, including all review reproductions and default-environment Unicode boundaries. |
| `test_engineer_runtime.py` | 9 tests passed. |
| `test_code_review_pipeline_regression.py` | 172 tests passed with 39 existing skips and 5 expected failures. |
| `test_runtime_launcher_parity.py` | 59 tests passed with 5 existing skips and 2 expected failures; Git usr/bin PATH prefix as above. |
| `test_spec_probes.py` | 2 tests passed; UTF-8 oracle comparison preserved. |
| `test_code_review_flags.py` / `test_code_review_depth.py` | 16 / 55 tests passed. |
| Comprehensive scanner | 561 tracked Markdown files, zero findings. |
| `git diff --check` | No whitespace errors. |

The correction slice starts from `60446c1a8a969a1fbc2e5ddd79b5b890b0ea1893`.

## Final boundary corrections

Fresh review reproduced additional ordinary shell/Markdown forms and a real
slow-header response that exceeded the previous in-process deadline. Starting
from `09665d3e1c2cee6a658f6d579e99f9d632c805b9`, this slice:

- Parses balanced, quote-aware command substitutions; wrapper options and their
  operands; timeout duration suffixes; quoted shell command strings; and
  blockquote/list-contained code fences. Variable names and user names used as
  option operands remain data. Escaped and single-quoted literals stay excluded.
  Command-shaped prose is scanned, and original source line locations survive
  Markdown container normalization. No path allowlist was introduced.
- Uses a portable inline stdlib subprocess supervisor for the .ai readiness
  example. It enforces the 30-second total budget outside the polling worker,
  kills the child on expiry and waits for it to exit. This works without an
  installed engineer runtime and bounds a per-byte slow HTTP header read.
- Restores nonempty JSON string acceptance in both verifier examples, alongside
  list/object acceptance. Empty strings and scalar numbers/booleans/null fail.

`python -m unittest discover -s tests -p test_markdown_python.py -v` passes all
21 tests. The real slow-header fixture uses a 0.6-second budget, confirms the
connection and incomplete header read, observes failure within 2 seconds and
checks that the child was terminated and reaped. Deterministic timeout,
HTTP-error, non-2xx and eventual-success checks remain; all prior Unicode and
quick-scope fallback checks still pass. The current inventory scan remains
561 tracked Markdown files with zero findings; `git diff --check` is clean.
Unchanged broad runtime suites were not repeated for these bounded example and
scanner changes.

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
