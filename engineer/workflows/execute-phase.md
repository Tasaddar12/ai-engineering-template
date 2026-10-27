<!-- workflow: execute-phase; roles: coordinator, executor, code-reviewer -->
<purpose>
Implement the explicitly authorized phase through isolated dependency waves, then carry its verified session work through authorized publication. Continue to verification and shipping in this session without making the user issue routine handoff commands. Honor a real context handoff by preserving worker ownership, commits and continuation evidence. Route findings under engineer/RULES.md#issues-found-while-working: fix in-scope defects, record independent deferred work, and block only work requiring a human decision. Never create new todos during execution.
</purpose>
<core_principle>
The coordinator routes and integrates; each executor reads its full plan and owns only its assigned paths. Shared state, roadmap, requirements, issues and delivery remain coordinator-owned. A timeout does not prove worker exit.
</core_principle>
<required_reading>
@engineer/RULES.md
@engineer/references/worker-handoff.md
@engineer/references/worktree-sessions.md
@engineer/references/parallel-status.md
@engineer/references/git-workflow.md
@engineer/references/verification-evidence.md
</required_reading>
<isolation_reading>
@engineer/references/worktree-branch-check.md
@engineer/references/worktree-path-safety.md
@engineer/workflows/execute-phase/steps/worktree-recovery-policy.md
</isolation_reading>
<available_agent_types>
Use exact roles executor, code-reviewer, doc-writer, verifier, debugger, targeted-fixer; resolve any routed executor type through the runtime. Do not fall back to a generic agent.
</available_agent_types>
<model_selection>
For every exact dispatch role run `engineer_run query resolve-model ROLE --raw` and `engineer_run query resolve-effort ROLE --raw`. Pass resolved model and effort inline, omitting each field whose value is `inherit`. Resolve values again for a routed role or continuation. Empty values never become an explicit model parameter.
</model_selection>
<authority>
Before execution, require the user's explicit instruction to implement this exact phase, recorded with its scope in CONTEXT. Discussion, design approval, planning, readiness, a previous phase's instruction or an unattended mode do not supply that authority. When the current user instruction explicitly authorizes this phase, the coordinator records that actual instruction and scope in CONTEXT and proceeds without asking again. If authority is absent, report the concrete missing instruction and do not implement. Never continue automatically into another phase.
</authority>
Read [bounded correction dispatch](../references/bounded-correction-dispatch.md) before assigning source repair.
<context_handoff>
The coordinator must never stop because a context threshold was reached. Workers converge at a safe committed boundary and return their exact continuation packet; the coordinator persists goals, authority, base/head, completed/remaining scope, dirty paths, pending gates and confirmed lifecycle state, then resumes the authorized bounded continuation in a fresh isolated checkout. Keep orchestration and the execute → verify → authorized ship chain in this session. A threshold does not create a human checkpoint or a request to type another command. Preserve active ownership until actual worker stop is confirmed.
</context_handoff>
<process>
Every execution exit passes through `review_phase_issues` and reports complete, blocked, deferred and human-decision items accurately. An early blocker does not authorize skipping issue reconciliation or claiming the phase shipped.
<step name="parse_args">
Require a phase identifier. Parse `--plan <id>`, `--wave <n>`, `--sequential`, `--resume`, and `--no-review`. Require --wave to be a positive integer and reject incompatible --plan/--wave selection rather than broadening it. Selection flags limit the selected plans; sequential limits concurrency but preserves isolated executor dispatch for every plan. Resume is evidence-based and never repeats a plan with a valid completed summary. An omitted selection means all unfinished plans.
</step>
<step name="initialize">
Read and execute `engineer/workflows/_runtime-launcher.snippet.sh`. Run `engineer_run query phase.locate "${PHASE_NUMBER}"`; stop on a missing or inconsistent result. Quote and enter its returned worktree. Run `engineer_run query init.execute-phase "${PHASE_NUMBER}"`. Read actual plan_records/plans/incomplete_plans, checks_configured, models/efforts, artifact_files and existing *_path fields. Resolve required roles through the exact model/effort verbs and context_window through explicit config-get; do not assume absent init aliases. Stop on a missing phase, zero plans, missing required agents, or an inconsistent locator/bundle identity. A bundle's existence says nothing about the chosen isolation mode.

If the bundle explicitly emits `threat_id_duplicate_count`, keep its duplicate-ID hard stop: read `engineer/workflows/execute-phase/steps/threat-id-gate.md` when nonzero. Apply the complete native-handle bounded observer in `plan-phase/steps/stall-detection-helpers.md` to every executor wait using the executor intervals below and executor completion/SUMMARY contract instead of planner/checker markers. Record actual timestamps and meaningful progress, never infer stop from a timeout. Read executor stall interval and no-progress threshold via `engineer_run query config-get executor.stall_detect_interval_minutes --default 5 --raw` and `engineer_run query config-get executor.stall_threshold_minutes --default 10 --raw`. Preserve the configured response language in prose; do not translate commands or identifiers.
</step>
<step name="open_session">
Inspect phase locator lineage and `engineer_run query session.status`. Reuse the matching phase session. Use `engineer_run query session.adopt phase "${PHASE_NUMBER}"` only for an already named clean isolated checkout with established ownership; otherwise run `engineer_run query session.open phase "${PHASE_NUMBER}"`. Stop on failure, quote and enter the returned worktree, capture SESSION_WORKTREE, SESSION_BRANCH and SESSION_BASE, and re-run init.execute-phase there. Re-check implementation authority in the actual session CONTEXT. Report branch/path in one line. Do not deliver from initialization.
</step>
<step name="safe_resume_gate">
Read `engineer_run query phase-plan-index "${PHASE_NUMBER}"`. Treat phase-plan-index incomplete_plans and each parsed complete flag as candidate selection, then inspect the actual committed SUMMARY status; run only plans lacking valid complete summary evidence; a valid completed SUMMARY and matching commits remain completed even if the worker's terminal session ended abnormally. If all selected plans already have summaries, go to aggregate_results and the normal verification tail. No restart/recovery menu is required. Preserve blocked or partial summaries as blockers to reconcile, never convert them to completion by mere existence.
</step>
<step name="check_blocking_antipatterns">
Read any phase handoff's blocking anti-pattern rows. For each one, state the actual failure mechanism, how it manifested, and the concrete preventive mechanism. Resolve uncertainty from current code/history; otherwise apply the most direct preventive guard within scope, name the row in the closing report and continue independent work. A missing human decision blocks its dependent paths only.
</step>
<step name="preflight">
Require no unrelated dirty changes outside the phase's owned planning records. Read `engineer/workflows/execute-phase/steps/protected-branch.md`. Require the actual session branch, nondefault branch identity and exact session worktree. Do not switch branches or stash unrelated changes to make a preflight pass.
</step>
<step name="resolve_isolation">
Run `engineer_run query dispatch-isolation --raw --phase "${PHASE_NUMBER}"`. Accept exactly:

| Mode | Dispatch contract |
|---|---|
| harness-worktree | Runtime record-agent ownership plus the host's literal worktree isolation flag |
| orchestrator-worktree | Runtime worktree.create path plus an executor root pin to that exact checkout |

There is no third value and no opt-out. Unknown, empty or failed resolution stops dependent execution. The worktree-guard hook is advisory; the mandatory procedure and runtime mutation guards enforce ownership. Run `engineer_run query worktree.reap-orphans` for owned stale lifecycle records without deleting unverified work. An executor branch-check exit 42 marks that plan blocked and preserves its checkout; it never authorizes an isolation downgrade. Report the selected mode in one line.
</step>
<step name="validate_phase">
Run `engineer_run query state.begin-phase "${PHASE_NUMBER}"` only after session, authority and isolation guards pass. Read the phase goal and success criteria; they remain the acceptance source.
</step>
<step name="discover_and_group_plans">
Refresh the assignment table and observed lifecycle under [parallel status](../references/parallel-status.md); preserve bounded observations and confirmed-stop ownership.

Read `engineer_run query phase-plan-index "${PHASE_NUMBER}"`. Preserve declared dependency waves, then move any plans with overlapping files_modified, files_deleted or conflicting shared resources into later waves. Treat a dependency cycle as a planning defect and stop those plans. Read `engineer/workflows/execute-phase/steps/ready-wave-gate.md`; skip named blocked plans and incomplete predecessors. Recompute readiness after an integrated predecessor completes, never dispatch a plan over missing predecessor evidence. Respect the selected plan or wave filter without treating filtered-out work as done. For --wave N, read partial-wave.md before dispatch: select only that effective wave after dependency/overlap/resource grouping, require every predecessor delivered and integrated, and never pull another wave in to make the selection runnable.

Report an assignment table with plan ID, wave, exact owner, paths/deletions, branch, worker state and blocker. Refresh the parallel-status display at dispatch, observation and join. When every selected plan has a complete summary, continue to aggregate_results; blocked, waiting or filtered remaining work appears explicitly in the closing report.
</step>
<step name="execute_waves">
Refresh the assignment table and observed lifecycle under [parallel status](../references/parallel-status.md); preserve bounded observations and confirmed-stop ownership.

Dispatch a wave's independent executor calls in one message unless sequential mode or a single plan applies. Before any coordinator Git operation, enforce the retained cwd-drift guard below and require the exact session root.

**Orchestrator cwd-drift guard (FIRST ACTION at execute_waves entry — #48):**

A prior `Agent(isolation="worktree")` dispatch can silently leave the orchestrator's
cwd inside an agent worktree (or a subdirectory of one). Every subsequent
orchestrator-side git call would then target the wrong tree — this is how a wrong-base
merge nearly shipped ~1000 files. Resolve the _worktree root_ (so a subdirectory cwd
cannot skew the check) and refuse if it is an agent worktree. The discriminator is the
per-agent branch namespace `agent-`/`worktree-agent-`/`worktree-wf_`, NOT the path: the
orchestrator may itself be legitimately invoked from a feature worktree under
`.claude/worktrees/`, so a path-substring refusal would break legitimate runs. Do NOT
pin to `git worktree list`'s first entry — that is the main worktree, the wrong target
when the orchestrator legitimately runs from a feature worktree.

```bash
# gsd:guard=orchestrator-cwd-drift
ORCHESTRATOR_WT=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "FATAL: execute_waves entry is not inside a git worktree (#48)." >&2; exit 1; }
ORCH_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
if printf '%s' "$ORCH_BRANCH" | grep -Eq '^((worktree-)?agent-|worktree-wf_)'; then
  echo "FATAL: orchestrator cwd is inside an agent worktree (branch '$ORCH_BRANCH', root '$ORCHESTRATOR_WT') — refusing to execute waves (#48). A prior isolation=\"worktree\" dispatch drifted the cwd; re-run from the orchestrator's own worktree." >&2
  # #1856 handoff: the refusal above is correct, but on its own it is a dead end —
  # this worktree may hold committed fixes AND uncommitted work, and "re-run from
  # the orchestrator's worktree" silently means abandoning them. Report exactly
  # what is stranded and how to integrate it. Every command here is DIAGNOSTIC:
  # each is `|| true`-guarded so a failure degrades to the plain refusal above
  # rather than crashing before the message prints.
  _WT_BASE=""
  for _ref in "$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)" \
              origin/next origin/main next main; do
    [ -n "$_ref" ] || continue
    if git rev-parse --verify --quiet "$_ref" >/dev/null 2>&1; then _WT_BASE="$_ref"; break; fi
  done
  _WT_AHEAD=""
  [ -n "$_WT_BASE" ] && _WT_AHEAD=$(git rev-list --count "$_WT_BASE..HEAD" 2>/dev/null || true)
  # Count BEFORE truncating, so a long list reports its true size rather than
  # under-reporting what is stranded — which is the whole point of this report.
  _WT_DIRTY_ALL=$(git status --porcelain 2>/dev/null || true)
  _WT_DIRTY_N=0
  [ -n "$_WT_DIRTY_ALL" ] && _WT_DIRTY_N=$(printf '%s\n' "$_WT_DIRTY_ALL" | wc -l | tr -d ' ')
  _WT_HAS_COMMITS=0
  [ -n "$_WT_AHEAD" ] && [ "$_WT_AHEAD" -gt 0 ] 2>/dev/null && _WT_HAS_COMMITS=1

  echo "" >&2
  echo "── Handoff: what is in this worktree (#1856) ──" >&2
  if [ "$_WT_HAS_COMMITS" -eq 1 ]; then
    echo "  $_WT_AHEAD commit(s) on '$ORCH_BRANCH' not on '$_WT_BASE':" >&2
    git log --oneline --no-decorate "$_WT_BASE..HEAD" 2>/dev/null | head -20 | sed 's/^/    /' >&2 || true
    [ "$_WT_AHEAD" -gt 20 ] 2>/dev/null && echo "    … and $((_WT_AHEAD - 20)) more" >&2
    echo "  These live ONLY on this branch. Switching away without integrating loses them." >&2
  fi
  if [ -n "$_WT_DIRTY_ALL" ]; then
    echo "  $_WT_DIRTY_N uncommitted change(s) still in this worktree:" >&2
    printf '%s\n' "$_WT_DIRTY_ALL" | head -20 | sed 's/^/    /' >&2
    [ "$_WT_DIRTY_N" -gt 20 ] 2>/dev/null && echo "    … and $((_WT_DIRTY_N - 20)) more" >&2
  fi
  if [ "$_WT_HAS_COMMITS" -eq 1 ] || [ -n "$_WT_DIRTY_ALL" ]; then
    echo "" >&2
    echo "  To integrate before continuing:" >&2
    [ -n "$_WT_DIRTY_ALL" ] && echo "    1. git add -A && git commit -m 'chore(recover): recover worktree state'   # from THIS worktree" >&2
    echo "    2. cd <orchestrator worktree>   # a checkout whose branch is NOT agent-*/worktree-agent-*" >&2
    echo "    3. git merge --no-ff $ORCH_BRANCH        # or: git cherry-pick <sha>...  for selected commits" >&2
    echo "    4. re-run the phase from there" >&2
    echo "  Verify with: git log --oneline ${_WT_BASE:-HEAD}..$ORCH_BRANCH" >&2
  fi
  exit 1
fi
# Pin to the worktree root; each later orchestrator-side block re-pins the same way
# (see the #3174 cleanup guard). Treat $ORCHESTRATOR_WT as the canonical root for the
# rest of the phase — prefer `git -C "$ORCHESTRATOR_WT"` for cross-step git calls,
# since a bare `cd` does not persist across separate tool invocations.
[ "$ORCHESTRATOR_WT" = "$SESSION_WORKTREE" ] || { echo "FATAL: orchestrator root differs from the phase session worktree." >&2; exit 1; }
export ORCHESTRATOR_WT
cd "$ORCHESTRATOR_WT" || { echo "FATAL: cannot cd to orchestrator worktree '$ORCHESTRATOR_WT' (#48)." >&2; exit 1; }
```


For each ready wave:
1. Describe what is being built and the observable outcomes, using actual plan objectives.
2. Capture `EXPECTED_BASE=$(git rev-parse HEAD)` and EXPECTED_BRANCH in the session. Read `per-plan-worktree-gate.md` to extract each plan's declared files and deletions; block any submodule intersection or unparseable scope rather than running outside isolation.
3. Read `per-plan-executor-routing.md`. Default EXECUTOR_TYPE to executor. Resolve its model and effort inline. Read TDD applicability only when the runtime registers `phase.tdd-applicable`; a failed supported query is a blocker, not a false result. Carry TDD_APPLICABLE and the plan's actual check constraints in the dispatch packet.
4. For harness-worktree, dispatch the executor with literal `isolation="worktree"` and embed the runnable branch-check guard from engineer/references/worktree-branch-check.md with the captured base and assigned identity. Read the actual worker branch/path from host metadata, then register with `engineer_run query worktree.record-agent "${plan_id}" --phase "${PHASE_NUMBER}" --branch "${WORKER_BRANCH}" --path "${WORKER_PATH}" --base "${EXPECTED_BASE}" --files ... --deletions ...`. Never register the coordinator branch as the worker. Missing metadata blocks integration; reconcile it from the completed worker and Git evidence after confirmed stop rather than inventing a path.
5. For orchestrator-worktree, call `engineer_run query worktree.create "${plan_id}" --phase "${PHASE_NUMBER}" --base "${EXPECTED_BASE}" --files ... --deletions ...`. Read the returned path, branch and base and dispatch the same executor Agent into it with the complete project_root_pin from `orchestrator-root-pin.md`. No process-spawn lane or unisolated alternative is permitted.
6. Give each executor this complete packet and resolve actual placeholders before dispatch:
```text
<assignment>
Phase/plan: {phase and exact plan ID}
Work root/branch/base: {assigned values}
Ownership: {complete files_modified, files_deleted, resources}
<required_reading>
AGENTS.md; assigned role; complete PLAN and CONTEXT; canonical references;
engineer/references/worker-handoff.md; worktree-path-safety.md; applicable assigned skills.
</required_reading>
<handoff>{actual continuation evidence or explicitly none}</handoff>
<context_window>{actual supported context window; prior-wave summaries only when at least 500000}</context_window>
<isolation>{resolved mode and complete runnable branch check or root pin}</isolation>
<constraints>
Execute only the assigned plan, preserve locked acceptance, declare new scope needs, and honor explicit test deferral. Commit each meaningful owned slice atomically. Do not change STATE, ROADMAP, REQUIREMENTS or coordinator-owned issue records. Write and commit the complete required SUMMARY before returning, including status, scope, acceptance, documentation, executed checks or explicit pending checks, issue_refs, and remaining/deferred findings. A wrong plan returns blocked with evidence. No self-review or publication.
</constraints>
<output>
Return complete or blocked, exact commit(s), SUMMARY path, work root/branch/base and every unresolved finding. A complete return requires the owned commits and required summary on disk.
</output>
</assignment>
```
7. ORCHESTRATOR RULE: after dispatch, wait before touching worker-owned files or integrating its work. A host timeout is not confirmed exit. Do not steer a working executor to finalize; read executor-progress-policy.md. Observe real commits, summaries and worker activity. Resolve an abnormal end with completion-reconciliation.md before considering redispatch.
8. After confirmed stop, recognize `## Self-Check: FAILED` as a failed self-check requiring evidence review, not completion. Verify actual commits and SUMMARY against phase-plan-index and Git log. A complete message without a committed complete SUMMARY is blocked. Continue a genuine context handoff in a fresh isolated checkout from its recorded scope; consume it only after integration. Permit at most two stall/handoff reattempts, measured from the last meaningful progress, without asking for routine recovery. Unknown failures go to debugger; preserve every failed checkout.
9. Join every worker in the wave before integration. Merge only complete committed owned slices through `engineer_run query worktree.merge-wave --phase "${PHASE_NUMBER}"`. Require the runtime registry to account for this wave's exact plan IDs and completed states; do not invent a plan-filter flag. The runtime verifies declared scope and deletions; a deletion must be explicitly in files_deleted, never inferred from files_modified. An undeclared deletion or conflict blocks integration and goes to a bounded isolated correction; never remove the guard. Run `engineer_run query worktree.cleanup-wave --phase "${PHASE_NUMBER}"` only after merge evidence exists. Keep blocked or unmerged worktrees intact.
10. Run run_checks, then track_integrated_slice. Continue independent later waves after failures, skipping only true dependents. If all agents fail from one systemic cause, stop dispatch and report the shared blocker.
</step>
<step name="checkpoint_handling">
Resolve choices within the user's delegated discretion from approved context and code evidence, recording consequential outcomes with state.add-decision. An unresolved locked decision, credential, irreversible approval or human acceptance blocks only its dependent plan. Record the exact required human action in the closing report; do not auto-approve it. Re-dispatch approved continuation work only in a fresh isolated checkout after confirmed worker stop.
</step>
<step name="run_checks">
Refresh the assignment table and observed lifecycle under [parallel status](../references/parallel-status.md); preserve bounded observations and confirmed-stop ownership.

Run `engineer_run query verification.run-checks` against the integrated session revision when execution is permitted. Reuse only passing receipts whose declared inputs and fingerprints remain current. A user-deferred test remains pending and blocks any verdict requiring it; do not run it or fabricate a receipt. Join all configured results. A failed or timed-out check blocks dependent integration/completion and routes to bounded targeted-fixer/executor correction, or debugger for an unknown cause. After repair, rerun only invalidated/required checks on the new revision and rejoin their actual results.
</step>
<step name="track_integrated_slice">
Run review_phase_issues before the draft write, including every unresolved canonical issue URL. On normal completion, deferral, blocked/halted work or early termination, reconcile all available committed producer records before returning; missing publication remains a concrete blocker. The same-execution fixed-work exemption applies only to ordinary findings actually resolved with evidence and no remaining obligation; it creates no repeated issue for that exact resolved scope. It never waives planned/unplanned threat tracking or human acceptance.

When publication is authorized, push the session branch with upstream tracking and no force, then run `engineer_run query pr.open "${SESSION_BRANCH}" --title "${TITLE}" --body-file "${BODY_FILE}" --phase "${PHASE_NUMBER}"`. Build the complete current canonical PR template, validate issue links, and read back provider state under engineer/references/git-workflow.md. Open a draft on the first push and refresh its full title/body after every meaningful integrated slice. Do not publish when the user explicitly withheld delivery.
</step>
<step name="aggregate_results">
Reconcile every PLAN/SUMMARY through [canonical threat tracking](../references/git-workflow.md#canonical-threat-tracking) and the complete _canonical-threat-tracking.md procedure. The canonical default for each new planned risk, including accepted/deferred exposure, is a stable checklist entry unless an existing full-scope tracker already remains canonical. Keep canonical trackers linked; standalone tracking is required for a distinct unplanned risk without one. Preserve each PLAN register and separately report outcome evidence. Include every remaining finding and human dependency in the closing report.

After all waves:

```markdown
## Phase {X}: {Name} Execution Complete

**Waves:** {N} | **Plans:** {M}/{total} complete

| Wave | Plans            | Status     |
| ---- | ---------------- | ---------- |
| 1    | plan-01, plan-02 | ✓ Complete |
| CP   | plan-03          | ✓ Verified |
| 2    | plan-04          | ✓ Complete |

### Plan Details

1. **03-01**: [one-liner from SUMMARY.md]
2. **03-02**: [one-liner from SUMMARY.md]

### Issues Encountered

[Aggregate from SUMMARYs, or "None"]
```

</step>


Reconcile threats in every PLAN/SUMMARY against stable canonical threat identities. List uncovered phase requirements as gaps. Report all still-open findings, deferred work and human-decision blockers explicitly. Do not create todos. If `--wave` was selected, read partial-wave.md and report remaining waves without claiming the phase complete. Set PARTIAL_EXECUTION when any phase plan remains unfinished. Continue required review/issue reconciliation and accurate progress/session records, then RETURN before run_verify_work, full phase completion or shipping when PARTIAL_EXECUTION is true.
<step name="code_review_gate">
Require the independent [issue-link audit](../references/git-workflow.md#issue-link-audit) for the exact source and provider snapshot.

If the user explicitly requested `--no-review`, record the optional extra review as skipped. Otherwise read `engineer_run query config-get workflow.code_review --raw`: if it returns `false`, record the configured optional extra review as skipped; if it returns `true`, or the key is absent (default `true`), dispatch the fresh read-only code-reviewer with configured `verification.run-checks` at one frozen revision after integration. A config read error blocks; never treat an unreadable value as disabled. Give the reviewer complete goal, CONTEXT, plans, summaries, source diff and locked decisions; resolve model/effort inline. Wait for every result before accepting evidence or repairing source. Critical correctness, security and acceptance failures block completion; INFO stays advisory. Route demonstrated in-scope failures through bounded isolated correction and run a new frozen batch after source changes. The flag and setting skip only this optional extra review. Required independent review owned by `verify-work`, security review, acceptance evidence and configured checks remain mandatory before closure.
</step>
<step name="review_phase_issues">
Require the independent [issue-link audit](../references/git-workflow.md#issue-link-audit) for the exact source and provider snapshot.

Read and execute the complete engineer/workflows/_canonical-threat-tracking.md procedure for planned and unplanned phase risks. Preserve each PLAN register, deterministic checklist identity, explicit match review, full Security risk variant, actual provider-rendered anchors and independent audit. Never default to a standalone issue for every planned risk.

For each complete/blocked SUMMARY and REVIEW artifact, call `engineer_run query phase.issue-declare "${PHASE_NUMBER}" "${ARTIFACT}"`. Reconcile its full issue_refs snapshot. Update declarations only with `--entries-file "${ENTRIES_FILE}" --expect-digest "${SNAPSHOT_DIGEST}"`. Every unresolved item needs a canonical issue URL; every resolved item needs evidence and reason. Preserve stable threat identities and avoid duplicate issues.
Planned threats use `--variant "Security risk"` and the complete canonical deterministic checklist/container policy and phase.threat-review/preview/publish schema; distinct unplanned risks use standalone issues. Do not default to one standalone issue per planned risk, and verify provider-rendered heading anchors before linking them. For an ordinary non-threat finding requiring publication, author the complete public title/body from the canonical issue template, validate its full variant and request the content-bound preview with `phase.issue-preview N ARTIFACT FINDING_ID --variant VARIANT --title TITLE --body-file PUBLIC.md`. Add exactly one reviewed `--existing-issue URL_OR_NUMBER` or `--no-match` to the preview; this disposition is hash-bound to the exact title/body/source. Review exact public content and canonical matching evidence, then publish with the same arguments, explicit `--variant VARIANT`, disposition and `--preview-token TOKEN`; issue-update uses the established linked issue. A reviewed closed match may link without reopening or closing it. Re-read provider state; do not retry a second create after an unknown result. A failed publication remains an explicit blocker, not a fabricated link. Run `engineer_run query phase.handoff "${PHASE_NUMBER}"` and require `ready: true` before verification handoff or shipping; report exact errors otherwise.
</step>
<step name="update_roadmap">
Update plan progress only for complete committed SUMMARYs with `engineer_run query roadmap.update-plan-progress "${plan_id}"`. Do not mark the phase complete before canonical verification passes.
</step>
<step name="pending_todo_reconciliation">
Keep existing Folded Todos pending through execution and verification; only shipping after merged-provider evidence may reconcile them. Do not edit todo status or create new todos from findings here.
</step>
<step name="update_state">
Run state.update-progress and state.record-session through engineer_run query, then commit the exact shared record paths with the complete execution artifacts. Only the coordinator writes these fields. Keep record-health warnings visible without inventing phase acceptance.
</step>
<step name="session_handoff">
Capture the session identity, source head, complete and blocked plan IDs, review/check evidence, issue handoff state and pending human decisions. Preserve the session for verification or for any dependent blocker; do not close it merely because implementation returned.
</step>
<step name="completion">
Use `## PHASE COMPLETE` only for actual fully completed execution coverage, not from a PLAN COMPLETE marker. Report the actual integrated results, remaining independent/dependent work, configured check outcomes or pending tests, issues and session branch/path. A partial selected wave stops with its actual remaining work and does not trigger full-phase completion.
</step>
<step name="run_verify_work">
Only when the full phase index has zero incomplete plans, PARTIAL_EXECUTION is false, and issue handoff is ready, read and execute `engineer/workflows/verify-work.md` for this same phase/session. Its passed/current result continues to authorized shipping. Honor explicit user limits on checks, publication and merging. A blocker is reported with dependent work preserved; never replace a pending check with passed or start another phase.
</step>
</process>
<failure_handling>
Fix in-scope defects through owned isolated work; put out-of-scope findings in the closing Deferred report; leave actual human decisions as blockers. Unknown causes need a debugger. A systemic all-agent failure stops the affected dispatch batch and preserves evidence.
</failure_handling>
<resumption>
An authorized `/execute-phase {phase}` resumes from actual committed summaries and runtime lifecycle state, dispatching only unfinished work. Never redispatch a completed plan solely because a terminal session ended abnormally.
</resumption>
<anti_patterns>
Do not self-execute dispatched plans, touch active worker paths, infer confirmed stop from timeout, bypass isolation/deletion guards, create todos, mark completion before verification, merge without instruction, or ask the user to type routine handoff commands. Don't look for a way to run a plan unisolated — there is no opt-out.
</anti_patterns>
<success_criteria>
Explicit phase implementation authority is recorded; every executor was isolated with exact ownership; worker commits and summaries were reconciled; merges honored deletion declarations; current checks/reviews and canonical issue handoff support the result; shared records are coordinator-owned; and ready work continued to verify-work in the same session with publication and merge limits preserved.
</success_criteria>
