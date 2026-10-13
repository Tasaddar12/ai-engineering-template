# GitLab TODO issue publication maintenance summary

Implemented configured self-hosted GitLab support behind the existing TODO
publication state machine. GitHub behavior and its regression suite are retained.

## Assignment and revision

- Branch: `quick-gitlab-todo-issues-113916820`
- Base: `7dcf64136918e050454f2aabaf33aed8f481dc5d`
- Reviewed/tested source: `1c24438f7ce7960b44c0208a131d101f992044be`
- Tracking issue: https://github.com/Tasaddar12/ai-engineering-template/issues/74
- Draft PR: https://github.com/Tasaddar12/ai-engineering-template/pull/77
- Authorization: implement and publish; do not merge, contact on-prem servers,
  change credentials or run benchmarks. Adoption records remain unfilled.

## Changes

`providers.resolve` resolves origin offline into the accepted six-key dictionary:
provider, host, project, remote, web_url and repository. `delivery.provider`
defaults to auto; explicit github/gitlab selections must match origin.
`delivery.gitlab_hosts` maps origin hostnames to HTTPS web authorities, keeping
SSH transport ports independent. Nested namespaces, SSH aliases and supported
SSH/HTTPS shapes are checked; unknown hosts, credentials, traversing/encoded
paths, unsupported URL shapes and cross-project item URLs are rejected.

`gitlab_issues` pins authenticated API requests to the configured authority and
encoded full project path. It validates project capability/identity, local IIDs,
item URLs, response fields and pagination. Calls pin the documented API protocol
and disable inherited repository/host, CI-autologin and subfolder redirection.
CLI diagnostics stay private; UTF-8 preserves reviewed Unicode intent.

`todo_issues` routes GitLab operations at the existing provider boundary. The
shared logic retains selected preview, open/closed candidates and branch/explicit
MR context, portable canonical issue validation, reviewed create/reuse, verified
readback and stored linkage. Attempted intent is persisted before create. An
uncertain create recovers only one exact marker with matching public intent and
never creates again automatically. Completion reads closed status only on an
explicit completion request. No remote close/reopen, body updates or polling were
added.

## Checks and review

- `python -m unittest discover -s tests -p test_providers.py -v`: 6 passed.
- `python -m unittest discover -s tests -p test_gitlab_todo_issues.py -v`: 19 passed;
  real runtime, Git, locks and TODO files with an offline `glab` subprocess.
- `python -m unittest discover -s tests -p test_todo_issues.py -v`: final source
  rerun, 34 passed with one host symlink-capability skip; existing suite unchanged.
- `python -m unittest discover -s tests -p test_issue_format.py -v`: 13 passed.
- `git diff --check`: passed before source publication.
- Tracking issue passed canonical `issue.validate --variant Enhancement`.
- Independent phase-checker: approved at `aed84341b4eaf922a30b66c46ea2d081a3fe5bc7`;
  PC-GL-01 task checks and PC-GL-02 exact ownership corrected.
- Fresh independent code-reviewer: clean at source `1c24438`, zero critical,
  warning or info findings; Git blob hashes confirmed all reviewed files match.
- Required Linux/Windows CI remains pending at summary authoring; current/final
  status and exact run evidence are maintained in the draft PR body. Source run:
  https://github.com/Tasaddar12/ai-engineering-template/actions/runs/38426554666

## Commits and integration

- `fb3c19c`: scoped maintenance plan.
- `aed8434`: independent plan-review corrections.
- `941099c`: shared resolver, defaults, configuration reference and tests.
- `e819ff6`: reject empty origin query/fragment suffixes.
- `1c24438`: GitLab issue adapter, state-machine routing and 19 lifecycle tests.
- This SUMMARY is committed separately; its exact commit is in the final handoff.

Delivery owner accepted sole ownership of the shared resolver/config by this task
and owns `delivery.py`, MR adapter, ship paths and delivery tests separately in
https://github.com/Tasaddar12/ai-engineering-template/pull/76. Its actual resolver
dependency is this PR; latest providers-only tip is
`e819ff6f9d7a3e9dfe44a05030c261ed574ab3a5`. No delivery files were duplicated here.
The TODO runtime is independently executable without the MR-delivery changes.

## Deviations and remaining evidence

The offline tests caught a provider-string YAML serialization failure; persisted
repository identity is now a plain string. Harness assertions were corrected to
allow a linked TODO to remain pending and to inject save faults only on the
intended operation. Official CLI documentation confirmed `GLAB_API_PROTOCOL`.

Live GitLab execution is intentionally untested under the no-on-prem-contact
constraint. Required CI is pending at this record's creation. No implementation
stubs, credential changes, automatic remote issue mutations or unrelated source
edits remain. Worktree and draft are preserved for review; no merge was performed.

## Self-check

Owned source/tests/reference exist and are committed. The unchanged adoption
skeleton and unrelated worktrees were preserved. Independent review and focused
test evidence identify the source revision above; final PR evidence records CI
at the final candidate. Context usage: unavailable.
