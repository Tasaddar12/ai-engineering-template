# Publish a phase PR

Read [RULES](../RULES.md), current verification, required UAT and the user's
publication boundary. Use the assigned clean integration worktree.

Complete required behavior, documentation and local checks before publication.
Record real publication authorization; `--authorized` asserts existing authority
and does not obtain it. Choose the actual target branch for the project.

```text
python .ai/runtime/phase.py publish 01-authentication --authorized --base BASE
```

Replace BASE with the agreed branch. `--draft` requests a draft PR. The runtime
pushes and creates or updates the phase PR, checks current evidence and reports
required remote checks. It never invokes a merge command.

PR creation precedes its CI results. Inspect current checks with phase status
--remote; pending or failed required checks prevent declaring the PR ready.
Publication itself does not promise to wait for CI completion.

Review the complete PR, fix actionable findings in the worktree, repeat affected
checks and independent verification, then push the updated result. Report the
PR link, actual review/check state, remaining limitations and readiness.
If the user requested no merge, stop with the PR open and worktree preserved.

Publication is distinct from delivery. Merge and cleanup are separate actions
requiring applicable authorization and observed merge evidence; they are not an
automatic consequence of this procedure. A failed publication must not become
a local merge.
