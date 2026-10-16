---
status: passed
revision: 3c30e2eba98c1da3d46561c90d20ca234f9f3bb6
diff_base: 77b5668f2003bea60127d87e8785469286abafb3
acceptance: [MODEL-01, MODEL-02, MODEL-03]
---

# Model defaults verification

Fresh independent verification passed all four observable truths and all three
quick acceptance labels at the revision above. The full specialist returns are
retained in the session transcript; this record joins their results and checks.

| Host | Scout | Targeted fixer | Coder | Phase preparer |
|---|---|---|---|---|
| Claude runtime | haiku / inherit | haiku / inherit | sonnet / high | opus / medium |
| Codex runtime | gpt-6-luna / high | gpt-6-luna / high | gpt-6.1-sol / medium | gpt-6.1-sol / high |

The verifier ran all eight actual `resolve-agent <role> --host <host>` queries.
Claude native exports carry the same models, with effort omitted except for
phase-preparer's `medium`. Shared Markdown remains model/effort free. Only the
Codex coder TOML changes; other roles retain their models and effort.

MODEL-01/02 are verified by independently expected exported metadata, fresh
installation, installed-runtime subprocesses and the complete native role matrix.
MODEL-03 is verified by stale/duplicate-field removal, original body/permission
assertions, ordinary YAML override/inherit behavior, fixed leaf override resistance,
custom body/config/backup preservation and repeat-operation safety. Existing
migration refusal after removing `.ai` still leaves the snapshot unchanged.

## Checks

Python: `D:/Codex/2026-10-16/task-7/python-runtime/python.exe` (3.11.9).
Installer environment: short workspace-local TEMP/TMP and Python/Git Bash on PATH;
normal approved elevation avoids Windows sandbox MSYS restrictions.

| Exact command | Observed result |
|---|---|
| python -m unittest discover -s tests -p 'test_install*.py' -v | 121 tests, 710.264 seconds, OK, six skips, exit 0 |
| python -m unittest discover -s tests -p test_agent_sources.py | 16 tests passed (joined worker result) |
| python -m unittest discover -s tests -p test_phase_runtime.py -k Dispatch | 15 tests passed (joined worker result) |
| git diff --check | Passed |
| python .ai/runtime/phase.py query verification.run-checks | configured=false; adoption template verification.commands remains empty |

The six installer skips are three symlink-creation restrictions, one unavailable
short-path-alias case and two Codex-only settings cases skipped for Claude. None
skips the new model, effort, resolver, update or migration acceptance coverage.
Earlier sandbox failures and interrupted runs are preserved in the coder SUMMARY;
they are not passing evidence. The completed stable run supersedes them.

## Independent review

Fresh code-reviewer: clean, 14 files, zero critical/warning/info findings.
Fresh doc-verifier: 52/52 claims passed, zero failed or unverifiable.

| Document | Claims passed |
|---|---:|
| AGENTS.md | 3 |
| .ai/RULES.md | 3 |
| .ai/agents/README.md | 16 |
| .ai/install-assets/README.md | 8 |
| .ai/install-assets/agent-entry.txt | 3 |
| .ai/runtime/TEMPLATE-CONTRACT.md | 9 |
| .planning/config.yaml comments | 10 |

## Publication and limits

Draft PR: https://github.com/Tasaddar12/ai-engineering-template/pull/99.
Linux CI passed the full Python suite and four hook suites at this source revision.
Windows CI and the final publication-head check were pending when verification
finished; the PR body records their current results. The final bookkeeping commit
changes only this report and QUICK.md; executable inputs remain unchanged.

Current official Claude documentation supports model aliases and per-agent effort:
https://code.claude.com/docs/en/sub-agents#choose-an-effort-level.
Per-invocation effort requires Claude Code v2.1.292+; host environment overrides and
model availability still apply. No global effort setting or permissions change.
Existing project configuration is preserved during update/migration. No live paid
Claude invocation, benchmark, merge or changes to existing workflow PRs occurred.
PR #97 edits adjacent installer rendering context but does not duplicate this
model assignment change; reconcile that context if both changes later land.

No acceptance gaps or security threats identified in the inspected scope. The
adoption identity, STATE, ROADMAP and REQUIREMENTS skeletons remain unchanged.
