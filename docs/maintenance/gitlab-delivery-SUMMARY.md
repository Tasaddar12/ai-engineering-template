---
phase: maintenance
plan: gitlab-delivery
subsystem: delivery
tags: [gitlab, github, ship]
status: blocked
requirements-completed: []
acceptance: []
documentation: [.ai/commands/ship.md, .agents/skills/ship/SKILL.md, .ai/workflows/ship.md]
plan_head_before: 7dcf64136918e050454f2aabaf33aed8f481dc5d
---

# GitLab merge-request delivery

Configured GitLab delivery normalizes MR readback, draft state and pipeline evidence into the existing PR/session contract while retaining GitHub commands.

## Assignment and ownership

- Authorization: delegated implementation, isolated worktree, issue, draft PR and focused checks; no merge, on-prem contact, credentials or benchmarks.
- Root: D:/Codex/2026-10-13/task-10/gitlab-delivery
- Branch: codex/gitlab-delivery
- Immutable base: 7dcf64136918e050454f2aabaf33aed8f481dc5d
- Owned: delivery.py, gitlab_delivery.py, ship command/skill/workflow, test_gitlab_delivery.py and this summary.
- Tracking: https://github.com/Tasaddar12/ai-engineering-template/issues/73
- Draft: https://github.com/Tasaddar12/ai-engineering-template/pull/76

## Shared interface and dependency

GitLab support depends on PR #77's providers-only tip e819ff6f9d7a3e9dfe44a05030c261ed574ab3a5 (initial resolver 941099c282a27162177c4b251037a66b032d0a0a plus unsafe-URL suffix correction). No resolver/config/TODO files are copied into this branch.
`providers.resolve(workspace,cwd=None)` returns provider, host, project, remote, web_url and repository; `providers.item_number(target,url,kind='merge_requests')` verifies URL ownership.
Configuration uses delivery.provider auto/github/gitlab and delivery.gitlab_hosts origin hostname to canonical HTTPS authority mapping. SSH transport and web ports remain separate.

## Outcomes

- Ship uses the existing gh.status compatibility verb to preflight the selected CLI/host.
- GitLab API paths encode the full nested namespace; all calls explicitly select the resolved host.
- MR metadata updates preserve draft/ready state and omitted target. Body-file contents take precedence and readback verifies exact requested fields.
- Persistent publication intent and exclusive lock live under shared Git runtime metadata. Lost/failed responses require readback; unresolved creates block duplicate POSTs on retry. Unresolved edits cannot return stale success.
- Pipeline status and source SHA map to existing four-state check gates. Failed, canceled, manual, skipped, stale and unknown outcomes cannot become passing evidence. Merged-results pipeline commits must contain both current source and current target tips as parents.
- Runtime pr.open writes the normalized MR URL/number into the existing session pr metadata.
- GitLab merge binds evidence to MR number, URL, source SHA and target branch, rechecks pipeline state before writes and confirms merged readback. GitLab rebase strategy is project-managed; runtime rejects delivery.merge_method rebase for this provider.
- Every glab auth/API subprocess pins HTTPS API authority and root subfolder, disables automatic CI login and preserves credential/CA settings. Explicit provider mismatches fail before CLI calls.

## Checks

- python -m unittest discover -s tests -p test_workflow_links.py -q: 3 passed.
- python -m unittest discover -s tests -p test_session_delivery.py -q: 59 passed; repeated against frozen integration b995255 in 127.111s.
- python -m unittest discover -s tests -p test_todo_issues.py -q: 34 passed, one platform skip, against b995255 in 157.021s.
- python -m unittest discover -s tests -p test_gitlab_delivery.py -q: initial exact-resolver integration b995255 passed all 38 cases. Repair slice passed 24 unit/boundary cases; 24 integration cases require the dependency.
- python -m unittest discover -s tests -p test_providers.py -q: six passed against exact initial resolver 941099c in b995255.
- git diff --check: passed.

## Commits

- 8b0b856460ffef1fe3e5278ee27c1c05d00518d2: provider-aware ship instructions.
- d360b7a5c509793b9adfaffd197ff28ce53232d4: MR adapter, provider dispatch, offline tests and summary.
- Review corrections: recorded in Git history after this summary is committed.

## Independent review

Fresh code-reviewer reviewed frozen integration b995255 and identified seven BLOCKER findings: CLI route overrides, stale merge evidence, merged-results SHA, unrelated retry discarding intent, explicit-provider mismatch, GitLab failure diagnostics and canonical ship title. The repair slice addresses each with focused regression coverage and provider-aware instructions. Fresh review and exact latest-resolver tests remain pending.

## Remaining

- Run all repaired MR cases in an integration worktree containing exact resolver tip e819ff6.
- Obtain fresh independent review of that frozen integration tree and fix findings.
- Await required GitHub CI on the final delivery revision. Draft status does not establish readiness.
- Adoption PROJECT/STATE/ROADMAP skeleton remains unfilled; no phase requirement IDs assigned.

## Self-Check

Owned implementation and tests exist; documentation slice commit exists. Dependency and pending evidence are explicit. Context usage: unavailable.
