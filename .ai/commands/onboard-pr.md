---
description: Review onboarding, prepare its reviewed delivery, and report the publication path
argument-hint: [--scope full|rules-only|issue-sweep|docs-reconciliation] [target-branch]
---

Read and follow [RULES](../RULES.md).

Land this adoption with an explicit scope on **$ARGUMENTS** (default:
`--scope full`; inspect the remote default branch and never assume `main`). The
scope is one of `full`, `rules-only`, `issue-sweep`, or `docs-reconciliation`.
Full adoption checks intent, configuration, structure, records and code-backed
documentation. Each narrow scope checks only its named content plus repository
required checks; it does not bypass CI or claim full-adoption completion.

## 1. Inspect and prepare in the assigned worktree

Inspect the content selected by the scope, report evidence, and prepare the
concrete change in the assigned worktree. Do not require a clean HEAD before
committing the current authorized change:

- **Full scope: `.ai/state/PROJECT.md`** — filled in, no `CHANGEME`, and the non-goals and
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
- **Full scope: `.ai/config.yaml`** — `verification.commands` holds the project's real test
  and lint commands, not an empty list.
- **Deletions** — every retired document was explicitly approved.

Run relevant local checks and the repository's required verification commands
for every scope. Prepare a concise description covering scope, decisions,
contradictions corrected, captured findings and anything still open. Keep
unrelated edits out of the assigned worktree.

## 2. Commit, review and describe

Group the change so a reviewer can follow it. If the template copy was already
committed separately, this is one commit of onboarding decisions; if not, split
it:

1. the `.ai/` copy, unmodified
2. everything `/onboard` decided — intent, specs, promotions, deletions,
   `AGENTS.md`, intake

Do not include unrelated work. Review the resulting commits and write the
concrete publication description before target integration. If the worktree has
changes that are not part of the adoption, stop and report them rather than
sweeping them in.

## 3. Integrate and publish only with authority

Refresh the target branch in the assigned delivery worktree. If it advanced,
integrate that target into the reviewed onboarding branch and rerun the
relevant local checks on the resulting tree. Preserve the exact checked head
for publication; a later target advance requires the same integrate-and-check
cycle again.

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

Existing explicit authority to push and merge persists. If push, PR creation or
merge authority is missing, ask at this concrete publication step. If
publication or PR creation fails, report the failure and preserve the branch;
it is not a delivered adoption and must not fall back to a local merge.

## 4. Merge and verify

After the authorized push and single PR creation above, wait for required CI
and formal review, and merge the exact reviewed head. Fast-forward sync the
primary target and verify ancestry and that its tree equals the tested tree.
Run fresh required checks only if the integrated tree changed; otherwise retain
the checks tied to the exact reviewed head. Then clean up only the exact clean
merged worktree and branch. Report the PR URL and evidence.

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
