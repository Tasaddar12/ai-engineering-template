---
phase: github-publication-templates
reviewed: 2026-11-06T15:23:23Z
depth: standard
base: 97a2f0dc03b739f4ba0ad89dc5f5298269d8cd46
candidate: c6f8db6a1f598e06ee63d8ffb52f1f26f0bd3b27
files_reviewed: 29
files_reviewed_list:
  - .github/ISSUE_TEMPLATE/README.md
  - .github/ISSUE_TEMPLATE/bug.yml
  - .github/ISSUE_TEMPLATE/chore.yml
  - .github/ISSUE_TEMPLATE/decision-required.yml
  - .github/ISSUE_TEMPLATE/docs_issue.yml
  - .github/ISSUE_TEMPLATE/enhancement.yml
  - .github/ISSUE_TEMPLATE/feature_request.yml
  - .github/ISSUE_TEMPLATE/security-risk.yml
  - .github/ISSUE_TEMPLATE/uat.yml
  - .github/PULL_REQUEST_TEMPLATE/enhancement.md
  - .github/PULL_REQUEST_TEMPLATE/feature.md
  - .github/PULL_REQUEST_TEMPLATE/fix.md
  - AGENTS.md
  - CONTRIBUTING.md
  - bin/install_support.py
  - docs/INSTALL.md
  - docs/maintenance/github-templates/REVIEW.md
  - docs/maintenance/github-templates/VERIFICATION.md
  - engineer/bin/README.md
  - engineer/bin/lib/delivery.py
  - engineer/bin/lib/issue_format.py
  - engineer/bin/lib/issues.py
  - engineer/references/git-workflow.md
  - engineer/templates/README.md
  - engineer/templates/issue.md
  - engineer/templates/pull-request.md
  - tests/test_installer_runtime.py
  - tests/test_issue_format.py
  - tests/test_misc_verbs.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
resolved_findings: 2
status: clean
---

# GitHub publication template review

Reviewed the exact assigned base-to-candidate change in the isolated, unchanged
`review` checkout. The removed files were reviewed at the base. No source files
were modified, and no provider publication or merge was performed by this reviewer.

## Narrative Findings (AI reviewer)

No remaining grounded findings in the final candidate. Re-reviewed the complete
assigned base-to-final change, the repair delta from the initial candidate, and
the user-requested expansion to eight issue forms and three distinct PR variants.
The latest requested removal of the default PR template is implemented: only
enhancement, feature and fix remain, with selected runtime validation and no
default file export.
Both initial blockers below are resolved. The installed-guide UAT reference
warning identified by verification is also resolved: the guide now names the
actual source and per-host installed UAT paths without a broken local-install
relative hyperlink.

## No-default final evidence

The final reviewed candidate is
`c6f8db6a1f598e06ee63d8ffb52f1f26f0bd3b27` against base
`97a2f0dc03b739f4ba0ad89dc5f5298269d8cd46`.

- `PY -m unittest discover -s tests -p test_issue_format.py -v`: all 22 tests
  passed in 6.997 seconds, zero skips. Added cases cover canonical selection,
  unknown/path-like names, and a missing selected file in an existing directory.
- `.github/pull_request_template.md` is absent. Installer snapshot/export
  selection now allows only `.github/ISSUE_TEMPLATE/` and
  `.github/PULL_REQUEST_TEMPLATE/`; it has no default-file source/export entry.
  Fresh-install assertions prohibit both a recreated default file and a default
  origin in the ownership manifest. Retention of a previously installed retired
  default is explicitly documented and separate from recreation.
- Independently compared all three current visible PR bodies to their
  `60d4bf9` contents: unchanged. Each selected body passes the actual validator.
  Shared authoring and selection instructions are now in each typed template's
  HTML comment, so there is no required read of the deleted file.
- Independently exercised `delivery.command` with parsed `pr.open --template`
  arguments for enhancement, feature and fix. Each forwarded the exact selected
  name and supplied body to validation. The probe deliberately stopped at
  validation, with Git/provider reads mocked; no push or publication occurred.
- Unknown/path-like template names, including `../fix`, `feature.md`, `default`,
  empty and null, fail with `invalid-pr-template` before the template file read.
  The allowlist check precedes filename construction. A separate legacy-runtime
  probe with no PR directory retained five-section validation, rejected an
  unstructured body and wrote no `.github` or default file.
- Source docs and all three typed-template comments consistently distinguish
  runtime `--template feature` from GitHub URL `template=feature.md`. The runtime
  option selects validation only, while callers supply the composed body. The
  omitted option selects enhancement without creating a default file.
- The eight issue forms, their variant mappings and fallback shapes are unchanged
  from the previously reviewed `60d4bf9` revision. Existing original issue bodies
  remain preserved; prior new-variant probes below still describe unchanged code.
- `git diff --check BASE CANDIDATE` passed and `PY -I scripts/links.py` reported
  zero broken targets. Live old-path mentions are historical-retention docs or
  absence assertions; prior maintenance reports identify their earlier tested
  revision. The source review checkout remained clean.

## Prior expanded-scope evidence at 60d4bf9

The previous expanded-scope reviewed candidate was
`60d4bf943786871a6fe990a9fe7b18e8d7bee768` against base
`97a2f0dc03b739f4ba0ad89dc5f5298269d8cd46`.

- `PY -m unittest discover -s tests -p test_issue_format.py -v`: all 19 tests
  passed in 6.918 seconds, zero skips. Existing all-variant tests now cover the
  eight canonical names, including malformed/missing/order/duplicate-section
  rejection for the new variants.
- Independently parsed all eight `.yml` files using PyYAML 6.0.3. The YAML names
  and Report defaults agree exactly with runtime extraction. For every variant,
  template-derived schema equals the explicit fallback schema. Filled each
  default with safe fixture facts and called the real `issues.validate` function;
  all eight passed. No provider create/edit was invoked.
- `generated_body` rejects Docs issue, Chore and Feature request with
  `reviewed-body-required`, as designed. They accept reviewed, complete bodies
  through the publication validator instead of inventing missing facts.
- All three separate Markdown PR bodies pass the real PR validator and retain
  the original common heading sequence. Their Goal, Changes and check prompts
  distinguish enhancement, feature and fix. The default PR's visible Markdown
  still exactly equals the original base-revision fenced body; its new selection
  instructions are inside the authoring comment.
- Inspected `.github/PULL_REQUEST_TEMPLATE/` export selection and the unchanged
  common local/global destination routing, ownership, conflict, backup and
  manifest handling. The installed-runtime regression now asserts bytes and
  manifest source paths for all three PR variants in both hosts and scopes,
  alongside eight issue forms and the default PR. Actual installer execution
  results belong to the independent verifier's report.
- Source catalogs, contributor/install/runtime instructions and authoring guides
  consistently name the eight issue forms and three PR variants. GitHub's
  [documented `template` query parameter](https://docs.github.com/en/pull-requests/reference/using-query-parameters-to-create-a-pull-request)
  selects a file from `.github/PULL_REQUEST_TEMPLATE/`, matching the instructions.
- `git diff --check BASE CANDIDATE` passed and `PY -I scripts/links.py` reported
  zero broken targets. The review source checkout remained clean.
- The in-repository maintenance reports at this candidate explicitly cover the
  earlier `f12b8234d554d590d1802b989fdb72e496fbf27c` revision. They were read as
  prior evidence, not as proof of this expanded final candidate. This new review
  states its own revision and checks; the coordinator can publish fresh reports.

## Prior repair evidence at f12b823

The following checks were executed at
`f12b8234d554d590d1802b989fdb72e496fbf27c`. The repaired resolver and PR
empty-schema rejection code are unchanged in the expanded final candidate.

- `PY -m unittest discover -s tests -p test_issue_format.py -v`: all 19 tests
  passed in 6.501 seconds at the final candidate, zero skips. This includes
  comment-only, header-free and optional-section-only PR-template rejection,
  plus correct exclusion of authoring-comment headings.
- Independently exercised the real final `github_directory()` with temporary
  namespace/project directories and on-disk ownership manifests. With both
  `.github` directories present, `local` selected the project and `global`
  selected the namespace. Invalid JSON, missing scope, an array, an unknown scope
  and null scope all failed with `issue-schema`. With no manifest, both existing
  namespace and source-project fallback cases passed. Only namespace/root inputs
  were patched; resolution logic and manifest parsing were the actual code.
- Inspected the actual installed transition regression: it covers both Codex
  and Claude, global-to-local and local-to-global, deliberately damaging the
  retained inactive template to prove it is ignored. Full installer execution
  outcomes remain the independent verifier's evidence, not a claim of this
  source review.
- `git diff --check BASE FINAL`: passed. `PY -I scripts/links.py`: passed with
  zero broken targets. Final review checkout remains clean.
- The five issue defaults and visible PR body are unchanged from the initially
  reviewed candidate; the exact-original-content comparisons below still apply.
- Assessed `engineer/workflows/ship.md:206` in its invoking-command context. Its
  generic, unlinked instruction to use the canonical Git workflow and existing
  PR template names no removed path and introduces no broken execution-context
  dependency. Existing body/title examples there predate this migration; no
  additional routing defect was established.

## Resolved findings from initial candidate

The following observations and reproductions apply to
`b0f7df95f3f96c9b7442f6ecca9b0072ea4fb9f2`, not to the final candidate.

### CR-01 — BLOCKER: a malformed PR template disables required-section validation

**File:** `D:/Codex/2026-11-06/task-6/review/engineer/bin/lib/delivery.py:55-58`

**Resolution:** Repair `d0905dd` rejects a present canonical PR template when its
visible required-heading list is empty. The final 19-test run passed the three
malformed-schema regressions and valid-comment handling. No active finding.

**Issue:** A nonempty template now replaces `required` unconditionally with all
visible level-two headings. A comment-only template, a damaged template, or one
whose only headings are the excluded optional sections produces an empty list.
`validate_body("Unstructured body")` then succeeds with none of the required PR
sections. The base implementation retained the five required defaults when it
could not extract a canonical File Template block. This is a regression in the
publication gate, separate from the correct migration of the shipped template.

**Reproduction:** At the candidate, with the actual validator imported from
`engineer/bin`, substituting a comment-only template for the file read accepts
an unstructured body:

```python
from unittest.mock import patch
from lib import delivery

with patch.object(delivery, "read", return_value="<!-- incomplete template -->"):
    delivery.validate_body("Unstructured body")  # unexpectedly returns normally
```

The same file contents supplied to the base function loaded from
`git show 97a2f0dc03b739f4ba0ad89dc5f5298269d8cd46:engineer/bin/lib/delivery.py`
raise `Failure: Missing template sections`. Both outcomes were reproduced with
Python 3.11.9. The mock replaces only filesystem text retrieval; it does not
replace heading extraction or validation.

**Fix:** Extract the derived headings into a separate variable and retain the
existing defaults when the result is empty, or reject a present template without
required headings as a template-schema failure. Add regressions for comment-only
and optional-section-only templates, while retaining the current successful
canonical-template and missing-body-section checks.

### CR-02 — BLOCKER: a global-to-local installation keeps selecting retired global templates

**File:** `D:/Codex/2026-11-06/task-6/review/engineer/bin/lib/issue_format.py:94-97`

**Resolution:** Repair `d0905dd` reads the installed manifest's scope before
choosing a template directory, refuses invalid scope and retains fallback only
for runtimes without a manifest. The final independent reviewer probe described
above passed both scope selections and malformed-scope cases. No active finding.

**Issue:** Template resolution uses namespace-directory existence as the complete
scope decision. Installing globally and subsequently locally for the same target
and host succeeds, and the ownership manifest correctly records `scope: local`.
The installer intentionally preserves retired owned paths, so the former
`<target>/.codex/.github` directory remains. `github_directory()` then selects
that retired directory instead of the active local `<target>/.github` templates.
Issue and PR validation can therefore disagree with the templates used by GitHub
or ignore subsequent local template updates. The same resolver is used for both
hosts, so Claude has the same source-level defect.

**Reproduction:** Independently inspected and reran the verifier's
`verification-logs/check_scope_transition.py` against the frozen candidate. The
script invokes the real installer twice on one disposable target (`--global`,
then `--local`, host Codex), checks both complete results, reads the resulting
manifest, and invokes the actual installed runtime's resolver. Observed:

```text
global installation complete; revision b0f7df95f3f96c9b7442f6ecca9b0072ea4fb9f2
local installation complete; revision b0f7df95f3f96c9b7442f6ecca9b0072ea4fb9f2
Manifest scope: local
Expected local canonical templates: <temporary-target>/.github
Runtime selected templates: <temporary-target>/.codex/.github
AssertionError: Installed local runtime chooses retained global templates
```

The first sandboxed attempt stopped before the resolver with Windows access
denied during atomic replacement of the disposable identity file. Repeating the
same operation with approved test-only execution access reached the resolver and
reproduced the defect above. No real user installation was changed.

**Fix:** For an installed runtime, resolve scope from its ownership manifest and
honor `local` versus `global` explicitly. Do not infer active scope from retired
directory existence. Preserve the source/hand-built-runtime fallback only when
no manifest exists. Add actual installed regressions for scope transitions and
for local project-template edits while retired global templates remain, for
both Codex and Claude; retain the installer's preservation of retired files.

## Initial-candidate checks and overall boundaries

- `PY -m unittest discover -s tests -p test_issue_format.py -v`: all 17 tests
  passed in 6.910 seconds, zero skips. `PY` was
  `D:/Codex/2026-10-16/task-7/python-runtime/python.exe` (Python 3.11.9).
- Parsed all five issue form YAML files with PyYAML 6.0.3. Each Report default
  exactly matches its original base-revision fenced body after trimming only
  trailing whitespace at the end of the body. No issue fields or tables were lost.
- The visible PR template body exactly matches the original fenced PR body after
  removal of the new enclosing guidance comment and boundary whitespace.
- `git diff --check BASE CANDIDATE`: passed.
- `PY -I scripts/links.py`: passed, zero broken targets.
- Searched source for old issue/PR/workflow paths. Remaining references outside
  historical `PLANNED-UPDATES.md` describe intentionally preserved retired
  installation paths or assert their absence from new installations.
- Read installer export selection, destination routing, path protection,
  ownership/conflict handling, installed schema resolution and publication
  callers. The independent verifier owns execution of installer integration
  tests; this report does not claim those outcomes.
- Read project AGENTS and reviewer role; no `CLAUDE.md` or project skill
  directories were present. `agent-skills code-reviewer --skills-only` returned
  an empty skill block.

GitHub's official documentation supports YAML issue forms under
`.github/ISSUE_TEMPLATE`, textarea default values, and Markdown PR templates at
`.github/pull_request_template.md`. Issue forms are not supported for PRs.
Sources: [issue form syntax](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms),
[form schema](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-githubs-form-schema),
and [PR template creation](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository).
This is syntax and source review, not evidence of GitHub rendering on the default
branch, interactive host acceptance, or the complete historical test suite.
