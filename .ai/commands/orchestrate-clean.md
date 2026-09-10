---
description: Remove worktrees and branches left by an orchestration run, after checking nothing unmerged is lost
argument-hint: [run-id | --all | --dry-run]
---

Clean up: **${1:-the most recent run}**

**This deletes work.** A worktree holds a full checkout, and a track branch may
hold commits that exist nowhere else. Removing one that was not merged destroys
it. So the order here is fixed: **find out what would be lost, show the user,
then delete.**

Default to `--dry-run` behaviour when the argument is ambiguous. Deleting less
than the user wanted costs one more command; deleting more costs a track.

## 1. Find what exists

```bash
git worktree list
git branch --list 'orch/*'
ls .ai/state/orchestration/
```

## 2. Establish what is safe, per branch

Three checks. A branch is only safe when all three pass.

**Is it merged into the base?**

```bash
git branch --merged <base> --list 'orch/*'
git log --oneline <base>..<branch>        # empty means fully merged
```

**Does its worktree have uncommitted changes?**

```bash
git -C .worktrees/<name> status --porcelain
```

Anything here is in no commit at all. It is the most easily lost thing in the
repo and the most likely to matter — a track interrupted mid-implementation.

**Is its request still open?**

```bash
gh pr list  --head <branch> --state open
glab mr list --source-branch <branch> --state opened
```

An open PR on a branch you are about to delete leaves a request nobody can
merge.

## 3. Show the user before deleting

| Track | Worktree | Branch | Merged? | Uncommitted | PR | Safe? |
|---|---|---|---|---|---|---|

Split into two lists and be explicit about the difference:

**Safe to remove** — merged, clean, no open request.

**Would lose work** — anything failing a check. For each, say precisely what
disappears: *"`orch/ORCH-001/w2t1` has 7 commits not in `main`, and 3 modified
files not committed at all."*

**Never delete anything from the second list without an explicit yes**, even
under `--all`. `--all` means every run, not every safety check waived.

For a track that stopped for a human, recommend keeping the worktree. That is
where the work resumes, and the manifest points at it.

## 4. Remove

```bash
git worktree remove .worktrees/<name>        # add --force only if the user said so
git branch -d orch/<run>/<track>             # -d refuses unmerged; that is the point
git worktree prune                           # clears stale administrative files
```

Use `git branch -d`, never `-D`, unless the user explicitly confirmed losing
that branch. The refusal is a safety check, not an obstacle to route around.

If `git worktree remove` reports the worktree is dirty, **do not reach for
`--force`.** Go back to step 3 and show the user what is in it.

## 5. Close the run

Only when a run's tracks are all merged or explicitly abandoned:

- Mark the manifest closed, with what merged and what did not. **Keep the
  file** — it is the record of why plans were sequenced the way they were, and
  it is the first thing anyone reads when a later run hits the same
  dependencies.
- Update `.ai/state/STATE.md`.
- Append a journal entry: what was cleaned, and anything abandoned with commits
  on it.

## Report

- Worktrees and branches removed
- What was kept, and why
- **Anything abandoned that had unmerged commits** — say it plainly, with the
  branch name, so it can be recovered from the reflog if that was a mistake
- Runs still open
