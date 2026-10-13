# GitLab TODO issue publication maintenance

Base: 7dcf64136918e050454f2aabaf33aed8f481dc5d
Issue: https://github.com/Tasaddar12/ai-engineering-template/issues/74
Authorization: implement this bounded lifecycle in a new worktree, publish a linked draft PR; do not merge, contact on-prem servers, change credentials or run benchmarks.

## Tasks

1. Add offline provider/origin resolution with explicit GitLab host configuration, nested projects and repository-pinned item URLs. Preserve GitHub defaults. Coordinate the consumed interface with the MR delivery owner.
2. Add GitLab issue operations behind the existing TODO state machine: preview, candidates and MR context, create/reuse, verified readback, persistent linkage, uncertain-create recovery and explicit closed-status checks. Reuse portable issue validation.
3. Add fake-provider lifecycle regression coverage, run focused tests, obtain independent review and await required GitHub CI. Keep the draft current.

## Ownership

- `.ai/runtime/lib/providers.py`, `.ai/runtime/lib/gitlab_issues.py`, `.ai/runtime/lib/todo_issues.py`
- `tests/test_providers.py`, `tests/test_gitlab_todo_issues.py`; preserve `tests/test_todo_issues.py` as GitHub regression suite.
- Provider config documentation/defaults after coordination; maintenance plan/summary.
- MR delivery and ship paths belong to the separate delivery owner.

## Acceptance and validation

GitHub tests remain green. Offline GitLab tests cover nested project origins, configured hosts, SSH/HTTPS and ports, unsafe URLs, open/closed candidates, MR branch/explicit context, creation/reuse, readback failures and intent recovery without duplicate creation, explicit completion and fail-closed responses. No automatic issue mutations beyond authorized creation.

## Threat boundaries

Reject unknown provider/host, credential-bearing origins, path traversal, malformed URL/response and cross-project linkage before writes. Keep CLI diagnostics private. Do not trust environment repository redirection. Persist attempted intent before create and never retry an uncertain create automatically.
