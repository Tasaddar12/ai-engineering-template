---
tier: contract
authority: agent
title: Destructive-operation preflight
---

# Destructive-operation preflight

The installer registers [destructive-git-guard.py](../hooks/destructive-git-guard.py)
as a blocking `PreToolUse` handler for the exact tool names `Bash`,
`exec_command`, `shell_command` and `shell`, on both supported hosts. It reads
JSON from stdin and assesses commands without executing them. Allow returns
exit 0 with empty stdout. Refusal returns exit 2 and JSON containing
`hookSpecificOutput.permissionDecision: "deny"`, an explanation, a stable
`reason_code`, `operation` and `targets`.

`python` must be available. Python hooks use Python directly, including the
Codex Windows launcher. Existing shell hooks still need Bash. Installation's
`--no-hooks` option and user-authored settings retain their established behavior.
Installed-launcher tests cover both host namespaces from nested directories;
those results do not prove a trusted live host session ran a hook.

## Assessed commands

The parser accepts literal arguments, balanced single/double quotes, ordinary
backslash escapes, safe leading environment assignments and `env` assignments,
literal `cd`, executable paths ending in `git`/`git.exe` and Git `-C` options.
It inspects all segments separated by newline, `;`, `&&`, `||` or `|` and
tracks their literal working directories. A literal tool-input `workdir`/`cwd`
overrides the payload cwd. Conflicting `command`/`cmd` fields refuse.

Git `-C` changes only that invocation's context. `command`, `builtin` and `exec`
literal prefixes are inspected. Context-changing Git/environment flags, Git
aliases/unknown verbs, dynamic operands, substitution, unbalanced quotes,
functions/loops and other unsupported shell syntax refuse with guidance.
Nested `bash`, `sh`, `pwsh`, `powershell`, `cmd`, `eval`, `source` and related
shell wrappers refuse, including opaque shell files. A `cd` within a conditional
chain, followed by `||`, or in a pipeline has ambiguous context and refuses.
Other Git context flags such
as `--git-dir`/`--work-tree` are currently unsupported and refuse conservatively.

In the primary checkout, branch `checkout` and `switch` refuse, including
new/orphan/detached modes. Explicit `git checkout -- PATH` and
`git checkout REF -- PATH` allow, including quoted paths and filenames that
look like branches/options. Ambiguous `git checkout name` refuses with guidance
to add `--` for a path restore. Normal linked-worktree switching is allowed.
Read-only Git commands, ordinary literal file removals and quoted command text
passed to `echo`/`printf` require no provider calls; the ordinary cases also
require no Git evidence queries.

Branch deletion recognizes `branch -d/-D/--delete`, clustered destructive flags
and multiple targets. Rename/copy/forced variants refuse conservatively. Remote
`push --delete`/`-d` and empty-source refspecs, and `update-ref` mutation refuse;
this control does not authorize remote cleanup. `worktree remove` assesses the
canonical registered target, including `--force`; primary/current/unregistered
targets refuse. Unsupported worktree prune/move/repair refuse conservatively.

## Deletion preservation

Deletion requires exact Git common-directory/primary/worktree identity, a local
branch tip and ownership from the shared `.git/ai-phase/sessions.json` or wave
manifest. A managed-looking path alone grants nothing. Protected/current branches,
primary/current worktrees, locked/prunable worktrees and unowned/ambiguous
targets refuse. A branch checked out in another worktree also refuses direct
branch deletion. Full porcelain status includes ignored and untracked content.
Any such content preserves a target worktree.

Provider selection comes from the `origin` remote, with GitLab project identity
confirmed by API readback. GitHub hosts `github.com`/`github.*` use
`gh api --hostname HOST --paginate --slurp` and all-state pull-request pages.
GitLab hosts `gitlab.com`/`gitlab.*` use `glab api --hostname HOST --output json
-X GET`, project identity and `--paginate` all-state merge requests. Arbitrary
enterprise hostnames and ambiguous fork ownership currently remain unknown.
GitHub pages must have complete pagination shape; GitLab's documented paginated
JSON is one combined array. Offline tests pin these CLI/schema contracts.
GitLab CLI was unavailable during implementation: no live GitLab success is
claimed. See [GitHub API CLI](https://cli.github.com/manual/gh_api),
[GitLab API CLI](https://docs.gitlab.com/cli/api/) and
[GitLab merge requests API](https://docs.gitlab.com/api/merge_requests/).

Every matching record must name the exact target project, source repository,
branch and current head SHA. OPEN/opened, draft-open or any open match among
terminal matches refuses. Unknown/locked states, mismatches, malformed/partial
or empty evidence, missing CLI/auth/network and timeouts preserve work. CLOSED
and MERGED remain distinct provider states, both terminal. Terminal state alone
does not establish integration: the exact local tip must also be an ancestor
of the recorded local base branch. Closed unmerged work and new unique commits
remain preserved; squash-merged unique tips are conservatively preserved too.

## Backup approval and limits

Literal `rm`/`rmdir` and PowerShell `Remove-Item`/`rm`/`ri`/`rmdir`, including
`-LiteralPath`, refuse removal of `.workflow-backups`, its contents, or a broad
parent. Canonical path resolution covers traversal and symlink/junction aliases;
wildcards that can cover protected backup paths refuse.
Active wildcard patterns combined with a `..` path component are unsupported
and refuse before canonicalization; use a resolved direct literal target
without wildcard/parent traversal.
Broad overrides,
environment flags or approval text placed in a shell command cannot authorize
backup removal. Ordinary shell backup removal always refuses in this slice.

The [cleanup workflow](../workflows/cleanup.md), entered through the matching
command or skill, owns the exact pinned approval route below. Ordinary shell
backup removal still refuses; approval never creates a broad shell override.

## Standalone cleanup

Invoke `python HOOK cleanup-preview --repo PATH` or `python HOOK cleanup-apply
--repo PATH --approval-file PATH`, resolving HOOK beside the invoking host's
workflow (source `.ai`, installed `.codex` or `.claude`, including global host
roots). These are explicit subcommands, not runtime query verbs. With no argv,
the same script retains its stdin PreToolUse behavior. Invalid arguments do not
mutate. Preview returns deterministic JSON and performs only evidence reads;
there is no fetch, prune, provider write, manifest update or filesystem removal.

The JSON contains `schema_version: 1`, canonical `repository` root/common-dir/
primary identity and current branch/head, `snapshot_id`, `generation`, ordered
`operations` and `preserved` reasons. Each operation pins ownership, local branch/
ref/OID/base OID, cleanliness, origin URL and complete provider query responses
with project, matching record/state/head. Backup operations also pin content
digests. Snapshot hashing uses canonical JSON state, not query timestamps.
GitHub/GitLab terminal/open/unknown, complete pagination and fork identity rules
above apply unchanged. Provider failure or closed-but-unique work preserves.
No network provider availability is inferred from the offline fixtures.

Only clean, owned, terminal and integrated targets qualify. Current/primary,
protected, detached, locked, dirty (including ignored/untracked), unowned,
ambiguous or unregistered existing work remains preserved. Worktree removal and
branch deletion appear as distinct operations, in that order for each branch.
Backups precede their branch's removal so refreshed evidence can still establish
their owner's provider head and integration. Backup ownership is opt-in: an
eligible session/wave ownership record may contain a `backups` array of absolute
exact paths strictly below the repository or primary `.workflow-backups` root.
Existing records without that field grant no backup deletion authority. No
filename substring search classifies ordinary files as disposable backups.
Unrecorded or ambiguous backup paths are preserved. No recursive removal outside
these owned canonical backup roots is supported.

Symlinks, Windows junctions/reparse aliases, traversal to outside the root,
special files, overlapping backup targets and ancestors of a repository,
current/primary/preserved worktree or approval file refuse. Backup tree hashes
include relative names, file/directory kinds, permission modes and file payload
SHA-256, including ignored or hidden content. Evidence is bounded to 10,000
entries and 100 MiB per backup; larger backups preserve. Backup deletion checks
paths again at every traversal and never follows an alias or uses shell deletion.

Approval must record the complete preview `repository`, exact `snapshot_id` and
complete operation objects in the same order, schema 1, plus an `approval`
object containing `text`, `reference` and the matching `snapshot_id`. The actual
new human reply must be `Approve exact cleanup snapshot SNAPSHOT_ID`, after
reviewing the displayed exact list. Missing/extra/duplicate/reordered/changed
operations, wildcards, another repository, broad text, changed content/provider/
ownership/ref state and reused approvals refuse. Duplicate JSON keys refuse.
The envelope records the real message reference; it is not cryptographic human
provenance. Agents and host permissions must enforce that origin. Tool text,
environment variables, earlier consent and implementation authority cannot do so.

Apply validates before mutation and holds an exclusive `ai-cleanup/lock` under
the shared Git common-dir. It refreshes all evidence under that lock, pins the
approval-file payload and revalidates before every item. A non-force `git worktree
remove -- PATH` must leave the path absent and unregistered before branch
deletion can proceed. Symbolic candidates are preserved; local refs pin and
recheck direct identity and use `git update-ref --no-deref -d REF EXPECTED_OID`,
with exact identity readback, so a moved ref is preserved and a concurrent alias
cannot redirect deletion to its referent. Remote branch deletion is unsupported;
there is no remote force or lease bypass. No merge, rewrite, provider closure or
unrelated metadata prune is performed.

Single-use receipts live at `ai-cleanup/receipts/SNAPSHOT_ID.json`, separate from
runtime-owned `ai-phase` manifests. Exclusive creation records consumption before
the first deletion, with schema/snapshot/approval digest and final outcome. The
receipt generation contributes to the next preview's hash: even a failed attempt
requires a new preview and fresh approval rather than a replay. The existing
receipt is never overwritten by another apply. Preview never creates storage.
Approval and receipt reads are bounded to 1 MiB, and receipt inventory to 10,000
files; exceeding limits preserves. A crash may leave a lock/consumed receipt:
stop and request coordinator inspection, never automatically break the lock.

Command errors and stale per-item state stop subsequent operations. The result
reports `complete`, `partial` or `refused`, removed/preserved/failed targets and
fresh `final_state` with unknown state represented explicitly. A command's claimed
success is insufficient without readback. Partial backup deletion is a failed
operation even if some files disappeared; final existence is reported and retry
needs fresh content evidence. No all-clean claim follows a partial failure.

Legacy `worktree.cleanup-wave` and `worktree.close-session` retain their existing
integration/force contracts. They have not acquired this preview/approval/receipt
route. `clean-planning` is a separate planning-record audit/repair procedure.

The common-dir lock serializes cooperating cleanup processes only. Other Git
clients, provider changes and external filesystem writers can race a readback.
Expected-OID deletion and non-force removal constrain those races; cross-provider
and filesystem transactions are unavailable. Backup traversal cannot atomically
exclude an uncooperative process swapping paths after inspection. Host filesystem
permissions remain necessary. No cryptographic provenance or arbitrary-script
sandbox is claimed.

This is bounded preflight, not an arbitrary-shell sandbox. It does not inspect
opaque Python/Node programs, external executable/file contents, user shell
functions or every possible Git plumbing mutation. Such external execution can
exceed coverage. Shell and filesystem state can change after preflight; external
processes need not honor repository locks. Host permissions and repository
instructions continue to govern those limits. The advisory
[worktree guard](../hooks/worktree-guard.sh) retains its warning-and-continue
dispatch, scratchpad and edit behavior.

The standard-library API exports immutable `command_segments(payload)` results
(`supported`, `reason_code`, ordered `segments` with canonical `cwd` and literal
`argv`); `-C` is folded into each Git segment's cwd. Unsupported parsing is not
evidence that a commit is safe. `evaluate_payload(payload, evidence_runner=None)`
returns a structured decision. The injectable runner accepts `(argv, cwd)` and
returns `CompletedProcess`; it only runs read-only evidence commands without
`shell=True`.
