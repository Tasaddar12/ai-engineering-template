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
- python -m unittest discover -s tests -p test_gitlab_delivery.py -q: final exact-resolver integration 94dfe272994cf1507bc1291159c259d011ae4a61 passed all 48 cases, no skips, in 13.184s. The independent delivery tree runs 24 unit/boundary cases and explicitly skips 24 dependency cases.
- python -m unittest discover -s tests -p test_providers.py -q: six passed against latest exact resolver e819ff6 in final integration 94dfe27.
- python -m unittest discover -s tests -p test_agent_sources.py -q: 16 passed against 94dfe27.
- python -m unittest discover -s tests -p test_efficiency_contracts.py -q: eight passed against 94dfe27.
- python -m unittest discover -s tests -p test_unattended_flow.py -q: ten passed against 94dfe27.
- python -m unittest discover -s tests -p test_verification_bookkeeping.py -q: three passed against 94dfe27.
- git diff --check: passed.

## Commits

- 8b0b856460ffef1fe3e5278ee27c1c05d00518d2: provider-aware ship instructions.
- d360b7a5c509793b9adfaffd197ff28ce53232d4: MR adapter, provider dispatch, offline tests and summary.
- 5c4345d65e92bd692ef8f0a5b7b2ec4a4217a3ec: independent-review corrections and regression coverage.
- Final evidence summary: subsequent documentation-only commit recorded in Git history; three implementation/documentation slices precede it.

## Independent review

Fresh code-reviewer reviewed frozen integration b995255 and identified seven BLOCKER findings: CLI route overrides, stale merge evidence, merged-results SHA, unrelated retry discarding intent, explicit-provider mismatch, GitLab failure diagnostics and canonical ship title.
Correction review at frozen integration 94dfe272994cf1507bc1291159c259d011ae4a61 independently confirmed all seven resolved, with zero blockers/warnings. Independent offline reproductions also confirmed a pipeline changing after draft clearance blocks merge and a refused provider merge cannot return success. Source remained clean and unchanged during both review batches.

## Remaining

- GitLab delivery requires separately reviewed PR #77/resolver tip e819ff6; this PR deliberately contains no duplicate shared resolver/config files and is not independently GitLab-ready. Both reviewable worktrees remain preserved.
- Required GitHub CI on the final summary commit was pending when this summary was committed; the current result is maintained on PR #76. Required `validate` aggregates both unchanged Linux/Windows suites; no Actions/protection configuration was edited.
- Real provider execution and on-prem tests were intentionally excluded by the assignment; all GitLab tests are offline fakes and no credentials were changed. No PR was merged.
- Adoption PROJECT/STATE/ROADMAP skeleton remains unfilled; no phase requirement IDs assigned.

## Self-Check

PASSED: owned implementation, tests and documentation exist; all three slice commits exist; no tracked deletions or unrelated changes. Final reviewed source is delivery candidate 5c4345d with exact dependency e819ff6; final summary commit changes only this report. Dependency and CI evidence boundaries are explicit. Context usage: unavailable.
