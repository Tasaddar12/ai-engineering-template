# Publish and deliver changes

Read [RULES](../RULES.md#session-and-authorization), current verification, required
UAT and any user delivery override. Use the assigned integration worktree. The
default for authorized tracked work is commit, push, PR/MR and automatic merge.
The coordinator owns publication and merge; component workers return commits.

## Commit and publish each slice

1. Inspect the owned diff and run applicable checks for a bounded, reviewable slice.
   Commit it immediately with a descriptive nonempty message before the next slice.
2. Verify the actual remote, target branch and task branch. Push each completed
   standalone or integrated slice immediately after its commit, before beginning
   the next slice. Do not batch pushes or hold committed progress until completion.
3. On the first push, immediately open a draft PR/MR for tracking. Find an existing
   PR/MR for that source and target first; update it if present. Keep the same
   request current after every subsequent slice. Keep it draft while required
   scope, documentation or verification remains. Describe unfinished work accurately. Default progress pushes use the forge's supported
   CLI/API; an explicit local-only or no-push instruction prevents publication.

## Verify final readiness

Complete required behavior, documentation, local checks, independent review and
required UAT. Fix actionable findings in the worktree, commit each correction,
repeat affected checks and verification, and push the resulting revision.

For a runtime-managed GitHub phase, use the publisher from the clean integration
worktree after current phase verification:

```text
python .ai/runtime/phase.py publish 01-authentication --authorized --base BASE
```

Replace BASE with the verified target branch. `--authorized` asserts the standing
delivery authorization or an applicable explicit instruction; it does not obtain
permission. The runtime pushes and creates/updates a GitHub PR, checks current
evidence and reports configured remote checks. `--draft` still requires that
evidence; use the direct forge route above for earlier progress snapshots.

Standalone work uses the same review, checks and delivery rules through the
forge's tools without inventing phase records. For GitLab, use supported MR
tools; the Python publisher does not implement GitLab publication.

Review the complete request and confirm the remote head matches the locally
verified revision. Mark a finished draft ready unless the user requested draft-only
delivery. Observe required remote checks and reviews for that head; pending,
failed, cancelled or missing required results prevent merge. Wait for pending
checks, correct actionable failures within scope and reverify changed content.

## Merge automatically and confirm

Unless the user requested no merge or another narrower boundary, merge the PR/MR
through the forge once verification and repository requirements pass. Use the
repository's permitted merge method, preserving slice commits where supported.
Bind the merge to the verified head when supported; recheck and reverify if it
changes. Do not bypass protections, use an admin override, approve on a human's
behalf, force push or replace a failed publication with a local merge.

The Python publisher does not invoke merge commands. The coordinator performs
this step with the forge CLI/API without asking for another approval. If using
forge auto-merge or a merge queue, observe it through completion: scheduling a
merge does not establish delivery.

Confirm the remote merged state, target branch and merge revision. Report the
PR/MR link, commits, actual checks and observed merge result. If remote access,
required human review, checks or merge availability blocks delivery, preserve the
branch/worktree and report the exact blocker and next action. Explicit no-merge
instructions leave the request open. Synchronization may only fast-forward a
verified clean primary checkout; destructive cleanup needs separate authorization
and the [worktree](worktree.md) safeguards.
