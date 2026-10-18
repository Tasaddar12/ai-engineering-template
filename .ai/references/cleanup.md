<!-- generated-by: doc-writer -->

# Cleanup contract

Use [/cleanup](../commands/cleanup.md) through its
[workflow](../workflows/cleanup.md). The standalone
[CLI](../hooks/cleanup.py) loads the adjacent
[cleanup library](../runtime/lib/cleanup.py). Installation copies the CLI,
library, command, skill, workflow and this reference into the selected host.
Run the CLI explicitly; it has no stdin hook mode or host hook registration.

## Evidence and eligibility

Preview reads Git and GitHub/GitLab provider evidence without optional Git locks,
fetching, pruning or provider writes. Keep the complete JSON response. Operations
require all of the following evidence:

- Exact repository root, Git common-dir, primary checkout, current branch and HEAD.
- A unique ownership identity from Git-common-dir `ai-phase/sessions.json`
  (`sessions`) or `ai-phase/waves/*.json` (`entries`), including the candidate
  branch, worktree path and base branch. Ownership is read, never created here.
- A clean candidate worktree, including no ignored or untracked files, with no
  lock, prunable registration, bare state or ambiguous branch registration.
- Complete matching terminal provider records for the exact origin project,
  source project, branch and current OID. GitHub uses `gh api --paginate --slurp`;
  GitLab uses `glab api` with project identity and paginated merge-request reads.
  Missing, open, mixed, malformed, partial, forked or unavailable evidence
  preserves the candidate.
- Git ancestry proving that the exact candidate OID is integrated into its
  recorded local base branch. A closed provider record alone is insufficient;
  a merged record does not authorize deleting later unique commits. Squashed
  work whose exact tip is not an ancestor stays preserved.

Preserve the current and primary checkout, detached worktrees and branches named
`main`, `master`, `develop`, `trunk` or `release/*`. Preserve unowned, ambiguous,
dirty, locked and unknown candidates. Symbolic branch refs are ineligible,
including aliases with missing targets. Reject symlinks, junctions and path
aliases before canonicalization.

## Snapshot and operations

Preview returns `schema_version: 1`, `repository`, receipt `generation`, ordered
`operations`, `preserved` reasons and a content-derived `snapshot_id`. Each
operation pins branch/ref identity and OID, base OID, ownership, cleanliness and
provider reads. Backups also pin a recursive content/mode digest.

An owner's `backups` list authorizes only explicit absolute targets beneath
the invoking or primary checkout's `.workflow-backups/`. Preserve unrecorded
siblings and containers. Reject wildcard paths, overlapping targets, duplicate
ownership, protected ancestors, escaping aliases and special files. Evidence
limits preserve backups that exceed 100 MiB or 10,000 entries.

Operations place backups before their branch's removal evidence disappears and
worktree removal before branch deletion. Worktree removal uses literal
`git worktree remove -- PATH` without force. Branch deletion uses literal
`git update-ref -d --no-deref REF EXPECTED_OID`; it cannot dereference a replaced
symbolic ref and delete its referent. Backup removal walks validated exact paths
without a shell or forced recursive deletion.

## Approval, application and reporting

Follow the workflow's exact approval envelope and require the actual human reply
`Approve exact cleanup snapshot SNAPSHOT_ID`. Copy the entire repository object
and ordered operation objects unchanged. Store the envelope outside removal
targets; use the real human message reference. The envelope cannot itself prove
who supplied that reference.

Apply validates the snapshot, operation list and envelope, acquires an exclusive
lock under Git-common-dir `ai-cleanup/`, refreshes evidence and rereads approval.
It consumes a one-use receipt before mutation and revalidates the remaining
ordered operations, preserved rows, repository identity and approval before each
item. It checks exact ref identity and backup digest immediately before removal.
The lock coordinates cleanup processes that use this CLI; it does not lock out
other Git or filesystem writers or freeze provider state. Revalidation narrows
these races but cannot make cleanup atomic with external changes. Report the
observed outcomes and readback without claiming a global lock or atomic result.

Report `complete`, `partial` or `refused` truthfully, with removed/failed/preserved
rows and fresh `final_state` and `final_preserved` readback. Treat unknown readback
as unknown. Consumed receipts survive failed attempts and change the next
preview's generation. Retry with a new preview and exact human approval.
Preserve stale locks for inspection; do not bypass or automatically clear them.
Planning records, ownership manifests and remote refs remain unchanged.

Good: invoke the resolved CLI with `cleanup-preview --repo REPOSITORY`, review
its complete snapshot, then follow the workflow before invoking `cleanup-apply`.
If preview returns no operations, report preserved targets and stop.
