---
description: Review onboarding, prepare its reviewed delivery, and report the publication path
argument-hint: [target-branch]
---

Read and follow [RULES](../RULES.md).

Land this adoption on **$ARGUMENTS** (default: inspect the remote default branch;
never assume `main`). First report the requested adoption scope: rules-only,
issue sweep, documentation reconciliation, or full adoption. Apply only gates
that the scope can satisfy. Full adoption still requires filled intent,
configuration and structure; narrower scopes do not pretend to satisfy those
gates.

## 1. Inspect, verify and prepare

Check each scope-relevant item and report evidence before committing:

- **Full adoption: `.ai/state/PROJECT.md`** — filled in, no `CHANGEME`, and the non-goals and
  hard constraints are specific enough to reject a plan. Everything downstream
  is graded against this file.
- **`.ai/specs/`** — nothing asserted that has not been checked against the
  code. A spec claiming untrue things is worse than no spec; say so plainly if
  any were retro-written from a document rather than verified.
- **`AGENTS.md`** — the snippet is appended, and no surviving language
  contradicts `.ai/RULES.md`. Grep for "never modify", "source of truth", "do
  not change" and quote whatever you find.
- **`.ai/agents/`** — any pre-existing agent that writes files has `Write`
  and `Edit` in its `tools:` list.
- **`.ai/plans/intake/`** — a readable set of clustered items, not one file per
  `TODO`.
- **Full adoption: `.ai/config.yaml`** — `verification.commands` holds the project's real test
  and lint commands, not an empty list.
- **Deletions** — every retired document was explicitly approved.

Run the required checks on the exact reviewed HEAD, verify the worktree is
clean, and prepare a concise description covering scope, decisions,
contradictions corrected, captured findings and anything still open. Keep
unrelated edits out of the assigned worktree.

## 2. Commit in a reviewed worktree

Group the change so a reviewer can follow it. If the template copy was already
committed separately, this is one commit of onboarding decisions; if not, split
it:

1. the `.ai/` copy, unmodified
2. everything `/onboard` decided — intent, specs, promotions, deletions,
   `AGENTS.md`, intake

Do not include unrelated work. Prepare these commits in an assigned sibling
worktree, review and open the PR, then merge and synchronize the primary target
before continuing. If the worktree has changes that are not part of
the adoption, stop and tell the user rather than sweeping them in.

## 3. Publish only with authority

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
`gh pr create` instead. If neither route is available, report that publication
is unavailable and preserve the branch for an authorized retry; do not claim
delivery from a compare URL alone.

Existing explicit authority to push and merge persists; ask only when that
authority is missing. If publication or PR creation fails, report the failure
and preserve the branch. It is not a delivered adoption and must not fall back
to a local merge.

## 4. Merge and verify

Open the PR with the prepared description, wait for required checks and review,
then merge the exact reviewed head. Refresh the target, verify ancestry and the
tested tree, rerun required checks on the synchronized target, and clean up
only the exact clean merged worktree and branch. Report the PR URL and evidence.

The description covers, briefly:

- What the structure is, and a one-line pointer to `.ai/README.md`
- **Decisions the reviewer should check** — SPECs derived from reviewed code,
  documents retired, and the intent file's non-goals. These are judgment calls,
  not mechanical changes, and they are the reason this is a merge request
  rather than a commit to main.
- Contradictions found and fixed in `AGENTS.md` or existing agents
- FIX and INTAKE items captured, with the evidence distinguishing confirmed
  code defects from unknowns and other fragments
- What was deliberately *not* done — areas left unspec'd, the mode chosen and
  why
- Anything still open: unanswered questions, `.ai/plans/blocked/` entries

Then report the MR or PR URL and the synchronized verification evidence.
