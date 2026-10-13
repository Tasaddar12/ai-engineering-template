# GitLab TODO issue publication maintenance

Base: 7dcf64136918e050454f2aabaf33aed8f481dc5d
Issue: https://github.com/Tasaddar12/ai-engineering-template/issues/74
Authorization: implement this bounded lifecycle in a new worktree, publish a linked draft PR; do not merge, contact on-prem servers, change credentials or run benchmarks.

## Tasks

1. Add offline provider/origin resolution with explicit GitLab host configuration, nested projects and repository-pinned item URLs. Preserve GitHub defaults. Coordinate the consumed interface with the MR delivery owner.
2. Add GitLab issue operations behind the existing TODO state machine: preview, candidates and MR context, create/reuse, verified readback, persistent linkage, uncertain-create recovery and explicit closed-status checks. Reuse portable issue validation.
3. Add fake-provider lifecycle regression coverage, run focused tests, obtain independent review and await required GitHub CI. Keep the draft current.

### Task 1 evidence

- read_first: `.ai/runtime/lib/config.py`, `.ai/runtime/lib/gitops.py`, `.ai/runtime/lib/todo_issues.py`, `tests/test_todo_issues.py`.
- action: implement the accepted `providers.resolve` dictionary and `item_number` ownership contract. Own defaults in `.ai/runtime/lib/config.py` and configuration guidance in `.ai/references/providers.md`; do not edit adoption config or delivery files.
- acceptance_criteria: known GitHub shapes remain valid; configured GitLab nested project and SSH/web ports resolve offline; unknown hosts, credentials and cross-project item URLs are rejected.
- verify: `python -m unittest discover -s tests -p test_providers.py -v`; fails_when: nonzero exit or zero tests discovered.

### Task 2 evidence

- read_first: `.ai/runtime/lib/todo_issues.py`, `.ai/runtime/lib/todos.py`, `.ai/runtime/lib/issue_format.py`, `.ai/templates/issue.md`, `tests/test_todo_issues.py`, `.ai/runtime/lib/providers.py`.
- action: route only GitLab issue operations through a pinned adapter; retain the publication state machine and portable issue validator.
- acceptance_criteria: selected preview, open/closed candidates and MR context, reviewed creation/reuse, verified readback/linkage, uncertain-create recovery without retry and explicit closed-status completion work offline.
- verify: `python -m unittest discover -s tests -p test_gitlab_todo_issues.py -v`; fails_when: nonzero exit or zero tests discovered.

### Task 3 evidence

- read_first: `tests/test_todo_issues.py`, `tests/test_gitlab_todo_issues.py`, `tests/test_providers.py`, `.github/workflows/validate.yml`, `.ai/agents/code-reviewer.md`.
- action: run focused lifecycle/portable validator tests, capture independent review, correct blockers and observe required CI at the published candidate. Keep honest draft evidence and write the owned SUMMARY.
- acceptance_criteria: GitHub regression and GitLab suites pass; review has no unresolved blockers; required validate CI succeeds. Unverified evidence remains a reported gap.
- verify: `python -m unittest discover -s tests -p test_todo_issues.py -v` and `python -m unittest discover -s tests -p test_issue_format.py -v`; fails_when: nonzero exit or zero tests discovered for either command. `gh pr checks 77 --repo Tasaddar12/ai-engineering-template`; fails_when: a required check fails or remains pending at completion.

## Ownership

- `.ai/runtime/lib/providers.py`, `.ai/runtime/lib/gitlab_issues.py`, `.ai/runtime/lib/todo_issues.py`
- `tests/test_providers.py`, `tests/test_gitlab_todo_issues.py`; preserve `tests/test_todo_issues.py` as GitHub regression suite.
- `.ai/runtime/lib/config.py`, `.ai/references/providers.md`, `docs/maintenance/gitlab-todo-PLAN.md`, `docs/maintenance/gitlab-todo-SUMMARY.md`; owned by this maintenance coordinator after delivery-owner contract agreement. No `.planning/config.yaml` edits.
- MR delivery and ship paths belong to the separate delivery owner.

## Acceptance and validation

GitHub tests remain green. Offline GitLab tests cover nested project origins, configured hosts, SSH/HTTPS and ports, unsafe URLs, open/closed candidates, MR branch/explicit context, creation/reuse, readback failures and intent recovery without duplicate creation, explicit completion and fail-closed responses. No automatic issue mutations beyond authorized creation.

## Threat boundaries

Reject unknown provider/host, credential-bearing origins, path traversal, malformed URL/response and cross-project linkage before writes. Keep CLI diagnostics private. Do not trust environment repository redirection. Persist attempted intent before create and never retry an uncertain create automatically.
