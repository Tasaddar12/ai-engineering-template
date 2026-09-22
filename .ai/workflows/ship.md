<!-- workflow
step: ship
agent-roles: orchestrator, code-reviewer
produces: pull request, merged base branch, closed session
consumes: VERIFICATION.md, SUMMARY.md, ROADMAP.md, STATE.md
-->

<purpose>
Deliver a phase's session worktree. A phase is discussed, planned, executed and
verified onto one session branch; this is the workflow that takes that branch to
the base branch. It confirms the phase actually passed verification, opens the
pull request, judges its checks, and -- once the user confirms -- merges, syncs
the base branch and closes the session.

Shipping is the only route a phase's work has to the base branch. It does not
decide that unverified work is good enough, and it does not merge on a check
verdict that is anything other than genuinely green.
</purpose>

<required_reading>
@~/.ai/references/universal-anti-patterns.md
</required_reading>

<available_agent_types>
Valid subagent types (use these exact names — never fall back to a generic agent):
- code-reviewer — reviews the changes being published
</available_agent_types>

<model_selection>
Model and effort are injected inline at dispatch, never read from an agent's
frontmatter. Resolve both from the runtime and pass them on the `Agent(...)`
call:

```bash
phase_run query resolve-model <agent> --raw
phase_run query resolve-effort <agent> --raw
```

A result of `inherit` means the project set no override — **omit that argument
entirely** and let the host choose. Pass `model` only when resolution returned a
model alias, and `effort` only when it returned one of `low`, `medium`,
`high`, `xhigh` or `max`. The two resolve independently: a role can carry an
effort and no model, or the reverse. The `models` and `efforts` maps in each
init bundle carry the same resolved values for every agent that workflow
dispatches.
</model_selection>

<process>

<step name="initialize">
Parse `$ARGUMENTS`: an optional phase number, plus:
- `--draft` — open the PR as a draft
- `--review` — run a code review over the full diff before opening the PR
- `--no-push` — compose and show the PR body without pushing or opening anything
- `--no-merge` — open or update the PR and stop; the session stays open

`--no-merge` leaves the phase undelivered. Say so in the report, because a
session left open is work on a branch nobody merged, and a later `/ship` of the
same phase is what finishes it.

```bash
_root="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
for _c in "$_root"/.{ai,claude,codex}/runtime/phase.py "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/runtime/phase.py "${CODEX_HOME:-$HOME/.codex}"/runtime/phase.py; do
  [ -f "$_c" ] && PHASE_RUNTIME="$_c" && break
done
[ -n "${PHASE_RUNTIME:-}" ] || { echo "ERROR: phase runtime not found; run the installer." >&2; exit 1; }
phase_run() { "$(command -v python3 || command -v python)" "$PHASE_RUNTIME" "$@"; }
INIT=$(phase_run query init.ship "${PHASE}")
```

Extract: `phase_found`, `phase_number`, `padded_phase`, `phase_name`, `phase_dir`,
`goal`, `artifacts`, `verification`, `checks`, `checks_configured`, `git`
(`base_branch`, `current_branch`, `is_protected`, `has_remote`), `commit_docs`,
`response_language`.

**If `response_language` is set:** all user-facing output MUST be presented in
`{response_language}`; technical terms, code, file paths and commit/PR text stay
in English.

Display: `► SHIP PHASE {phase_number}: {phase_name}`
</step>

<step name="resolve_session">
The phase's work is on its session branch, not in the checkout you were invoked
from. Find it before checking anything, because every check below has to run
against the tree being shipped:

```bash
phase_run query session.status
```

Take the open session whose `kind` is `phase` and whose `label` is
`${padded_phase}`. **Run every subsequent command in this workflow from its
`worktree`**, and use its `branch` wherever a branch is named.

If there is no such open session, the phase was never worked in one. Stop:

```
No open session for Phase {N}.

Its work was either never started, or already delivered. Run `/progress` to see
where the phase stands; `/discuss-phase {N}` opens a session for new work.
```

Do not fall back to the current branch. Shipping whatever happens to be checked
out is how unrelated work reaches the base branch.

Report it in one line before continuing:

```
Session: {branch} at {worktree}
```
</step>

<step name="preflight_checks">
Verify the work is ready to publish. Every check below blocks; none is advisory.

1. **Verification passed.**

   ```bash
   phase_run query verification.status "${phase_number}"
   ```

   Only `status: passed` may ship. Any other value — `gaps_found`,
   `human_needed`, or no report at all — blocks:

   ```
   Cannot ship Phase {N}: verification is {status or "missing"}.

   Run `/verify-work {N}` and resolve its findings first.
   ```

   Exit. Do not offer a bypass: an unverified PR is exactly what this gate exists
   to prevent.

   Also compare the report's `revision` to the current HEAD. If the code moved
   since verification, the report is stale — say so and require re-verification.

2. **Clean session worktree.**

   ```bash
   git -C "${SESSION_WORKTREE}" status --short
   ```

   If there are uncommitted changes, ask the user to commit them first. Shipping
   over a dirty tree publishes something nobody reviewed, and the uncommitted
   part does not reach the pull request at all.

3. **The session branch is checked out, and it is not the base branch.**

   ```bash
   git -C "${SESSION_WORKTREE}" rev-parse --abbrev-ref HEAD
   ```

   This must report the session branch. If it reports the base branch, you are
   not in the session worktree — go back and resolve it. There is no offer to
   create a branch here: `session.open` already did that, and a `/ship` that
   branches for itself is shipping work from outside the session.

4. **The session has something to deliver.**

   ```bash
   git -C "${SESSION_WORKTREE}" log --oneline "${SESSION_BASE}..${SESSION_BRANCH}"
   ```

   An empty range means the phase wrote nothing to its branch. Report that and
   stop rather than opening an empty pull request.

5. **Remote configured.**

   If `git.has_remote` is false:

   ```
   No `origin` remote configured — there is nowhere to open a pull request.
   ```

   Exit.

6. **`gh` available and authenticated.**

   ```bash
   gh auth status
   ```

   If `gh` is missing or unauthenticated, report the setup steps and exit.

7. **Configured checks pass.**

   ```bash
   phase_run query verification.run-checks
   ```

   A failing check blocks. Report the command and its output tail.
</step>

<step name="optional_review">
**Only when `--review` was passed.**

```
Agent(
  prompt="
Review everything Phase {phase_number} is about to publish.

**Diff:** {SESSION_BASE}...{SESSION_BRANCH}, in {SESSION_WORKTREE}
**Phase goal:** {goal}

Review the changed source for correctness bugs, security issues and anything a
reviewer on the PR would rightly object to. Judge the code as it stands.

Return:
## REVIEW
Findings: <numbered, each with file:line and severity (critical|warning)>
",
  subagent_type="code-reviewer",
  ${models['code-reviewer'] === 'inherit' ? '' : `model="${models['code-reviewer']}",`}
  ${efforts['code-reviewer'] === 'inherit' ? '' : `effort="${efforts['code-reviewer']}",`}
  description="Pre-ship review of phase {phase_number}"
)
```

Critical findings block the PR. Fix them, re-verify, and start again — do not
publish with a known critical finding and a note about it.
</step>

<step name="push_branch">
**Skip when `--no-push` was passed.**

```bash
git -C "${SESSION_WORKTREE}" push -u origin "${SESSION_BRANCH}"
```

If the push is rejected because the remote moved, report it and stop. Do not
force-push: the remote branch may hold work you cannot see.
</step>

<step name="generate_pr_body">
Compose the PR body from the phase's own records — its summaries and verification
report — rather than from the diff. A reader wants to know what shipped and what
was confirmed, not a file list.

```markdown
## Phase {N}: {phase_name}

{goal}

### What shipped

{For each {padded_phase}-{MM}-SUMMARY.md: one line naming the plan and what it
delivered.}

### Requirements covered

{Each REQ id claimed by the phase, and where it is satisfied.}

{Read each one's recorded status:}

```bash
phase_run query requirements.list
```

{Say so in the PR body when one the phase claims still reads `Pending`.}

### Verification

Status: {verification.status} (revision {verification.revision})

{The Acceptance section from VERIFICATION.md: what was confirmed, and how.}

{If checks are configured:}
Checks: {each command and its result}

{If the report recorded accepted gaps:}
### Known gaps

{Each one, with why it was accepted rather than closed.}
```

```bash
phase_run query planning.validate
```

Append a short `### Record health` section when `warning_count` is above zero,
naming each finding and the verb that resolves it. This never blocks the PR.

Show the composed body to the user before opening the PR.
</step>

<step name="create_pr">
**Skip when `--no-push` was passed.**

```bash
phase_run query pr.open "${SESSION_BRANCH}" \
  --title "Phase ${phase_number}: ${phase_name}" \
  --body-file "${body_path}" \
  ${draft:+--draft}
```

Use the verb, not `gh` directly: it records the pull request against the session,
which is what `session.close` later reads to prove the work merged.

`pr.open` is idempotent. On a re-run it edits the pull request already open for
this branch rather than failing, so a second `/ship` of the same phase updates
that pull request instead of creating a rival one. The result's `created` and
`updated` fields say which happened — report it.

Opening a PR can start CI. It does not mean the checks have finished, and it
never means the PR is ready to merge.
</step>

<step name="judge_checks">
**Skip when `--no-push` was passed.**

```bash
phase_run query pr.checks "${SESSION_BRANCH}"
```

The verdict decides; you do not. Report the state and the check names behind it
exactly as observed:

| `state` | What to do |
|---|---|
| `passing` | Continue to the merge gate |
| `pending` | Report the unfinished checks and stop. Re-run `/ship {N}` when they settle — waiting is the whole point of the state |
| `failing` | Report the failing check names and stop. Fix them on this same branch, in this same session worktree, and push again. The pull request stays open and keeps its history; do not open a second one |
| `none` | The pull request has no checks. The `verification.run-checks` run in preflight is the project's own evidence — carry `--local-checks-passed` into the merge only because it passed there. If no checks are configured either, there is no evidence and `pr.merge` refuses; report that refusal as correct |
</step>

<step name="merge_and_close">
**Skip when `--no-push` or `--no-merge` was passed.** On `--no-merge`, report the
pull request URL and that the session stays open, then go to the report step.

Merging moves the base branch. Unless `workflow.auto_advance` is true, confirm
first, showing the pull request URL, the check verdict and the merge method.

Use AskUserQuestion (header: "Merge"; options: "Merge now" — land Phase {N} and
close its session / "Leave it open" — stop here and leave the PR for review). In
text mode, ask the same question as a numbered list.

On "Leave it open", report the URL and stop. The session stays open and a later
`/ship {N}` resumes from here.

On "Merge now":

```bash
phase_run query pr.merge "${SESSION_BRANCH}"
phase_run query pr.sync
phase_run query session.close "${SESSION_BRANCH}"
```

Add `--local-checks-passed` to `pr.merge` only in the `none` case above, and only
because the project's own checks passed in preflight.

`session.close` returns `preserved: true` with a reason when it cannot prove the
work merged. Report that as it stands and leave the worktree in place. **Never
pass `--force` to tidy it up:** a preserved session is unmerged work, and the
reason it was kept is the reason not to delete it.
</step>

<step name="track_shipping">
Record the publication against the phase:

```bash
phase_run query state.record-session \
  --stopped-at "Phase ${phase_number} shipped: ${pr_url}" \
  --status "Shipped"
phase_run query state.add-decision "Phase ${phase_number} published as ${pr_url}"
phase_run query commit "docs(state): record phase ${phase_number} publication" \
  --files .planning/STATE.md
```

**Run this from the session worktree, before the merge gate**, so the record
travels in the pull request it describes. Once the session is merged and closed
its worktree is gone, and a commit made after that has nowhere to land.
</step>

<step name="report">
```
Phase {phase_number} shipped.

PR: {url} ({created ? "opened" : "updated"}{draft ? ", draft" : ""})
Base: {base_branch}
Session: {branch} — {closed | preserved: {reason} | open}
Verification: passed (revision {revision})
Checks: {observed state, and the check names behind it}
Merge: {method, evidence} | not merged ({--no-merge, declined, or check state})

---

## What's Next

{If merged:}
- `/next` — the base branch now carries this phase
- `/progress` — where the project stands

{If not merged:}
- Watch the PR's checks; opening it may have started them
- `/ship {phase_number}` again once they settle — it resumes this same PR
- The session stays open at {worktree}; its work is not on the base branch yet

---
```
</step>

</process>

<anti_patterns>
- Don't ship work whose verification is not `passed` — there is no bypass
- Don't ship against a stale verification report; code that moved needs re-verifying
- Don't force-push a branch that already exists on the remote
- Don't ship from the invoking checkout — resolve the phase's session and work
  from its worktree, or ship nothing
- Don't create a branch here; `session.open` already did, and branching in
  `/ship` means shipping work from outside the session
- Don't merge past a `pending` or `failing` verdict, and don't merge on `none`
  without the project's own passing checks
- Don't open a second pull request because the first one's checks failed — fix
  them on the same branch and push again
- Don't merge without confirming, unless `workflow.auto_advance` says otherwise
- Don't `--force` a preserved session away to make the report look clean
- Don't report CI as passing because the PR opened; report what `gh` observed
- Don't compose the PR body from the diff when the phase's own records say it better
- Don't ship over an uncommitted working tree
</anti_patterns>

<success_criteria>
- [ ] Verification confirmed `passed` and current for the revision being shipped
- [ ] The phase's open session resolved, and every command run from its worktree
- [ ] Session worktree clean, on the session branch, with commits to deliver
- [ ] Remote and `gh` available; configured checks run and passing
- [ ] Review run and critical findings resolved when `--review` was passed
- [ ] Session branch pushed and the PR opened or updated through `pr.open`
- [ ] PR body composed from the phase's summaries and verification report
- [ ] Publication recorded in STATE.md and committed before the merge gate
- [ ] Check verdict judged, reported as observed, and never merged past
- [ ] Merge confirmed with the user unless `workflow.auto_advance` is set
- [ ] Base branch synced and the session closed, or its preservation reported
      with the reason, unforced
</success_criteria>
