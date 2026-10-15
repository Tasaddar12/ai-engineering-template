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

The dependent cleanup implementation owns an exact pinned approval route, with
schema version, canonical repository/common-dir, snapshot ID, deterministically
ordered exact operations and actual human approval text/reference. That route,
locks, revalidation and single-use receipts are not implemented by this guard
slice. There is no approved cleanup command in this revision. Legacy runtime
cleanup verbs are unchanged and must not be represented as that approval route.

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
