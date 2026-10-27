<!-- workflow: quick; roles: planner, executor, plan-checker, verifier -->
<purpose>
Deliver one bounded outcome with a recorded plan, isolated execution, atomic commits and a runtime-owned quick record. Validate the plan and result when --validate is selected. This is not a shortcut around acceptance, ownership or merge authority.
</purpose>
<required_reading>
@~/.claude/engineer/RULES.md
@~/.claude/engineer/references/worktree-sessions.md
@~/.claude/engineer/references/worker-handoff.md
@~/.claude/engineer/references/git-workflow.md
</required_reading>
<available_agent_types>
Use planner, plan-checker, executor, verifier, code-reviewer and phase-researcher only when the bounded evidence need warrants that role.
</available_agent_types>
<model_selection>
Resolve the exact role with engineer_run query resolve-model and resolve-effort immediately before each dispatch. Pass actual values inline, omitting inherit. All source-changing workers remain isolated; the coordinator waits before integrating their paths.
</model_selection>
<scope_guardrail>
Require a single concrete outcome. A new independent capability is outside this task: record it in the required SUMMARY Deferred section, without creating a todo or expanding acceptance. A phase-sized change needs a separately scoped phase decision. A quick request authorizes implementing its named outcome; it does not authorize phase implementation or an unrelated merge.
</scope_guardrail>
Independent read-only evidence assignments may inspect the same frozen revision concurrently when their inputs do not depend on another result. Join every assigned result before accepting evidence or starting correction. Required source-changing workers remain outside a frozen batch.
<process>
<step name="parse_arguments">
Parse `list`, `status <slug>`, or `resume <slug>`, otherwise a new description. Accept only --validate and --text for implementation. Read and execute engineer/workflows/_runtime-launcher.snippet.sh, then run `engineer_run query init.quick "${DESCRIPTION}"`, adding --validate when supplied. Require initialized project records and available exact roles; role resolution failures stop dispatch. If records are missing, report `/new-project` or `/onboard` as the required setup. Apply text_mode and response_language only to rendering.
</step>
<step name="check_open_tasks">
Read `engineer_run query quick.list --status open`. List complete IDs, descriptions and statuses. List/status are read-only and return here. Resume selects the exact runtime record via quick.get; a missing or ambiguous slug is a blocker. For a new request with related open work, show the concrete existing task and allow the user to choose resume versus a genuinely new record; do not silently overwrite it or start duplicate execution.
</step>
<step name="open_session">
Inspect session.status and the selected quick record's lineage. Reuse its matching open quick session; adopt only an already named clean isolated checkout with established ownership. Otherwise run `engineer_run query session.open quick "${QUICK_LABEL}"` with the selected stable label; a new task needs a distinct label when an existing open task was not selected. Quote and enter the returned worktree, capture branch/base/path, and re-run init.quick there. A failed session operation blocks implementation, never falls back to the primary checkout.
</step>
<step name="create_task">
For new work run `engineer_run query quick.create "${DESCRIPTION}"` inside the session. Read id/quick_id, directory and record path; the runtime owns allocation, directory and QUICK.md. For resume, use quick.get and preserve its original ID/directory. Do not allocate another record merely to resume a worker.
</step>
<step name="plan">
Capture PLAN_INPUT_REVISION from the actual session HEAD. Dispatch planner with inline resolved model/effort, exact quick goal, current source paths, user constraints, runtime quick ID/path, full phase-prompt template, applicable skills and complete acceptance. Require a short task set because scope is bounded, not abbreviated task contracts: every task still needs read_first, concrete action, meaningful automated/fails_when verification, ownership, deletions, resources, threats and documentation obligations. Give the worker's actual isolation identity and handoff context. Require committed plan output with PLANNING COMPLETE/PARTIAL markers and a precise blocked return if the scope is wrong. ORCHESTRATOR RULE: wait for confirmed stop before touching or integrating the planner's owned paths.
</step>
<step name="reconcile_plan_threats">
Follow [canonical threat tracking](../references/git-workflow.md#canonical-threat-tracking) for every applicable planned or unplanned risk; use the complete procedure and preserve Pending dependencies.

Read and execute the complete _canonical-threat-tracking.md with the real quick ID and quick.threat-* route. Preserve its full Security risk schema, explicit match review, deterministic quick checklist, standalone unplanned risks, actual provider-rendered anchors and independent audit. Never fabricate a phase ID.

Read the full plan's threats and requirement/acceptance links. Preserve stable canonical threat identities and existing issue URLs; do not renumber or duplicate a threat to make a check pass. A missing mitigation or human decision blocks only dependent execution and is named in the report.
</step>
<step name="optional_plan_check">
When VALIDATE_MODE is true, read and execute engineer/workflows/quick/steps/plan-checker-loop.md. Require its canonical approved verdict and complete assigned coverage; INFO stays advisory. Do not treat a loop cap as approval.
</step>
<step name="prepare_dispatch">
Read and execute engineer/workflows/quick/steps/worktree-pre-dispatch-commit.md unconditionally. The committed plan and QUICK record must be available at the captured worker base. Read actual .gitmodules paths and compare every declared modification/deletion with submodule roots before isolation; preserve the complete copied submodule-data parse below.
```bash
if [ -f .gitmodules ]; then
  SUBMODULE_PATHS=$(python -I -c 'import json,subprocess,sys; p=subprocess.run(["git","config","--null","--file",".gitmodules","--get-regexp",r"^submodule\..*\.path$"],capture_output=True,text=True); sys.exit(p.returncode) if p.returncode not in (0,1) else None; print(json.dumps([item.split("\n",1)[1] for item in p.stdout.split("\0") if "\n" in item]))') || exit 1
else
  SUBMODULE_PATHS='[]'
fi
```
A submodule intersection or unparseable scope blocks the task for a human; never disable worktrees to bypass it.
</step>
<step name="execute">
Run quick.update with status in_progress. Resolve `engineer_run query dispatch-isolation --raw --plan "${QUICK_ID}"`; require one of the two mandatory modes. Capture EXPECTED_BASE from the session HEAD and exact plan files/deletions/resources. Use `worktree.create "${QUICK_ID}" --phase "quick-${QUICK_ID}" --base "${EXPECTED_BASE}" --files ... --deletions ...` for orchestrator-worktree. For harness-worktree, dispatch with isolation="worktree", then register actual worker branch/path through worktree.record-agent with that same phase key and exact ownership.

Build the complete executor packet with QUICK plan, AGENTS.md, applicable skills, assigned role and worker-handoff rules. Harness dispatch embeds the bound branch-check guard. Orchestrator-worktree embeds the complete supplied-root pin bound to the actual runtime-created path. Preserve the plan materialization necessary inside a harness checkout; materialize only committed assigned plan/QUICK input, not unrelated discussion/research artifacts. Resolve every template placeholder before dispatch.

Constraints: execute only the recorded planned tasks; preserve acceptance and explicit test deferral; commit meaningful owned slices atomically; write and commit `${QUICK_ID}-SUMMARY.md` before returning; include complete status, checks or pending checks, acceptance, documentation, issue_refs and Deferred findings. Do not write shared STATE or ROADMAP. A wrong plan, scope expansion, submodule boundary or failed identity guard returns blocked. Dispatch `Agent(subagent_type="executor", model=<inline resolved value>, effort=<inline resolved value>, ...)`, omitting inherit and including literal worktree isolation for harness mode.

After dispatch, wait without touching its owned paths. Confirm stop, then inspect the actual committed SUMMARY status, branch/base and owned commits. A terminal message alone does not complete the task. Merge complete owned work with `worktree.merge-wave --phase "quick-${QUICK_ID}"`; cleanup-wave runs only after current clean merge ancestry exists. Preserve failed/blocked worktrees. A rejected isolated run recovers only in a fresh narrowly scoped isolated checkout; primary-checkout execution is never a default recovery.
</step>
<step name="reconcile_summary_threats">
Follow [canonical threat tracking](../references/git-workflow.md#canonical-threat-tracking) for every applicable planned or unplanned risk; use the complete procedure and preserve Pending dependencies.

Re-run the complete kind-aware threat procedure for changed findings/evidence, preserving stable quick risk identities and the original PLAN register. Use quick.threat-audit ID before quick readiness when execution is permitted; a deferred or failed audit remains a real blocker.

Compare the complete SUMMARY threats with the approved plan and canonical tracker. Every unresolved finding needs a stable issue relationship and resolved items need evidence/reason. Reconcile publication under the complete canonical issue template and content-bound preview/readback contract. Never invent a URL or weaken the accepted mitigation to close an item.
</step>
<step name="run_checks">
Run `engineer_run query verification.run-checks` on the integrated session revision when execution is permitted. Reuse only current passing input-bound receipts. A failing/timed-out required check blocks completion and routes to isolated executor/debugger correction; rerun invalidated checks after integration. User-deferred checks remain pending and cannot support a passed report.
</step>
<step name="track_integrated_slice">
When delivery is authorized, push the exact session branch without force and run pr.open with that branch, complete canonical title/body file and intended base. It opens a draft on the first push and updates the existing PR after each meaningful integrated slice. Validate the template, canonical issue URLs and provider readback. Never publish an abbreviated body or a second PR after an uncertain result.
</step>
<step name="optional_verification">
When VALIDATE_MODE is true, read quick/steps/quick-verification.md and require its structured result. The coordinator persists the verifier's complete canonical report at `.planning/quick/NNN-slug/NNN-VERIFICATION.md`, with quick ID, status, covered_files, fingerprint, revision and explicit issue_refs. Use verification.fingerprint/current with --quick ID; do not invent a phase. A nonpass result blocks validated completion and delivery readiness.
</step>
<step name="complete_task">
Only after complete committed work and all selected required validation, run `engineer_run query quick.update "${QUICK_ID}" --status complete --commit "${INTEGRATED_COMMIT}"`, adding actual verification/issue/PR evidence through supported options. Run state.record-session with the actual result and record path. Commit exact QUICK_DIR and changed STATE with `engineer_run query commit "docs(quick-${QUICK_ID}): record task outcome" --files "${QUICK_DIR}" .planning/STATE.md`. Never hand-render a completed-task table or call pending checks complete.
</step>
<step name="deliver_session">
Publish/update the existing session draft using the full current template, inspect provider head/body and issue links, and wait for actual pr.checks results with --timeout. A quick session may become ready or merge only through its real quick verification route: `pr.ready BRANCH --quick ID` and, only with explicit merge instruction, `pr.merge BRANCH --quick ID --confirm`. Required frozen evidence, current check receipts, quick findings and independent PR issue audit must pass; no fake phase or verification bypass is permitted. If validation was not selected, do not invent a passed verifier report to satisfy merge—prepare the required independent evidence or leave the PR open.

After provider-confirmed merge, pr.sync fetches state; it does not integrate a local checkout. Close the session only from a different clean checkout whose HEAD actually contains the session HEAD, via session.close BRANCH. Preserve and report any dirty, active, unintegrated or pending-review closeout blocker. Do not force cleanup or start another task.
</step>
<step name="completion">
Report quick ID, concrete outcome, actual committed plan/SUMMARY, check and validation evidence or pending work, canonical issues, PR/merge state and remaining blockers. End with the quick record path. No unrelated capability or next-task menu is added.
</step>
</process>
<anti_patterns>
Do not bypass task scope, isolation, independent evidence, required committed SUMMARY, runtime record ownership, provider readback or explicit merge authority. Do not replace a task record with a condensed narrative or call blocked acceptance complete.
</anti_patterns>
<success_criteria>
The runtime owns the task ID/record, a committed complete planner contract guided isolated executor work, actual owned commits and SUMMARY were integrated, selected checks/verification have honest outcomes, and authorized delivery completed or preserved an explicit blocker with the session intact.
</success_criteria>
