<!-- workflow
step: ship
agent-roles: orchestrator, code-reviewer, verifier
produces: pull request, merged base branch, closed session
consumes: VERIFICATION.md, SUMMARY.md, ROADMAP.md, STATE.md
-->

<purpose>
Deliver a phase's session worktree. A phase is discussed, planned, executed and
verified onto one session branch; this is the workflow that takes that branch to
the base branch. Confirm current verification, open or update the PR, judge its
checks, then merge only with explicit user authorization; sync the base branch
and close the session after merge.

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
- verifier - owns the independent current issue-link audit
- debugger - diagnoses a failing check with unknown cause
- targeted-fixer - repairs a diagnosed bounded CI defect through the coordinator
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
init bundle carry the same resolved values for ordinary workflow assignments.
Resolve conditional fixer dispatch through [bounded correction dispatch](../references/bounded-correction-dispatch.md).
</model_selection>

<process>

<step name="initialize">
Parse `$ARGUMENTS`: an optional phase number, plus:
- `--draft` — keep a newly created PR as draft; first PRs are always drafts
- `--review` — run a code review over the full diff before opening the PR
- `--no-push` — compose and show the PR body without pushing or opening anything
- `--no-merge` — open or update the PR and stop; the session stays open

`--no-merge` leaves the phase undelivered. Say so in the report, because a
session left open is work on a branch nobody merged, and a later `/ship` of the
same phase is what finishes it.

```bash
_root="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
case "$_root" in /*) ;; *) _root="$(cd -- "$_root" && pwd -P)" ;; esac
for _c in "$_root"/.{ai,claude,codex}/runtime/phase.py "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/runtime/phase.py "${CODEX_HOME:-$HOME/.codex}"/runtime/phase.py; do
  [ -f "$_c" ] && PHASE_RUNTIME="$(cd -- "$(dirname -- "$_c")" && pwd -P)/$(basename -- "$_c")" && break
done
[ -n "${PHASE_RUNTIME:-}" ] || { echo "ERROR: phase runtime not found; run the installer." >&2; exit 1; }
phase_run() { "$(command -v python3 || command -v python)" "$PHASE_RUNTIME" "$@"; }
if [ -z "${PHASE:-}" ]; then
  SESSIONS=$(phase_run query session.status) || { echo "ERROR: session lookup failed; stop and report the runtime error." >&2; exit 1; }
fi
```

If `PHASE` was omitted, parse `SESSIONS` and count entries where `kind` is
`phase` and `status` is `open`. Set `PHASE` to the sole entry's `label` only when
exactly one matches. With zero or multiple matches, stop with `Supply /ship <phase>
to select the phase session.` Do not infer a phase from a blank argument or
project state. For an explicit argument, skip `session.status` and use it for
the locator. Run the locator only after `PHASE` is set:

```bash
LOCATE=$(phase_run query phase.locate "${PHASE}") || { echo "ERROR: phase lookup failed; stop and report the runtime error." >&2; exit 1; }
```

Parse `phase_found`, `padded_phase`, `worktree`, `session`, `branch` and `source`
from `LOCATE`. If `phase_found` is false, report `Phase {PHASE} not found in
the roadmap.` and exit. If `session` is null, report `No validated open phase
session for Phase {PHASE}; /ship requires its existing session worktree.` and exit.
If `worktree` is null, stop and report the locator result as inconsistent.

The locator-selected session must be used before loading phase data. Run the
explicit quoted `cd` to its absolute `worktree`; keep `PHASE_RUNTIME` absolute
so the launcher remains available after the directory change. Stop if `cd` fails.

```bash
cd -- "${worktree}"
INIT=$(phase_run query init.ship "${PHASE}")
```

Parse `phase_number`, `phase_name`, `phase_dir`, `goal`, `artifacts`,
`verification`, `checks`, `checks_configured`, `git`, `commit_docs` and
`response_language` from `INIT`. Confirm `padded_phase`, `branch` and
`worktree` still match `LOCATE` before any ship check. A mismatch stops shipping.


**If `response_language` is set:** all user-facing output MUST be presented in
`{response_language}`; technical terms, code, file paths and commit/PR text stay
in English.

Display: `► SHIP PHASE {phase_number}: {phase_name}`
</step>

<step name="resolve_session">
Use the validated `session` already selected by `phase.locate` before `init.ship`.
Keep its `worktree`, `branch`, `base`, `reused` and `synced` fields. Do not query
`session.status` again, call `session.open`, or fall back to the current branch.
Report the selection before any ship check:

```
Session: {branch} at {worktree}
```
</step>

<step name="preflight_checks">
Run `phase_run query phase.handoff "${phase_number}"` and require `ready: true`.
Review current leftovers and canonical declarations as
[execution handoff](execute-phase.md) requires. Necessary issue tracking is
already authorized; unavailable publication stays retryable/incomplete. This
operational gate does not prove prose completeness or actual human acceptance.
Verify the work is ready to publish. Every check below blocks; none is advisory.

- Reconcile each PLAN's threat links and SUMMARY outcomes through [canonical threat tracking](../references/git-workflow.md#canonical-threat-tracking).
  Read back safe issue status/evidence; keep remaining risks explicit and Pending
  publication as a gap. Preserve the readiness and critical-risk gates below.
- Inspect the current independent [issue-link audit](../references/git-workflow.md#issue-link-audit)
  and its currentness/provider-readback gate. Run `refresh_issue_link_audit` below
  when missing or stale. Truthful tracking drafts may state Pending dependencies;
  merge requires the current audit and last provider readback.

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

   Exit. A tracking draft may already exist under the
   [canonical Git workflow](../references/git-workflow.md), but draft status never
   bypasses this verified-readiness gate.

   Apply the coordinator currentness check in
   [verification evidence](../references/verification-evidence.md). Exact HEAD
   equality is the fast path; otherwise accept only the documented commits that
   publish this phase's exact verification report, after checking every
   intervening commit and requiring a clean worktree. Any other change requires
   re-verification. `verification.status` exposes report metadata and does not
   enforce freshness.

2. **Clean session worktree.**

   ```bash
   git -C "${SESSION_WORKTREE}" status --short
   ```

   If there are uncommitted changes, commit the phase's work with a descriptive
   message. Leave anything else in place and report it as the blocker. Never
   ship over a dirty tree.

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

   If a complete passing result exists at tested revision R, the report remains
   current, and intervening commits publish only that exact phase report, the
   coordinator may use the separate [successor qualification
   procedure](../references/verification-evidence.md#qualifying-check-receipts-across-a-report-only-successor).
   Keep original joined JSON external and supply the exact report path and
   captured HEAD as expected-head. Only qualified: true is complete check
   evidence. For fresh_required indices, run exactly those checks at H with
   verification.run-checks --only-checks INDEX ..., save the JSON externally,
   and requalify with fresh-evidence-file. A proper subset is not a passing
   aggregate. If baseline or proof is invalid, run the complete check set fresh.
   For ordinary preflight reuse, reuse a valid successful receipt only when its
   captured inputs, environment, and configuration match the current check,
   including the captured revision when the check declares `revision: true`.
   Retain the receipt's original tested revision. Rerun any check with missing,
   invalid, unsuccessful, or mismatched evidence through
   `verification.run-checks`; its default receipt behavior reuses only valid
   successful matches. This ordinary reuse rule is separate from successor
   qualification above.

   This qualifies check evidence, not report currentness; apply both gates.
   Preserve the report's original tested revision. Failing or ambiguous checks
   block and follow the existing diagnosis route.
</step>

<step name="optional_review">
**Only when `--review` was passed.**

```
Agent(
  prompt="
Review everything Phase {phase_number} is about to publish.

**Diff:** {SESSION_BASE}...{SESSION_BRANCH}, in {SESSION_WORKTREE}
**Frozen revision:** {session HEAD}; use it with the configured check receipts
from preflight.
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

<step name="prepare_shipping_record">
Before final reconciliation, commit the truthful pre-publication session status.
The PR URL does not exist yet; do not claim the phase shipped or add an invented
URL. The session's `pr.open` metadata records the actual PR after push.

If STATE already records `Preparing publication` for this same session branch,
set `preparation_record_changed=false` and skip the redundant record/commit. A
repeated ship run must not create a no-op lifecycle commit merely to refresh
verification. Otherwise set it true before writing and committing the record.

```bash
phase_run query state.record-session \
  --stopped-at "Preparing publication for phase ${phase_number} on ${SESSION_BRANCH}" \
  --status "Preparing publication"
phase_run query commit "docs(state): prepare phase ${phase_number} publication" \
  --files .planning/STATE.md
```
</step>

<step name="final_reconciliation">
If `preparation_record_changed=false`, reuse the already-passed report only when
the existing report is still current under the shared exact-revision/report-only
rule and the preflight receipts remain valid for this revision. In that case,
skip another verifier dispatch and report commit.

If the status record changed or currentness/evidence no longer holds, capture
the new revision and start configured checks plus a provisional read-only
verifier together. The verifier receives pending check results and reviews the
actual STATE record diff, the phase goal and source evidence. After every check
joins, resume the verifier with the complete results/receipts. On a pass, the
coordinator preserves the revision actually examined, writes the tracked phase
report, and commits only that report as the last local write.
Apply the shared [verification evidence lifecycle](../references/verification-evidence.md).
If this reconciliation is not `passed`, stop before push. A source repair
requires a fresh `/verify-work` cycle before another push attempt.
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
Read the [pull request template](../templates/pull-request.md) and copy only its **File Template** block into the PR body file.
Populate it from the phase records:

- Goal: phase goal.
- Changes: concise outcomes from each summary.
- Requirements or Issues: inspect recorded requirement status and list relevant issues:

  ```bash
  phase_run query requirements.list
  ```

  State when a claimed requirement remains `Pending`.
- Verification: exact revision, actual commands and results, and the Acceptance
  definition from `VERIFICATION.md`.
- Known gaps: accepted gaps and their reasons.
- Risks or rollback: link/status table with each owning PLAN/Threat ID, issue,
  outcome, Git state and evidence; list open risks and practical rollback.
  Follow [canonical threat tracking](../references/git-workflow.md#canonical-threat-tracking); audit closing references
  against scope-complete mitigation and existing explicit closure authority.
- Stack fields: include only for a dependent PR; use the recorded own-change boundary.

```bash
phase_run query planning.validate
```

Record planning-health findings and their repair verbs in the template's Known
gaps list. Preserve its section and field shapes.

```bash
phase_run query pr.validate --body-file "${body_path}"
```

Include each declared issue's canonical URL in the body. Use resolving references
only for demonstrated accepted work; deferred/unresolved/pending-human followups
use plain links and never closing keywords. `pr.open` binds the existing phase
session automatically and validates the effective body even on body-omitted edits.
Show the composed body to the user before opening the PR.

Compare this composed body/link snapshot with the independent
[issue-link audit](../references/git-workflow.md#issue-link-audit). Apply its
invalidation rules through `refresh_issue_link_audit`; Pending drafts do not
establish readiness.
</step>

<step name="create_pr">
**Skip when `--no-push` was passed.**

```bash
phase_run query pr.open "${SESSION_BRANCH}" \
  --title "Phase ${phase_number}: ${phase_name}" \
  --body-file "${body_path}" --draft
```

Use the verb, not `gh` directly: it records the PR against the session, which
`session.close` later reads to prove the work merged. Always create a first PR as
a draft for tracking, even when `/ship` was called without `--draft`.

`pr.open` updates the existing PR on reruns. The runtime preserves its draft
state when editing; it does not mark the PR ready automatically. Report the
`created`, `updated` and `isDraft` fields. Opening a PR can start CI; it does not
mean checks have finished or that the PR is ready to merge.

Read back the actual published body/links and provide that snapshot to the
independent [issue-link audit](../references/git-workflow.md#issue-link-audit).
Missing or changed readback remains a gap; publication success is not audit success.
Recheck the saved snapshot and linked issue states after publication; run
`refresh_issue_link_audit` for missing or stale evidence.
</step>

<step name="refresh_issue_link_audit">
Reuse only a current verifier-owned [issue-link audit](../references/git-workflow.md#issue-link-audit).
Whenever it is missing or stale, capture the current source revision, actual
PR/MR head SHA, exact proposed/published body and complete link snapshot, and
timestamped provider readback (or explicit Pending dependency). Resolve model
and effort for `verifier` using the existing dispatch rules, then dispatch a
fresh non-author verifier:

```
Agent(
  prompt="Perform the mandatory [Issue-link audit](../references/git-workflow.md#issue-link-audit).
Source revision: {current_source_revision}; actual PR/MR head SHA: {provider_head_sha}.
Exact body/link snapshot: {current_body_and_links}.
Provider readback: {timestamped_provider_readback_or_Pending_dependency}.
Read CONTEXT, owning PLANs and SUMMARY outcomes at the supplied revision.
Obtain/validate actual provider readback and return the canonical audit packet.
Remain read-only. Unavailable evidence stays Pending; do not claim a pass.",
  subagent_type="verifier",
  ${models['verifier'] === 'inherit' ? '' : `model="${models['verifier']}",`}
  ${efforts['verifier'] === 'inherit' ? '' : `effort="${efforts['verifier']}",`}
  description="Audit current PR/MR issue links"
)
```

Join the result and compare it to the current snapshot. After publication,
recheck actual saved body/links and provider state; refresh affected evidence
again if changed. Missing readback blocks merge under the existing gate.
</step>

<step name="judge_checks">
**Skip when `--no-push` was passed.**

```bash
phase_run query pr.checks "${SESSION_BRANCH}" --wait 240
```

Repeat the call while `state` is `pending`, up to 12 calls. Never hand the wait
to the user.

The verdict decides; you do not. Report the state and the check names behind it
exactly as observed:

| `state` | What to do |
|---|---|
| `passing` | Continue to the merge gate |
| `pending` | Still pending after 12 calls: report the unsettled checks and their links as the blocker |
| `failing` | Fix and re-judge (below). Keep the same pull request; never open a second one |
| `none` | The pull request has no checks. The `verification.run-checks` run in preflight is the project's own evidence — carry `--local-checks-passed` into the merge only because it passed there. If no checks are configured either, there is no evidence and `pr.merge` refuses; report that refusal as correct |

**Fixing a failing check** — at most 2 rounds:

1. Read each failing run's log: `gh run view <run-id> --log-failed`
2. Send unknown causes to an isolated `debugger` with check names, log excerpts and current revision.
3. Route complete diagnosed bounded findings/proposals through [bounded correction dispatch](../references/bounded-correction-dispatch.md).
4. Return incomplete or contradictory inputs to the originating debugger/reviewer via the coordinator; send broader authorized repairs to preparer/coder.
5. From the session worktree, integrate committed owned repairs. Do not push yet: the source
   change invalidates verification for this branch.
6. Invoke `/verify-work {phase_number}` in ship-repair/return-to-caller mode.
   Re-run local checks and final reconciliation on the repaired revision; do not
   repeat success bookkeeping or auto-start another `/ship`.
7. Only after it returns `passed`, push the repaired branch and judge the exact
   new tip with `phase_run query pr.checks "${SESSION_BRANCH}" --wait 240`.

Still failing after round 2: report it with its logs as the blocker.
</step>

<step name="merge_and_close">
**Skip when `--no-push` or `--no-merge` was passed.** On `--no-merge`, report the
pull request URL and that the session stays open, then go to the report step.

- Audit the PR/MR linked outcomes and closing references through [canonical threat tracking](../references/git-workflow.md#canonical-threat-tracking).
- Require the current independent [issue-link audit](../references/git-workflow.md#issue-link-audit)
  and last provider readback before merge eligibility. Compare source revision,
  actual body/link snapshot, verified URLs and outcomes; stale or missing required
  readback is a gap with its dependency and blocks merge. Obtain fresh applicable
  independent evidence after material changes, including ordinary follow-up links.
  Run `refresh_issue_link_audit` for a missing or stale verifier audit, then recheck
  the current provider snapshot before proceeding.
- Keep neutral links for unresolved, accepted, deferred and mitigated risks without
  verified closure eligibility. List actual closed only with evidence/readback;
  never infer closure from merge.

Merging moves the base branch. Merge only with the user's explicit
authorization. If the current instruction already authorizes this merge, do not
ask again. Otherwise show the PR URL, check verdict and merge method, then ask.
`workflow.auto_advance` never authorizes a merge.

Use AskUserQuestion (header: "Merge"; options: "Merge now" — land Phase {N} and
close its session / "Leave it open" — stop here and leave the PR for review). In
text mode, ask the same question as a numbered list.

On "Leave it open", report the URL and stop. The session stays open and a later
`/ship {N}` resumes from here.

On "Merge now":

```bash
if [ -n "${qualified_head:-}" ]; then
  MERGE=$(phase_run query pr.merge "${SESSION_BRANCH}" --expected-head "${qualified_head}")
else
  MERGE=$(phase_run query pr.merge "${SESSION_BRANCH}")
fi
```

When successor qualification was used, set qualified_head to its exact H and
pass it as expected-head. The runtime requires local HEAD and the OPEN PR
headRefOid to equal H, then passes --match-head-commit H to gh pr merge and
requires matching MERGED/head readback. Local or provider head movement blocks
the merge. Without a qualified successor, the existing invocation and gates
apply.

Require `merged: true` with matching number/URL/head and observed `pr_state:
MERGED`. Command success alone is insufficient. Unknown/mismatched readback keeps
the PR/session and requires readback of that same canonical PR; never call
`pr.merge` again to settle uncertainty or restart source reviews for unchanged code.
Only after verified merge, sync the base and require `synced: true`:

```bash
phase_run query pr.sync
```

From the synchronized primary checkout, select only the exact CONTEXT Folded Todos
filenames (never reviewed-only or unselected items), then run:

```bash
phase_run query phase.reconcile-todos "${phase_number}" \
  --pr "${pr_url}" --todos "${folded_todo_files[@]}"
```

Skip this call when no TODOs were folded. It independently validates the phase
session's matching MERGED PR and each linked CLOSED issue. CLOSED UAT still marked
PENDING HUMAN acceptance remains pending. Record completed/already-completed/pending
items and their issue URLs. For delayed/unavailable readback, report the returned
reconciliation-only `retry` command and pending filenames/URLs; preserve those
records and the session. No fresh review or issue creation is needed for this retry.

Commit successful TODO/STATE-only retirement through the existing runtime-owned
TODO planning-record policy in [worktree sessions](../references/worktree-sessions.md).
Collect only each selected moved record's old/new paths in `todo_record_paths`:

```bash
phase_run query state.sync-todos
phase_run query commit "chore(todos): reconcile merged phase ${phase_number}" \
  --files "${todo_record_paths[@]}" .planning/STATE.md
```

Publish that planning-record-only commit under the existing policy. Never add a
new source commit to the merged PR. Close the source session only after selected
reconciliation and record publication settle:

```bash
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
The pre-publication session status was committed before final reconciliation.
After `pr.open`, use its returned URL/session metadata in the user-facing report;
do not add a tracked post-push bookkeeping commit, which would make verification
stale. Report the observed publication outcome accurately.
</step>

<step name="report">
```
Phase {phase_number} shipped.

PR: {url} ({created ? "opened" : "updated"}{isDraft ? ", draft" : ""})
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
- Why: {declined at the merge question | checks blocked: names and links}
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
- Don't merge without the user's explicit instruction; `workflow.auto_advance` never authorizes merge
- Don't hand waiting on `pending` checks to the user
- Don't tell the user to re-run `/ship`
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
- [ ] Merge explicitly authorized by the user; do not ask again when current authorization already covers it
- [ ] `workflow.auto_advance` does not authorize merge
- [ ] Base branch synced and the session closed, or its preservation reported
      with the reason, unforced
</success_criteria>
