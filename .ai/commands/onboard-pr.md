---
description: Review the onboarding change, commit it, and open a merge request
argument-hint: [target-branch]
---

Land this adoption. Target branch: **$ARGUMENTS** (default: the repository's
default branch — check `git remote show origin` or `git symbolic-ref
refs/remotes/origin/HEAD` rather than assuming `main`).

## 1. Check the work before offering it

Report on each of these, and **stop if any looks wrong** — do not commit past a
problem here:

- **`.ai/intent/PROJECT.md`** — filled in, no `CHANGEME`, and the non-goals and
  hard constraints are specific enough to reject a plan. Everything downstream
  is graded against this file.
- **`.ai/specs/`** — nothing asserted that has not been checked against the
  code. A spec claiming untrue things is worse than no spec; say so plainly if
  any were retro-written from a document rather than verified.
- **`CLAUDE.md`** — the snippet is appended, and no surviving language
  contradicts `.ai/RULES.md`. Grep for "never modify", "source of truth", "do
  not change" and quote whatever you find.
- **`.claude/agents/`** — any pre-existing agent that writes files has `Write`
  and `Edit` in its `tools:` list.
- **`.ai/plans/intake/`** — a readable set of clustered items, not one file per
  `TODO`.
- **`.ai/config.yaml`** — `verification.commands` holds the project's real test
  and lint commands, not an empty list.
- **Deletions** — every retired document was one the user explicitly approved.

## 2. Commit

Group the change so a reviewer can follow it. If the template copy was already
committed separately, this is one commit of onboarding decisions; if not, split
it:

1. the `.ai/` and `.claude/` copy, unmodified
2. everything `/onboard` decided — intent, specs, promotions, deletions,
   `CLAUDE.md`, intake

Do not include unrelated work. If the worktree has changes that are not part of
the adoption, stop and tell the user rather than sweeping them in.

## 3. Push and open the merge request

Neither `gh` nor `glab` is assumed to be installed. On GitLab, push options
create the MR with no CLI:

```
git push -u origin HEAD \
  -o merge_request.create \
  -o merge_request.target=<target-branch> \
  -o merge_request.title="Adopt .ai/ orchestration structure" \
  -o merge_request.description="<description>" \
  -o merge_request.remove_source_branch
```

Check the remote host first. If it is GitHub and `gh` is available, use
`gh pr create` instead. If neither route is available, push the branch and give
the user the compare URL to open it themselves.

**Confirm with the user before pushing.** Pushing is outward-facing, and the
description below is a claim about work they have not read yet.

## 4. Write the description

Cover, briefly:

- What the structure is, and a one-line pointer to `.ai/README.md`
- **Decisions the reviewer should check** — documents promoted to specs,
  documents retired, and the intent file's non-goals. These are judgment calls,
  not mechanical changes, and they are the reason this is a merge request
  rather than a commit to main.
- Contradictions found and fixed in `CLAUDE.md` or existing agents
- How many intake items were captured, and that intake is a record of known
  problems rather than a commitment to fix them
- What was deliberately *not* done — areas left unspec'd, the mode chosen and
  why
- Anything still open: unanswered questions, `.ai/plans/blocked/` entries

Then report the MR or PR URL, or the compare URL if you could not open it.
