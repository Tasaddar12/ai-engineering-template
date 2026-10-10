# Worktree sessions and delivery

The two ends of the contract a workflow obeys when it writes source: open the
worktree the work lives in, and deliver that worktree's branch through a pull
request. Companion to [worktree-branch-check](worktree-branch-check.md),
[worktree-path-safety](worktree-path-safety.md) and
[worktree-recovery-policy](worktree-recovery-policy.md), which cover the
per-plan dispatch checkouts a session's executors run in.

**Work that touches source does not reach the base branch directly.** It happens
in its own worktree, on its own branch, and lands by being merged from a pull
request whose checks passed. There is no flag, no configuration and no recovery
path around that, and [worktree-guard.sh](../hooks/worktree-guard.sh) blocks the
attempt rather than warning about it.

## Scope

The session contract covers quick work and the shared phase lifecycle:

| Workflow | Session | Delivered by |
|---|---|---|
| `/quick` | `quick` | itself — one task, one branch, one pull request |
| `/discuss-phase`, `/plan-phase`, `/execute-phase`, `/verify-work` | `phase` | `/ship` |
| `/ship` | `phase` | itself |

The phase session is shared. `/discuss-phase`, `/plan-phase`, `/execute-phase` and `/verify-work`
run `phase.locate` before their init bundle, then use its validated session.
`/ship` selects and validates the same phase session before loading ship data.

**The planning workflows are deliberately outside this.** `/capture`,
`/check-todos`, `/phase` and its roadmap edits, `/new-milestone`,
`/complete-milestone`, `/milestone-summary` and `/onboard` write planning records
and nothing else, through runtime verbs (`todo.add`, `roadmap.*`, `commit`) and
never the editing tools. The guard intercepts the editing tools, so it does not
fire on them; and putting a one-line todo or a roadmap tweak through a pull
request, a merge and a session close costs more than the record is worth.

This exception covers only the named runtime-owned planning records. Reusable
`.ai` instructions, templates and tooling, or changes mixed with source, use the
source session and PR path. Template maintenance does not broaden the exception.
See the [canonical Git workflow](git-workflow.md).

Work a planning record *leads to* is a different matter. `/check-todos` hands
implementation to `/quick` or `/phase`, and those open sessions of their own.

## Phase session routing

Run these steps in `/discuss-phase`, `/plan-phase`, `/execute-phase`, `/verify-work` and `/ship`:

1. Resolve `PHASE_RUNTIME` to an absolute path and define `phase_run`.
2. Run `LOCATE=$(phase_run query phase.locate "${PHASE}")`. Stop on a nonzero exit and report the runtime error.
3. Parse `phase_found`, `worktree`, `session`, `padded_phase`, `branch` and `source`.
4. If `phase_found` is false, report the missing phase and exit.
5. If `session` is present, require a non-null absolute `worktree`, retain the session identity, run the explicit quoted `cd -- "${worktree}"`, then run the workflow's init bundle.
6. If `session` is absent in `/discuss-phase`, `/plan-phase`, `/execute-phase` or `/verify-work`, run the init bundle only after step 4. For a primary checkout, call `session.open phase "${padded_phase}"`. For a linked worktree, call `session.adopt phase "${padded_phase}"`. `/ship` stops when no validated session is returned.
7. After `session.open` or `session.adopt`, parse its returned paths, run the explicit quoted `cd` into its absolute worktree, reload the full init bundle and replace every previously derived value.
8. Stop on an unsupported session route or failed verb. Preserve selected worktree content and report the error.

For `/ship` without an explicit phase, run `session.status` and select a phase only
when exactly one open `kind=phase` entry exists. Use its `label` as `PHASE`, then
validate it with `phase.locate`. With zero or multiple entries, stop and require
`/ship <phase>`. Never pass an empty phase to `phase.locate` or ship the current
branch by inference.

## Opening non-phase sessions

Run this before the workflow's first write, after the runtime launcher.

```bash
SESSION=$(phase_run query session.open "${KIND}" "${LABEL}")
```

`KIND` is one of `phase`, `quick`, `milestone`, `onboard`. `LABEL` identifies the
unit of work within that kind — the padded phase number for a phase, the quick
id for a quick task, the milestone slug for milestone work.

| Field | Meaning |
|---|---|
| `worktree` | Absolute path to the checkout. **Run every subsequent command from here.** |
| `branch` | The branch this unit of work commits on |
| `base` | The revision it forked from |
| `reused` | `true` when a session for this unit was already open |
| `synced` | What `pr.sync` did to the base branch before forking |

For phase work, `phase.locate` returns the existing registered session when it
matches the phase. Call `session.open` only from the primary checkout after the
phase is confirmed. Call `session.adopt` only from the selected linked worktree
when no session is registered; it preserves that checkout's branch and records.

Report it in one line before doing anything else:

```
Session: {branch} ({reused ? "resumed" : "opened"}) at {worktree}
```

**If the verb fails, stop and report its message.** A failure means isolation
could not be established — a git too old for worktrees, a worktree root that is
not gitignored, a base that does not resolve. Do not continue in the checkout
you were invoked from; that is the one outcome this project has ruled out.

## Working

Run every workflow command from `SESSION.worktree`. Commit each completed
slice there with a descriptive message. After integration and applicable checks,
the coordinator pushes the session branch and updates the same tracking PR as
slices land. Follow the [canonical Git workflow](git-workflow.md) for the exact
commit boundary and truthful PR evidence.

A phase's per-plan dispatch worktrees are created **from the session branch**
and merged back **into it**, never into the base branch. They live beside the
session under the same worktree root rather than nested inside it, and
`worktree.merge-wave` targets whatever branch is current, which inside the
session is the session branch. No change is needed at the dispatch site.

## Delivering

The close sequence, in order. Each step is gated on the one before it, and a
failure stops the sequence rather than being worked around.

**First, check there is anything to deliver.** A workflow can complete without
writing — a summary shown but not written, a confirmation declined:

```bash
git -C "${SESSION_WORKTREE}" log --oneline "${SESSION_BASE}..${SESSION_BRANCH}"
```

Empty means nothing was written. Close the session and stop — an empty pull
request is noise:

```bash
phase_run query session.close "${SESSION_BRANCH}"
```

Otherwise push and open the pull request:

```bash
git -C "${SESSION_WORKTREE}" push -u origin "${SESSION_BRANCH}"
phase_run query pr.open "${SESSION_BRANCH}" --title "${TITLE}" --body-file "${BODY}" --draft
```

Create every first PR as a draft for tracking. `pr.open` is idempotent: a resumed
session updates the PR already open for that branch. The runtime preserves an
existing PR's draft state during edits. `pr.merge` marks a draft ready only as
part of an explicitly authorized merge; do not mark a PR ready automatically.

Then judge the checks. `pr.checks` returns one of four states, and only one of
them permits a merge:

| `state` | Meaning | What to do |
|---|---|---|
| `passing` | Every check reported success, or was skipped or neutral | Go to the merge gate |
| `pending` | At least one check has not finished | Wait and re-run. Never merge on an unfinished result |
| `failing` | A check failed, or was cancelled without reporting | **Fix it on this same branch, in this same worktree, and push again.** The pull request stays open and keeps its history. Do not open a second pull request, and do not close this one |
| `none` | The pull request has no checks at all | Supply the project's own evidence: run `verification.run-checks` and pass `--local-checks-passed` only if it passed. With neither, the merge is refused |

Merge only with the user's explicit authorization. If the current instruction
already authorizes this merge, do not ask again. Otherwise show the PR URL, check
verdict and merge method, then ask. `workflow.auto_advance` never authorizes a
merge. Use AskUserQuestion (header: `Merge`; options: `Merge now` — land it and
close the session / `Leave it open` — stop and leave the PR for review), or a
numbered list in text mode.

On `Leave it open`, report the URL and stop. The session stays open and the next
run of this workflow resumes it.

On `Merge now`:

```bash
phase_run query pr.merge "${SESSION_BRANCH}"
phase_run query pr.sync
phase_run query session.close "${SESSION_BRANCH}"
```

Add `--local-checks-passed` to `pr.merge` only in the `none` case above, and only
when the local run actually passed.

`pr.merge` squashes by default (`delivery.merge_method`) and deletes the remote
branch. `pr.sync` fast-forwards the base branch in the primary checkout so the
next session forks from work that already landed. `session.close` removes the
worktree and the local branch — but only against evidence the work actually
merged, and it reports what it preserved instead of discarding anything whose
fate is unclear.

**Never pass `--force` to `session.close` to tidy up a preserved worktree.** A
preserved session is unmerged work, and the reason it was kept is the reason not
to delete it. Report the preservation and its reason as they stand.

Report the outcome in one line:

```
Delivered: {url} — merged by {method}, evidence {evidence}; session {closed | preserved: {reason}}
```

## Anti-patterns

- Don't write anything from the checkout the command was invoked in
- Don't open a second session for a unit that already has one — use the
  `session` returned by `phase.locate`
- Don't open a new pull request because the first one's checks failed
- Don't merge on `pending`; an unfinished check is not a passing one
- Don't treat `none` as `passing`; silence is not evidence
- Don't merge the base branch into the session branch to "sync" it — the base
  moves under pull requests, not into them
- Don't close a session whose work is not proven merged
- Don't deliver a phase session from `/discuss-phase`, `/plan-phase`,
  `/execute-phase` or `/verify-work` — they accumulate onto it and `/ship`
  delivers it
- Don't open a session in a workflow that only writes planning records; it
  writes through runtime verbs, the guard does not fire on it, and the
  ceremony buys nothing
- Don't leave a session open at the end of a workflow that owns the whole unit;
  an undelivered session is work on a branch nobody merged
- Don't open a pull request for a session that wrote nothing
