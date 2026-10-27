<!-- workflow: ship; roles: code-reviewer, verifier; produces: pull request and session delivery evidence -->
<purpose>
Publish the verified phase session, keep its draft PR current, wait for required provider checks, and merge only on the user's explicit instruction. A nonpassed or stale verdict has no shipping bypass. Preserve an open session and concrete blockers when publication or merge cannot complete.
</purpose>
<required_reading>
@engineer/RULES.md
@engineer/references/universal-anti-patterns.md
@engineer/references/git-workflow.md
@engineer/references/verification-evidence.md
@engineer/templates/pull-request.md
</required_reading>
<available_agent_types>
Use code-reviewer, verifier, debugger and targeted-fixer, with exact role names and bounded assignments.
</available_agent_types>
<model_selection>
Resolve every exact role with engineer_run query resolve-model and resolve-effort immediately before dispatch. Pass actual values inline and omit each inherited field. A fresh verifier auditing published issue links must be independent of the PR/body author.
</model_selection>
<process>
<step name="initialize">
Parse an optional phase and `--draft`, `--review`, `--no-push`, `--no-merge`. Capture the caller checkout and whether this invocation is returning from verification repair. Read and execute engineer/workflows/_runtime-launcher.snippet.sh, then run session.status. Infer a phase only from one unambiguous matching open phase session; otherwise require an explicit target. Run phase.locate before init.ship, quote and enter its session worktree, then run `engineer_run query init.ship "${PHASE_NUMBER}"`. Recheck branch, worktree and base identity against the selected session. Read actual phase artifacts, state, configured checks and role maps. Optional config fields use explicit config-get queries, never a silently empty assumed bundle property.
</step>
<step name="resolve_session">
Use the locator's matching open session only. Never session.open here or fall back to the current branch. Capture SESSION_WORKTREE, SESSION_BRANCH and SESSION_BASE from the actual session. Stop on a missing/ambiguous/mismatched session; a branch with similar spelling is not the delivery target.
</step>
<step name="preflight_checks">
1. Run `engineer_run query phase.handoff "${PHASE_NUMBER}"` and require ready=true. Reconcile complete summaries, canonical threat IDs, resolved evidence/reasons and every unresolved canonical issue URL. Inspect the complete independent issue-link audit; a prose assertion that links exist is insufficient.
2. Require `engineer_run query verification.status "${PHASE_NUMBER}"` to be passed and `verification.current` to be current. If stale because an authorized repair changed source, run verify-work in ship-repair/return-to-caller mode, then return here. Otherwise report the exact nonpassed/stale blocker; do not ask whether to ship anyway.
3. Require a clean session worktree. Commit only already authorized phase-owned work with the appropriate complete templates; unrelated dirty work is a blocker, never a reason to stash or stage everything.
4. Require the actual session branch and a nonempty SESSION_BASE..SESSION_BRANCH commit range. Do not ship from a protected/default branch or offer a branch-creation shortcut here.
5. Resolve the configured remote/provider and its authenticated identity. Use `gh auth status` only for a GitHub remote; provider readback must identify the same repository. Do not publish to an unverified inferred remote.
6. Run `engineer_run query verification.run-checks` when permitted, reusing only valid current passing receipts. A user-deferred required check remains a shipping blocker.
7. Read every existing phase SECURITY artifact. Require a valid numeric threats_open equal to zero; missing/unparseable status is a blocker when the artifact is required. Do not waive an open threat or treat a failed query as zero.
8. Verify source head and every independent audit still describe the same phase/session before any external write.
</step>
<step name="optional_review">
When --review is explicitly requested, capture a frozen revision and dispatch code-reviewer read-only with inline resolved model/effort, full diff, acceptance, threat records and complete PR/body context. Wait for the report. Correct demonstrated blocking findings through a bounded isolated targeted-fixer and fresh verification; do not turn INFO into required scope. The optional flag does not replace mandatory verification or an independent issue-link audit.
</step>
<step name="prepare_shipping_record">
Use state.record-session to record "Preparing publication" only when continuity fields actually change. Commit the exact authorized bookkeeping before publication. Capture the resulting head and exact changed file list. Do not add a second tracked shipping-note commit after push.
</step>
<step name="final_reconciliation">
Require the canonical passed/current report, check receipts and issue handoff to remain valid after shipping bookkeeping. Capture and compare source/record diffs under verification-evidence.md; a changed source input requires a fresh frozen verification batch, not a waived stale check. Preserve the same active session and ship caller through repair. Join all read-only evidence before accepting the final ship gate.
</step>
<step name="push_branch">
With --no-push, skip every remote write and report the prepared local result, keeping the session open. Otherwise push the exact SESSION_BRANCH with upstream tracking, never force. A rejected push requires inspecting remote divergence and preserving both histories; do not reset remote work. The runtime pr.open also verifies and pushes its clean branch; use its provider result as the publication owner.
</step>
<step name="generate_pr_body">
Read engineer/templates/pull-request.md in full and populate its complete File Template. Preserve every required section and hidden validation marker. Lead with the concrete problem and resulting behavior; document actual implementation, full requirement coverage, tests executed or pending, risks and material limitations. Read authoritative requirements from the init requirements_path and phase requirement IDs; do not invent a requirements.list verb.

Use the canonical issue relationships and provider-confirmed URLs, distinguishing resolved items from pending human acceptance. Compare the exact body links with the independent audit snapshot. Include Record health from planning.validate only when the check was actually run; otherwise state it is pending. Write the exact multiline body to a file. Do not generate a shortened replacement template or interpolate public body text into a shell command.
</step>
<step name="create_pr">
Unless --no-push applies, run `engineer_run query pr.open "${SESSION_BRANCH}" --phase "${PHASE_NUMBER}" --title "${PR_TITLE}" --body-file "${PR_BODY_FILE}"`, adding --base only for the selected intended base. pr.open always creates a draft and updates the existing PR rather than duplicating it; no --draft runtime flag is required. The user-facing --draft flag means keep it draft. Read back the published title, complete body, base, repository, head SHA and URL. If any field differs from the reviewed material, reconcile the exact drift before accepting publication. Attach the created PR to this chat through the host's supported artifact tool when available.
</step>
<step name="refresh_issue_link_audit">
Dispatch a fresh non-author verifier at the current source revision with inline model/effort. Give the provider-read PR head SHA, full published body, canonical URL/link snapshot, phase findings, complete verification report and provider identity. Require independent readback of issue state, exact finding correspondence, threat identity, resolved evidence, PR head/body agreement and required human acceptance. The audit must identify source revision, PR head, body digest/link snapshot, provider repository and its verdict. Join it before merge/readiness. A changed body, head or linked issue invalidates the prior audit; author the canonical updated report through the coordinator and refresh as needed.
</step>
<step name="judge_checks">
Run `engineer_run query pr.checks "${SESSION_BRANCH}" --timeout 240` up to 12 calls, retaining actual provider status, failed/pending check names, head SHA and URLs. Pending/failed exits are status outcomes to inspect, never shell-success fallbacks.

| Provider outcome | Required action |
|---|---|
| All required checks passed on the actual head | Continue to merge_and_close subject to explicit authority |
| Pending within the bounded waits | Keep waiting within the configured limit |
| Still pending after the limit | Report pending checks and leave PR/session open |
| Failed | Diagnose the named failure and perform only authorized bounded repair |
| Missing, cancelled, unreadable or mismatched-head evidence | Report the exact blocker; do not call it green |

Permit at most 2 rounds of CI repair. A known bounded in-scope defect goes to an isolated targeted-fixer; an unknown cause goes to debugger. After integrating a committed repair, run verify-work in ship-repair/return-to-caller mode against a new frozen revision. Require passed/current evidence and a fresh issue-link audit, then push without force and read provider state again. Re-run `engineer_run query pr.checks "${SESSION_BRANCH}" --timeout 240` on the new actual head. Reaching the repair cap never authorizes merge or weakens acceptance. If user testing is deferred, do not trigger tests here; keep their required outcome pending.
</step>
<step name="merge_and_close">
Skip remote merge on --no-push, --no-merge, --draft, any failed/pending gate, or absent explicit merge authorization. Preserve the open PR/session and report why. When no authorization exists, show the exact PR URL, head/base and current green evidence and ask for that concrete merge once; never ask again for authorization already supplied in the session. Silence, a generic workflow-complete message or a mode flag is not merge permission.

With explicit instruction for this exact current PR and all gates current, run `engineer_run query pr.ready "${SESSION_BRANCH}" --phase "${PHASE_NUMBER}"` when required, then `engineer_run query pr.merge "${SESSION_BRANCH}" --phase "${PHASE_NUMBER}" --confirm`. Read back merged state, merged head/base and provider URL. A failed or uncertain response requires provider inspection before retry; do not claim a merge from command text alone.

Run `engineer_run query pr.sync` for remote readback/fetch. This verb does not integrate a local base branch. Resolve an existing clean intended integration checkout and fast-forward it to the provider-confirmed base only when that local sync is within the delivery scope; never switch the user's branch, overwrite dirty work or merge an unrelated branch to make cleanup pass. If no suitable integrated checkout is available, leave the session open and report that closeout blocker.

For existing Folded Todos only, call `engineer_run query phase.reconcile-todos "${PHASE_NUMBER}" --pr "${PR_URL}" --todos ...` with the exact CONTEXT filenames. It requires stable merged provider evidence, closed linked issues, unchanged local digests and accepted-human evidence for UAT. Inspect completed/already-completed/pending reasons; never force pending items complete. Run state.sync-todos and commit only its actual authorized changed records before final closeout, then ensure that commit too is integrated under the delivery contract.

Close with `engineer_run query session.close "${SESSION_BRANCH}"` only from a different clean checkout whose current HEAD actually contains the session HEAD. The runtime rechecks cleanliness and ancestry and has no force bypass. Do not delete an active, dirty, blocked or unintegrated session. Coordinate shared resources separately from Git checkout cleanup.
</step>
<step name="track_shipping">
Do not create tracked post-push bookkeeping, an empty trigger commit, or a hidden check-skip commit. Report the provider-confirmed pr.open URL and actual delivery evidence. A required new record mutation must be integrated and verified honestly; it cannot be disguised as a no-op shipping note.
</step>
<step name="report">
Report PR URL, base, session branch/path, canonical verification revision/verdict, actual provider check outcomes, independent audit state and merge state. For an open PR, state the exact not-merged reason and that the session remains open. For a merged PR, report only confirmed integration and closeout outcomes, including any preserved pending resources or Folded Todos. End with the concrete result; do not start another phase or offer unrelated commands.
</step>
</process>
<anti_patterns>
Never merge without explicit instruction, bypass nonpassed/stale evidence, overwrite a public template with a summary, duplicate an uncertain issue/PR creation, force-push, manufacture a current audit, or close dirty/unintegrated/active sessions.
</anti_patterns>
<success_criteria>
The intended phase session was identified; canonical handoff, current verification, configured checks and provider-confirmed links support publication; a draft PR was opened/updated from the complete template; checks and repairs used actual evidence; merge happened only on explicit instruction; and session closeout reflects actual clean integrated ancestry or a clearly reported preserved blocker.
</success_criteria>
