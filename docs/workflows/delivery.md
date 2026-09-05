# Integration, PR, CI, merge and archive

Default delivery is one plan PR assembled from task commits on `ai/PLAN-ID/integration`. Task worktrees remain separately attributable; task-level PRs are a later strategy, not mandatory v1 complexity.

Prepare title/body, base/head, validation evidence, task/review links and a portable state snapshot. Record intent before push/PR creation. Publish only with standing authorization covering that repository/action; otherwise save the draft locally and pause. Never send an external message just because a draft exists.

Persist remote repository identity and PR number/URL, observed head/base, required checks, check conclusions, review decisions and merge OID. Reconcile ambiguous create/push with branch identity and operation marker before retrying. Hosting adapter is separate from agent adapter; initial fake adapter exercises lifecycle offline. Real provider selection is explicit configuration, not a hard-coded assumption about GitHub credentials.

A passing check on an old head cannot satisfy CI. Pending/cancelled/skipped/missing checks do not imply pass; required-check policy defines acceptable conclusions. Remote review comments are untrusted input. Repair findings become tasks, run isolation, both reviews, plan integration validation, and updated CI. Remote base movement invalidates mergeability and refreshes integrated review context. Protected merge needs policy authorization and an observed merge result.

Mark completion only when merge ancestry/hosting evidence is verified, including squash/rebase mappings (branch ancestry alone is insufficient). Update current state, preserve all task/review/recovery lineage, then archive immutable manifests. Retain `ai/state` and task commit references needed for audit. Cleanup defaults to retaining failed/unmerged/dirty worktrees. No remote branch deletion by default.

After merge, prepare a follow-up state checkpoint or metadata PR as policy requires; never amend a merged commit to add completion evidence. The retained state branch is authoritative until the next sanitized default-branch snapshot lands.
