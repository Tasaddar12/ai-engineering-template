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

GitLab support depends on PR #77's providers-only commit 941099c282a27162177c4b251037a66b032d0a0a. No resolver/config/TODO files are copied into this branch.
`providers.resolve(workspace,cwd=None)` returns provider, host, project, remote, web_url and repository; `providers.item_number(target,url,kind='merge_requests')` verifies URL ownership.
Configuration uses delivery.provider auto/github/gitlab and delivery.gitlab_hosts origin hostname to canonical HTTPS authority mapping. SSH transport and web ports remain separate.

## Outcomes

- Ship uses the existing gh.status compatibility verb to preflight the selected CLI/host.
- GitLab API paths encode the full nested namespace; all calls explicitly select the resolved host.
- MR metadata updates preserve draft/ready state and omitted target. Body-file contents take precedence and readback verifies exact requested fields.
- Persistent publication intent and exclusive lock live under shared Git runtime metadata. Lost/failed responses require readback; unresolved creates block duplicate POSTs on retry. Unresolved edits cannot return stale success.
- Pipeline status and source SHA map to existing four-state check gates. Failed, canceled, manual, skipped, stale and unknown outcomes cannot become passing evidence.
- Runtime pr.open writes the normalized MR URL/number into the existing session pr metadata.
- GitLab merge uses source-SHA guarding and confirmed merged readback. GitLab rebase strategy is project-managed; runtime rejects delivery.merge_method rebase for this provider.

## Checks

- python -m unittest discover -s tests -p test_workflow_links.py -q: 3 passed.
- python -m unittest discover -s tests -p test_session_delivery.py -q: 59 passed in 132.458s.
- python -m unittest discover -s tests -p test_gitlab_delivery.py -q: 19 adapter tests passed; 19 exact-resolver integration cases require the separate dependency.
- git diff --check: passed.

## Commits

- 8b0b856460ffef1fe3e5278ee27c1c05d00518d2: provider-aware ship instructions.
- Runtime slice: recorded in Git history after this summary is committed.

## Remaining

- Run all MR cases in an integration worktree containing exact resolver commit 941099c.
- Obtain fresh independent review of that frozen integration tree and fix findings.
- Await required GitHub CI on the final delivery revision. Draft status does not establish readiness.
- Adoption PROJECT/STATE/ROADMAP skeleton remains unfilled; no phase requirement IDs assigned.

## Self-Check

Owned implementation and tests exist; documentation slice commit exists. Dependency and pending evidence are explicit. Context usage: unavailable.
