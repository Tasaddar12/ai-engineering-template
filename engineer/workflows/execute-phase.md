<!-- workflow: native orchestrator and declared agents -->
<purpose>
Execute all plans in a phase using wave-based parallel execution. Orchestrator stays lean — delegates plan execution to subagents.
</purpose>

<core_principle>
Orchestrator coordinates, not executes. Each subagent loads the full execute-plan context. Orchestrator: discover plans → analyze deps → group waves → spawn agents → handle checkpoints → collect results.
</core_principle>

<runtime_compatibility>
**Subagent spawning is runtime-specific:**

- **Claude Code:** Uses `Agent(subagent_type="executor", ...)` — backgrounded by default; verify completion
- **Codex:** native subagent sessions can end abnormally (`turn_aborted`) after the plan
  work is already committed. Completion is decided by the step-4 artifact reconciliation
  (SUMMARY + matching recent commits), not by the session's terminal state.
- If `Agent`/`agent` tool is genuinely unavailable (e.g. a backgrounded
  Claude Code agent per ), use sequential inline execution as
  the fallback for executor parallelization only. If `Agent` IS available (top-level Claude
  Code), you MUST spawn executor agents — inline execution is not authorized. Check for
  actual tool availability, not runtime name.

**Fallback rule:** If a spawned agent completes its work (commits visible, SUMMARY.md exists) but
the orchestrator never receives the completion signal, treat it as successful based on spot-checks
and continue to the next wave/plan. Never block indefinitely waiting for a signal — always verify
via filesystem and git state.
</runtime_compatibility>

<required_reading>
Read STATE.md before any operation to load project context.
@~/.claude/engineer/references/agent-contracts.md
@~/.claude/engineer/references/context-budget.md
@~/.claude/engineer/references/gates.md
</required_reading>

<available_agent_types>
These are the valid Engineer subagent types registered in .claude/agents/ (or equivalent for your runtime).
Always use the exact name from this list — do not fall back to 'general-purpose' or other built-in types:

- executor — Executes plan tasks, commits, creates SUMMARY.md
- verifier — Verifies phase completion, checks quality gates
- planner — Creates detailed plans from phase scope
- phase-researcher — Researches technical approaches for a phase
- plan-checker — Reviews plan quality before execution
- debugger — Diagnoses and fixes issues
- codebase-mapper — Maps project structure and dependencies
- integration-checker — Checks cross-phase integration
- nyquist-auditor — Validates verification coverage
- ui-researcher — Researches UI/UX approaches
- ui-checker — Reviews UI implementation quality
- ui-auditor — Audits UI against design requirements
  </available_agent_types>

<process>


<step name="parse_args" priority="first">
Parse `$ARGUMENTS` before loading any context:

- First positional token → `PHASE_ARG`
- Optional `--wave N` → `WAVE_FILTER`
- Optional `--gaps-only` keeps its current meaning

If `--wave` is absent, preserve the current behavior of executing all incomplete waves in the phase.
</step>

<step name="initialize" priority="first">
Load all context in one call:

@~/.claude/engineer/references/run-resolver.md

```bash
IFS= read -rd '' ENGINEER_ARGS <<'ENGINEER_ARGS_END' || true
$ARGUMENTS
ENGINEER_ARGS_END
ENGINEER_ARGS=${ENGINEER_ARGS%$'\n'}
WAVE_PARAM=""; if [[ "$ENGINEER_ARGS" =~ (^|[[:space:]])--wave[[:space:]]+([^[:space:]-][^[:space:]]*) ]]; then WAVE_PARAM="--wave ${BASH_REMATCH[2]}"; fi
INIT=$(engineer_run query init.execute-phase  "${PHASE_ARG}" $WAVE_PARAM)
AGENT_SKILLS=$(engineer_run query agent-skills executor )
```

Parse JSON for: `executor_model`, `verifier_model`, `commit_docs`, `parallelization`, `branching_strategy`, `branch_name`, `phase_found`, `phase_dir`, `phase_number`, `padded_phase`, `phase_name`, `phase_slug`, `plans`, `incomplete_plans`, `plan_count`, `incomplete_count`, `state_exists`, `roadmap_exists`, `phase_req_ids`, `response_language`, `requirements_path`, `section_manifest`, `threat_id_duplicate_count`.

**Threat-ID gate:** if `threat_id_duplicate_count` is non-zero, read and execute `execute-phase/steps/threat-id-gate.md` BEFORE any dispatch — it is a hard stop (the full duplicate list is in `threat_id_duplicates`).

`section_manifest` gates the three `steps/*.md` reads below: read a step file only when its `id` is in `section_manifest.included` (equivalently, its path is in `section_manifest.read`); skip it — without reading — when its `id` is in `section_manifest.excluded`. When `section_manifest` is `null` (degraded: manifest artifact missing/unreadable), read all three unconditionally — the safe superset.

**Model resolution:** If `executor_model` is `"inherit"`, omit the `model=` parameter from all `Agent()` calls — do NOT pass `model="inherit"` to Agent. Omitting the `model=` parameter causes Claude Code to inherit the orchestrator model automatically. Only set `model=` when `executor_model` is an explicit model name (e.g., `"claude-sonnet-5"`, `"claude-opus-4-8"`).

@~/.claude/engineer/references/execute-phase-response-language.md

Reset the wave-failure tally. Fenced `bash` blocks are separate shells, so the post-merge gate's cumulative count reaches step 5.8 through a handoff file; a previous run's tally must not leak in:

```bash
# engineer-handoff:begin wave-failure-reset
_ENGINEER_HANDOFF="$( { git rev-parse --absolute-git-dir 2>/dev/null || echo "${TMPDIR:-/tmp}/engineer-$(pwd | cksum | cut -d' ' -f1)"; } )/handoff"; mkdir -p "$_ENGINEER_HANDOFF"
: > "$_ENGINEER_HANDOFF/wave-failures"
# engineer-handoff:end wave-failure-reset
```


Read context window size for adaptive prompt enrichment:

```bash
CONTEXT_WINDOW=$(engineer_run query config-get context_window --raw 2>/dev/null || echo "200000")
```

When `CONTEXT_WINDOW >= 500000` (1M-class models), subagent prompts include richer context:

- Executor agents receive prior wave SUMMARY.md files and the phase CONTEXT.md/RESEARCH.md
- Verifier agents receive all PLAN.md, SUMMARY.md, CONTEXT.md files plus REQUIREMENTS.md
- This enables cross-phase awareness and history-aware verification

When `CONTEXT_WINDOW < 200000` (sub-200K models), subagent prompts are thinned to reduce static overhead:

- Executor agents omit extended deviation rule examples and checkpoint examples from inline prompt — load on-demand via @~/.claude/engineer/references/executor-examples.md
- Planner agents omit extended anti-pattern lists and specificity examples from inline prompt — load on-demand via @~/.claude/engineer/references/planner-antipatterns.md
- Core rules and decision logic remain inline; only verbose examples and edge-case lists are extracted
- This reduces executor static overhead by ~40% while preserving behavioral correctness

**If `phase_found` is false:** Error — phase directory not found.
**If `plan_count` is 0:** Error — no plans found in phase.
**If `state_exists` is false but `.planning/` exists:** Offer reconstruct or continue.

When `parallelization` is false, plans within a wave execute sequentially.



Read `workflow.tdd_mode` directly and retain native TDD execution guidance. Read `executor.stall_detect_interval_minutes` and `executor.stall_threshold_minutes` for the existing progress policy. Before any executor dispatch, read and execute the mandatory isolation resolver in `execute-phase/steps/executor-isolation-dispatch.md`; unavailable isolation is a hard stop.
</step>

<step name="safe_resume_gate">
Before trusting `STATE.md` or dispatching any executor, derive `CURRENT_PLAN_ID`
from the active incomplete plan in `INIT`, then search recent history:
```bash
SUMMARY_PATH="{phase_dir}/{plan_padded}-SUMMARY.md"
# The plan's commits come from the evaluation-scope resolver: anchored
# on the commit SUBJECT, zero-pad tolerant and tolerant of a decimal / N-segment /
# letter-suffixed phase number, reachable from THIS branch only, bounded to
# the latest reachable tag (milestone marker). One `<sha> <subject>` line per commit, newest first.
PHASE_NUMBER="{phase_number}"
PLAN_COMMITS=$(engineer_run check evaluation-scope --plan "${PHASE_NUMBER}-{plan_padded}" --commits-only --milestone-bound --max-commits 30 --raw 2>/dev/null) && PLAN_SCOPE_RC=0 || PLAN_SCOPE_RC=$?
# Exit 69 (UNAVAILABLE) = "could not look": empty is then NOT "no commits". Fail closed.
if [ "$PLAN_SCOPE_RC" -ne 0 ]; then echo "SAFE-RESUME GATE: could not resolve the plan's commits (evaluation-scope exit ${PLAN_SCOPE_RC}); not dispatching an executor on an unknown resume state." >&2; exit 1; fi
PLAN_COMMITS=$(printf '%s' "$PLAN_COMMITS" | engineer_run query json.commits --raw)
```
If production commits exist and `SUMMARY.md is missing` (no `.planning/async-jobs/*.json` manifest matches it: a match is a legal `external_job_waiting` deferral - reconcile per `docs/reference/planning-artifacts.md`, never re-dispatch), stop before spawning a
new executor; continuing risks duplicate work and stale `STATE.md`/ROADMAP progress.
Offer these recovery options:
- `close out manually` — inspect commits, write SUMMARY.md, then update STATE/ROADMAP.
- `re-execute from scratch` — revert or supersede partial commits before dispatch.
- `mark-and-skip` — record the anomaly and move on only with explicit confirmation.
</step>

**TDD gate.** Task-scoped enforcement runs inside plan execution (immediately before each implementation step), where `TASK_FILE`, `PLAN_ID`, and `TASK_ID` are defined. Keep the same predicate and RED-commit contract:

```bash
if [ "$TDD_MODE" = "true" ]; then
  IS_BEHAVIOR_ADDING=$(engineer_run query task.is-behavior-adding "$TASK_FILE" --pick is_behavior_adding)
  if [ "$IS_BEHAVIOR_ADDING" = "true" ]; then
    # The same resolver, scope and milestone bound as safe_resume_gate — anchored,
    # zero-pad tolerant, this branch only. A padded literal grep
    # hard-halted on a correct unpadded RED commit.
    # This pathspec IS the gate's definition of "a test file". It was
    # JS/TS-only, so Go tripped on every task; and `**/` never matches a
    # root-level path, so a root `foo.test.js` was invisible too. Bare globs
    # match at every depth. NOT widened to ordinary source — that would make
    # the gate pass on any in-scope commit. Trade-offs and the Rust gap:
    # references/tdd.md § Create first test file.

    RED_COMMIT=$(engineer_run check evaluation-scope --plan "${PHASE_NUMBER}-${PLAN_ID}" --commits-only --milestone-bound --max-commits 1 --raw --pathspec "*.test.*" --pathspec "*.spec.*" --pathspec "tests/" --pathspec "__tests__/" --pathspec "*_test.go" --pathspec "test_*.py" --pathspec "*_test.py" --pathspec "*_test.exs" --pathspec "*_spec.rb" --pathspec "*_test.rb" 2>/dev/null) && RED_SCOPE_RC=0 || RED_SCOPE_RC=$?
    # Exit 69 (UNAVAILABLE) = the scope could not be resolved: that is not "missing RED commit".
    if [ "$RED_SCOPE_RC" -ne 0 ]; then echo "TDD GATE UNAVAILABLE: could not resolve the plan's commits for ${PLAN_ID}/${TASK_ID} (evaluation-scope exit ${RED_SCOPE_RC})"; exit 1; fi
    RED_COMMIT=$(printf '%s' "$RED_COMMIT" | engineer_run query json.commits --first --raw)
    if [ -z "$RED_COMMIT" ]; then
      engineer_run query state.update last_gate_trip "${PLAN_ID}/${TASK_ID}" || true
      echo "TDD GATE TRIPPED: missing RED commit for ${PLAN_ID}/${TASK_ID}"
      exit 1
    fi
  fi
fi
```

Pure doc-only / config-only / test-only tasks return `is_behavior_adding=false` and are exempt. When the gate trips, Read `engineer/references/tdd.md` for the exact halt report format.
</step>

<step name="check_blocking_antipatterns" priority="first">
**MANDATORY — Check for blocking anti-patterns before any other work.**

Look for a `.continue-here.md` in the current phase directory:

```bash
ls ${phase_dir}/.continue-here.md 2>/dev/null || true
```

If `.continue-here.md` exists, parse its "Critical Anti-Patterns" table for rows with `severity` = `blocking`.

**If one or more `blocking` anti-patterns are found:**

This step cannot be skipped. Before proceeding to `check_interactive_mode` or any other step, the agent must demonstrate understanding of each blocking anti-pattern by answering all three questions for each one:

1. **What is this anti-pattern?** — Describe it in your own words, not by quoting the handoff.
2. **How did it manifest?** — Explain the specific failure that caused it to be recorded.
3. **What structural mechanism (not acknowledgment) prevents it?** — Name the concrete step, checklist item, or enforcement mechanism that stops recurrence.

Write these answers inline before continuing. If a blocking anti-pattern cannot be answered from the context in `.continue-here.md`, stop and ask the user for clarification.

**If no `.continue-here.md` exists, or no `blocking` rows are found:** Proceed directly to `handle_branching`.
</step>


<step name="handle_branching">
Check `branching_strategy` from init:

**"none":** Read and execute `execute-phase/steps/protected-branch.md`.

**"phase" or "milestone":** Use pre-computed `branch_name` from init.

Fork the new phase branch off `origin/HEAD` (the project's default branch), not the current HEAD — otherwise consecutive phases compound and stay unpushed. If `$BRANCH_NAME` already exists locally, reuse it as-is.

```bash
DEFAULT_BRANCH=$(engineer_run query git.base-branch 2>/dev/null \
  || git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||' \
  || echo main)

if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
  git switch "$BRANCH_NAME" || { echo "ERROR: Could not switch to existing branch '$BRANCH_NAME'." >&2; exit 1; }
else
  if ! git fetch --quiet origin "$DEFAULT_BRANCH"; then
    git show-ref --verify --quiet "refs/remotes/origin/$DEFAULT_BRANCH" \
      || { echo "ERROR: fetch origin/$DEFAULT_BRANCH failed and no local copy exists. Refusing to create '$BRANCH_NAME' off current HEAD." >&2; exit 1; }
    echo "WARNING: fetch origin/$DEFAULT_BRANCH failed; using local copy as base." >&2
  fi
  if [ -n "$(git status --porcelain)" ]; then
    echo "WARNING: Uncommitted changes will be carried onto '$BRANCH_NAME' (branched off origin/$DEFAULT_BRANCH, not previous HEAD)."
  else
    git switch --quiet "$DEFAULT_BRANCH" 2>/dev/null && git merge --ff-only --quiet "origin/$DEFAULT_BRANCH" 2>/dev/null || true
  fi
  # Pinned base; --no-track; warn if local ahead of origin.
  AHEAD=$(git rev-list --count "origin/$DEFAULT_BRANCH..$DEFAULT_BRANCH" 2>/dev/null || echo 0)
  [ "$AHEAD" != "0" ] && [ -n "$AHEAD" ] && echo "WARNING: $DEFAULT_BRANCH is $AHEAD ahead of origin — '$BRANCH_NAME' won't include those commits." >&2
  git checkout -b "$BRANCH_NAME" "origin/$DEFAULT_BRANCH" --no-track \
    || { echo "ERROR: Could not create '$BRANCH_NAME' from origin/$DEFAULT_BRANCH." >&2; exit 1; }
fi
```

All subsequent commits go to this branch. User handles merging.
</step>

<step name="validate_phase">
From init JSON: `phase_dir`, `plan_count`, `incomplete_count`.

Report: "Found {plan_count} plans in {phase_dir} ({incomplete_count} incomplete)"

**Update STATE.md for phase start:**

```bash
engineer_run query state.begin-phase --phase "${PHASE_NUMBER}" --name "${PHASE_NAME}" --plans "${PLAN_COUNT}"
```

This updates Status, Last Activity, Current focus, Current Position, and plan counts in STATE.md so frontmatter and body text reflect the active phase immediately.
</step>

<step name="discover_and_group_plans">
Load plan inventory with wave grouping in one call:

```bash
PLAN_INDEX=$(engineer_run query phase-plan-index "${PHASE_NUMBER}")
```

Parse JSON for: `phase`, `plans[]`, `waves`, `incomplete`, `runnable`, `ready_plans`, `has_checkpoints` — full per-plan fields and the readiness rules: read and follow `execute-phase/steps/ready-wave-gate.md`.

**Filtering:** Skip plans where `has_summary: true`. Additionally skip any plan whose `blocked_by` array is non-empty — it depends, directly or transitively, on a plan that halted at a designed stop rather than completing — and report it by name: "Skipping {plan.id}: blocked by halted {blocked_by.join(', ')}". Never silently drop a blocked plan from the report; it must appear by name with its reason, not merely vanish from the executable list. This rule is additive to the `has_summary` skip, not a replacement for it. Additionally skip any incomplete plan with `ready: false` (see `execute-phase/steps/ready-wave-gate.md`; never dispatch a not-ready plan). If `--gaps-only`: also skip plans whose `gap_closure` is not `true` — but first confirm every plan object carries a `gap_closure` key. If any lacks it, the index cannot answer the filter (an older engineer_run): STOP and report "--gaps-only cannot read gap_closure from phase-plan-index — refusing to report an empty selection" rather than filtering. A key the index never emitted must not surface as "No matching incomplete plans". If `WAVE_FILTER` is set: also skip plans whose `wave` does not equal `WAVE_FILTER`.

**Wave safety check:** If `WAVE_FILTER` is set and there are still incomplete plans in any lower wave that match the current execution mode, STOP and tell the user to finish earlier waves first. Do not let Wave 2+ execute while prerequisite earlier-wave plans remain incomplete.

**If all filtered — do NOT exit unconditionally.** "No plan work left" and "phase fully
done" are different conditions: a run can be interrupted between the final wave's SUMMARY and
`verify_phase_goal` (most commonly by a checkpoint plan that is retired but still writes a SUMMARY),
leaving a phase that looks complete from every index yet never produced `*-VERIFICATION.md`. A
third condition looks identical to the first two by plan_count alone but is neither: some filtered
plans were filtered because they are **blocked** (non-empty `blocked_by`), not because they
are done. Blocked-and-incomplete must never be reported as finished.

```bash
# The owner's answer — `status` and the bare command it routes to. A non-zero exit
# (an out-of-set report status) is a hard error: surface it, never read it as "no status".
VERIFY_STATUS=$(engineer_run query verification status "${PHASE_DIR}" --pick status) || { echo "verification status failed — see the error above" >&2; exit 1; }
VERIFY_ROUTE=$(engineer_run query verification status "${PHASE_DIR}" --pick route) || { echo "verification status failed — see the error above" >&2; exit 1; }
# Checkbox = marked-complete; report fields can claim a no-op write.
ANALYZE=$(engineer_run query roadmap.analyze)
PHASE_MARKED=$(echo "$ANALYZE"|jq -r --arg p "$PHASE_NUMBER" 'def n:sub("^0+(?=[0-9])";"");.phases[]|select(((.number//.phase_number|tostring|n))==($p|n))|.roadmap_complete'|head -1)
```

Evaluate in this exact order — the first matching condition decides the outcome; do not evaluate
later conditions once one matches:

1. **A filter is active** (`--gaps-only`, or `WAVE_FILTER` set): report "No matching incomplete
   plans" → exit, unchanged. A filtered run finding nothing left in ITS slice says nothing about
   whether the phase as a whole is done, and must never jump to verification.
2. **No filter is active, and at least one filtered plan was skipped because of a non-empty
   `blocked_by`** (irrespective of `VERIFY_STATUS`): the phase is NOT finished — it is **stuck on a
   halt**. A plan with no SUMMARY and no dispatched work must never be treated as done merely
   because nothing was left to filter. Report:
   `"Phase stuck: {blocked plan ids} blocked by halted {their blocked_by ids} — resolve the halt, do not resume verification."`
   → exit. Do not fall through to condition 3; this is not a completion state.
   2b. **No filter is active, no blocked-plan skip occurred, and at least one filtered plan was skipped because `ready: false` ** — the phase is WAITING on incomplete predecessors, not finished: report it by name and exit before any completion state (`execute-phase/steps/ready-wave-gate.md`).
3. **No filter is active, and every filtered plan was filtered by `has_summary` alone** (no
   blocked-plan skip occurred) — branch on the owner's answer, never on a status word:
   - **`VERIFY_ROUTE == execute-phase`** — the owner routes here when the verify step never ran
     (`VERIFY_STATUS == missing`) and when covered source changed after the verifier ran,
     on both sides of `PHASE_MARKED`. Report `$VERIFY_STATUS` with:
     `"All {plan_count} plans are summarized but no VERIFICATION.md exists — resuming at the phase gates ."`
     (or, for a stale report, "…verification is stale — resuming at the phase gates to re-run the verifier.")
     Skip wave execution and continue directly at `aggregate_results`, NOT `code_review_gate`. `aggregate_results`
     reads exclusively from on-disk `${PHASE_DIR}` artifacts (`*-SUMMARY.md`) and independent
     `engineer_run` calls — nothing it reads is produced only by `execute_waves` or `checkpoint_handling` —
     so it tolerates having executed no plans in this run; the `SECURITY_FILE` / secure-phase
     threats-open gate is the shared verification step's first step, and it reads on-disk artifacts
     only too. From there the run proceeds exactly as a normal one: `aggregate_results` →
     `verify_phase_goal` (the shared verification step: `verify_post_security_gate` →
     `code_review_gate` → `close_parent_artifacts` → `regression_gate` → verifier) →
     `update_roadmap`. Never skip `aggregate_results`, `code_review_gate` or `regression_gate` on
     this path — the manual workaround this replaces skipped all three, and that gap is the reason
     this route exists rather than telling users to spawn the verifier by hand.
   - **`VERIFY_STATUS == passed` + `PHASE_MARKED` is `true`**: genuinely finished.
     Report "No matching incomplete plans" → exit, unchanged.
   - **`VERIFY_STATUS == passed` + `PHASE_MARKED` not `true`** — the run died between
     `verify_phase_goal` and `update_roadmap`: verification EXISTS — do not redo
     it or the gates already run. Report `"Phase {X} is verified but never marked
complete — resuming at update_roadmap."` and continue directly at
     `update_roadmap`; the tail steps then run in their normal order. This is the ONLY arm that
     reaches `update_roadmap`.
   - **Anything else** (`gaps_found`, `human_needed`, `unparseable`, `phase_dir_not_found`):
     present the owner's `next_action` and `next_command` (`engineer_run query verification status
"${PHASE_DIR}" --pick next_action` / `--pick next_command`) → exit. Never `update_roadmap`.

Report:

```
## Execution Plan

**Phase {X}: {Name}** — {total_plans} matching plans across {wave_count} wave(s)

{If WAVE_FILTER is set: `Wave filter active: executing only Wave {WAVE_FILTER}`.}

| Wave | Plans | What it builds |
|------|-------|----------------|
| 1 | 01-01, 01-02 | {from plan objectives, 3-8 words} |
| 2 | 01-03 | ... |
```

</step>


<step name="execute_waves">
Before dispatch, ensure each worker receives its complete required reading and owned scope. At context limits, preserve an explicit handoff with actual commits, artifacts, blockers and next action; the coordinator continues only after confirmed worker stop.
Execute each selected wave in sequence. Within a wave: parallel if `PARALLELIZATION=true`, sequential if `false`.

**Orchestrator cwd-drift guard (FIRST ACTION at execute_waves entry):**

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
# engineer:guard=orchestrator-cwd-drift
ORCHESTRATOR_WT=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "FATAL: execute_waves entry is not inside a git worktree." >&2; exit 1; }
ORCH_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
if printf '%s' "$ORCH_BRANCH" | grep -Eq '^((worktree-)?agent-|worktree-wf_)'; then
  echo "FATAL: orchestrator cwd is inside an agent worktree (branch '$ORCH_BRANCH', root '$ORCHESTRATOR_WT') — refusing to execute waves. A prior isolation=\"worktree\" dispatch drifted the cwd; re-run from the orchestrator's own worktree." >&2
  # handoff: the refusal above is correct, but on its own it is a dead end —
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
  echo "── Handoff: what is in this worktree  ──" >&2
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
# (see the cleanup guard). Treat $ORCHESTRATOR_WT as the canonical root for the
# rest of the phase — prefer `git -C "$ORCHESTRATOR_WT"` for cross-step git calls,
# since a bare `cd` does not persist across separate tool invocations.
export ORCHESTRATOR_WT
cd "$ORCHESTRATOR_WT" || { echo "FATAL: cannot cd to orchestrator worktree '$ORCHESTRATOR_WT'." >&2; exit 1; }
```

**Stream-idle-timeout prevention — checkpoint heartbeats:**

Multi-plan phases can accumulate enough subagent context that the Claude API
SSE layer terminates with `Stream idle timeout - partial response received`
between a large tool_result and the next assistant turn (seen on Claude Code

- Opus 4.7 at ~200K+ cache_read). To keep the stream warm, emit short
  assistant-text heartbeats — **no tool call, just a literal line** — at every
  wave and plan boundary. Each heartbeat MUST start with `[checkpoint]` so
  tooling and `/manager`'s background-completion handler can grep partial
  transcripts. `{P}/{Q}` is the phase-wide completed/total plans counter and
  increases monotonically across waves. `{status}` is `complete` (success),
  `failed` (executor error), or `checkpoint` (human-gate returned).

```
[checkpoint] phase {PHASE_NUMBER} wave {N}/{M} starting, {wave_plan_count} plan(s), {P}/{Q} plans done
[checkpoint] phase {PHASE_NUMBER} wave {N}/{M} plan {plan_id} starting ({P}/{Q} plans done)
[checkpoint] phase {PHASE_NUMBER} wave {N}/{M} plan {plan_id} {status} ({P}/{Q} plans done)
[checkpoint] phase {PHASE_NUMBER} wave {N}/{M} complete, {P}/{Q} plans done ({wave_success}/{wave_plan_count} ok)
```

**For each wave:**

@~/.claude/engineer/references/execute-phase-wave-guard.md



1. **Intra-wave files_modified overlap check (BEFORE spawning):**

   Before spawning any agents for this wave, inspect the `files_modified` list of all plans
   in the wave. Check every pair of plans in the wave — if any two plans share even one file
   in their `files_modified` lists, those plans have an implicit dependency and MUST NOT run
   in parallel.

   **Detection algorithm (pseudocode):**

   ```
   seen_files = {}
   overlapping_plans = []
   for each plan in wave_plans:
     for each file in plan.files_modified:
       if file in seen_files:
         overlapping_plans.add(plan, seen_files[file])  # both plans overlap on this file
       else:
         seen_files[file] = plan
   ```

   **If overlap is detected:**
   - Warn the user:
     ```
     ⚠ Intra-wave files_modified overlap detected in Wave {N}:
       Plan {A} and Plan {B} both modify {file}
       Running these plans sequentially to avoid parallel worktree conflicts.
     ```
   - Override `PARALLELIZATION` to `false` for this wave only — run all plans in the wave
     sequentially regardless of the global parallelization setting.
   - This is a safety net for plans that were incorrectly assigned to the same wave.
     The planner should have caught this; flag it as a planning defect so the user can
     replan the phase if desired.

   **If no overlap:** proceed normally (parallel if `PARALLELIZATION=true`).

2. **Describe what's being built (BEFORE spawning):**

   **First, emit the wave-start checkpoint heartbeat as a literal assistant-text
   line — no tool call. Do NOT skip this even for single-plan waves; it
   is required before any further reasoning or spawning:**

   ```
   [checkpoint] phase {PHASE_NUMBER} wave {N}/{M} starting, {wave_plan_count} plan(s), {P}/{Q} plans done
   ```

   Then read each plan's `<objective>`. Extract what's being built and why.

   ```
   ---
   ## Wave {N}

   **{Plan ID}: {Plan Name}**
   {2-3 sentences: what this builds, technical approach, why it matters}

   Spawning {count} agent(s)... (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)
   ---
   ```

   - Bad: "Executing terrain generation plan"
   - Good: "Procedural terrain generator using Perlin noise — creates height maps and biome zones. Required before vehicle physics."

2.5. **Per-plan worktree decision (run for each plan in this wave BEFORE any dispatch):**

Read and execute `engineer/workflows/execute-phase/steps/per-plan-worktree-gate.md` for each plan. Retain declared files/deletions; submodule intersections block dispatch.

3. **Spawn executor agents:**

   **Emit a plan-start heartbeat (literal line, no tool call) immediately before
   each `Agent()` dispatch:**

   `[checkpoint] phase {PHASE_NUMBER} wave {N}/{M} plan {plan_id} starting ({P}/{Q} plans done)`

   Pass paths only — executors read files themselves.

   **Substitute `{plan_id}` in the prompt below with this plan's `id` field** from the `phase-plan-index` JSON loaded in step 1 (the same field referred to elsewhere in this workflow as `plan.id`) — unmodified and un-truncated, never a paraphrase. The guard hooks compare this value verbatim against the sentinel the per-plan gate wrote (`per-plan-worktree-gate.md`'s `plan_id`); a paraphrase or an omission costs the dispatch its recorded isolation decision.

   Resolve mandatory isolation for this plan immediately before native agent dispatch.

   **Executor routing.** Per plan, run `engineer/workflows/execute-phase/steps/per-plan-executor-routing.md` to set `EXECUTOR_TYPE` for `subagent_type="{EXECUTOR_TYPE}"` below.

   **TDD-applicability resolution.** Run `engineer/workflows/execute-phase/steps/tdd-applicability-resolution.md`.

   **Isolated native agent dispatch:**

   Before spawning, capture the current HEAD:

   ```bash
   EXPECTED_BASE=$(git rev-parse HEAD)
   DISPATCH_TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
   EXPECTED_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [ -z "${WAVE_WORKTREE_MANIFEST:-}" ]; then
     M=$(mktemp "${TMPDIR:-/tmp}/engineer-worktree-wave-XXXXXX") && mv "$M" "$M.json" && WAVE_WORKTREE_MANIFEST="$M.json" || exit 1  # XXXXXX must be path-final on BSD/macOS
     # Persist the dispatch-time orchestrator worktree root so wave-cleanup can pin back to the
     # orchestrator's OWN worktree — NOT `git worktree list`'s first entry (always the main
     # checkout), which pins a non-primary (per-phase lane) orchestrator off its branch.
     # Dispatch runs from the orchestrator's lane, so show-toplevel here is the correct root.
     ORCH_ROOT=$(git rev-parse --show-toplevel)
     ORCH_ROOT="$ORCH_ROOT" MANIFEST="$WAVE_WORKTREE_MANIFEST" python -c 'import json,os,pathlib; pathlib.Path(os.environ["MANIFEST"]).write_text(json.dumps({"orchestrator_root":os.environ.get("ORCH_ROOT") or None,"worktrees":[]})+"\n",encoding="utf-8")'
     export WAVE_WORKTREE_MANIFEST
   fi
   ```

   **Isolation model.** The block below is the **`harness-worktree`** path. For `orchestrator-worktree` use the dispatch below it; unavailable isolation stops dispatch. Both supported modes are detailed in `execute-phase/steps/executor-isolation-dispatch.md`.

   **Sequential dispatch for parallel execution (waves with 2+ agents):**
   Dispatch each `Agent()` call **one at a time with `run_in_background: true`**. Do NOT
   send all Agent calls in a single message: simultaneous `git worktree add` calls race
   on `.git/config.lock`. Agents still run in parallel once their worktrees are created.

   ```text
   # CORRECT: one Agent() per message with run_in_background: true
   # WRONG: multiple Agent() calls in one message -> .git/config.lock contention
   ```

   ```text
   Agent(
    subagent_type="{EXECUTOR_TYPE}",
    description="Execute plan {plan_number} of phase {phase_number}",
     # Only include model= when executor_model is an explicit model name.
     # When executor_model is "inherit", omit this parameter entirely so
     # Claude Code inherits the orchestrator model automatically.
     model="{executor_model}",  # omit this line when executor_model == "inherit"
     # The host's OWN declared isolation flag (`harnessFlag` from
     # `dispatch-isolation --json`; see the isolation-dispatch fragment).
     # Emit the declared token — do NOT hardcode a runtime's flag.
     {harnessFlag},
     prompt="
       <objective>
       Execute plan {plan_number} of phase {phase_number}-{phase_name}.
       [engineer:dispatch phase="{phase_number}" plan="{plan_id}"]
       Commit each task atomically. Create SUMMARY.md.
       Do NOT update STATE.md or ROADMAP.md — the orchestrator owns those writes after all worktree agents in the wave complete.
       </objective>

       <worktree_branch_check>
       ORCHESTRATOR build-time embed (NOT a sub-agent runtime step): before this dispatch, read `engineer/references/worktree-branch-check.md`, substitute `{EXPECTED_BASE}` with the base SHA captured above ({EXPECTED_BASE}), and replace this note with that fragment's `<worktree_branch_check>` block so the dispatched prompt carries the runnable guard verbatim — do not pass this instruction through in its place.
       Per-commit HEAD/cwd-drift/path-guard: `agents/executor.md` steps 0/0a/0b + `engineer/references/worktree-path-safety.md` (in <execution_context>).
       </worktree_branch_check>

       <parallel_execution>
       You are running as a PARALLEL executor agent in a git worktree. Worktree path safety (cwd-drift, absolute-path guards) is in `worktree-path-safety.md` (loaded below).
       Run `git commit` normally with hooks; never bypass them.

       IMPORTANT: Do NOT modify STATE.md or ROADMAP.md. the native executor
       follows this explicit shared-record prohibition. The orchestrator updates them centrally
       after merge.

       REQUIRED: SUMMARY.md MUST be committed before you return. In worktree mode the
       git_commit_metadata step in the native executor method commits SUMMARY.md and REQUIREMENTS.md
       only (STATE.md and ROADMAP.md are excluded automatically). Do NOT skip or defer
       this commit — the orchestrator integrates only committed output; incomplete worktrees are preserved for diagnosis.
       REQUIRED ORDER: Write SUMMARY.md → commit → only then any narration. No text between Write and commit (truncation risk;  rescue is not primary defense).

       </parallel_execution>

       <execution_context>
       ORCHESTRATOR build-time embed (NOT a sub-agent runtime step): before this dispatch, read each file listed below and replace this note with those files' contents, inlined verbatim in this block in the listed order. Never leave `@`-include lines in the dispatched prompt — `@path` never expands inside an Agent() `prompt="..."` string , so an include arrives as literal text the executor never sees.
       - `agents/executor.md`
       - `engineer/templates/summary.md`
       - `engineer/references/checkpoints.md`
       ${TDD_APPLICABLE ? '- `engineer/references/tdd.md`' : ''}  # Type: tdd, tdd="true", or workflow.tdd_mode
       - `engineer/references/worktree-path-safety.md`
       ${CONTEXT_WINDOW < 200000 ? '' : '- `engineer/references/executor-examples.md`'}
       </execution_context>

       <required_reading>
       Read these files at execution start using the Read tool.
       First resolve repo root so every path is anchored:
       \`PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)\`
       - ${PROJECT_ROOT}/{phase_dir}/{plan_file} (Plan)
       - ${PROJECT_ROOT}/.planning/PROJECT.md (Project context — core value, requirements, evolution rules)
       - ${PROJECT_ROOT}/.planning/STATE.md (State)
       - ${PROJECT_ROOT}/.planning/config.json (Config, if exists)
       ${CONTEXT_WINDOW >= 500000 ? `
       - ${PROJECT_ROOT}/${phase_dir}/*-CONTEXT.md (User decisions from discuss-phase — honors locked choices)
       - ${PROJECT_ROOT}/${phase_dir}/*-RESEARCH.md (Technical research — pitfalls and patterns to follow)
       - ${PROJECT_ROOT}/${prior_wave_summaries} (SUMMARY.md files from earlier waves in this phase — what was already built)
       ` : ''}
       - ${PROJECT_ROOT}/CLAUDE.md (Project instructions, if exists — follow project-specific guidelines and coding conventions)
       - ${PROJECT_ROOT}/.claude/skills/ or ${PROJECT_ROOT}/.agents/skills/ (Project skills, if either exists — list skills, read SKILL.md for each, follow relevant rules during implementation)
       </required_reading>

       ${AGENT_SKILLS}

       <mcp_tools>
       If CLAUDE.md or project instructions reference MCP tools (e.g. jCodeMunch, context7,
       or other MCP servers), prefer those tools over Grep/Glob for code navigation when available.
       MCP tools often save significant tokens by providing structured code indexes.
       Check tool availability first — if MCP tools are not accessible, fall back to Grep/Glob.
       </mcp_tools>

       <success_criteria>
       - [ ] All tasks executed
       - [ ] Each task committed individually
       - [ ] SUMMARY.md created in plan directory
       - [ ] No modifications to shared orchestrator artifacts (the orchestrator handles all post-wave shared-file writes)
       </success_criteria>
     "
   )
   ```

   The selected `plan_json` is the exact current `phase-plan-index` entry. Its `id` is the full PLAN filename stem (for example `01-02`), not the bare frontmatter plan number; use that same identity for checkout ownership, committed SUMMARY and terminal receipt.

   For the harness path, bind the common receipt inputs from this plan's captured scope and actual host checkout metadata before running the terminal receipt procedure:

   ```bash
   : "${HOST_WORKTREE_PATH:?Read the checkout path from native host metadata}"
   WORKTREE_PATH="$HOST_WORKTREE_PATH"
   WORKTREE_BRANCH=$(git -C "$WORKTREE_PATH" branch --show-current) || exit $?
   ALLOWED_BASES_JSON=$(EXPECTED_BASE="$EXPECTED_BASE" node -e 'process.stdout.write(JSON.stringify([process.env.EXPECTED_BASE]))') || exit $?
   PLAN_FILES_JSON=$(printf '%s' "$plan_json" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{const v=JSON.parse(s).files_modified;if(!Array.isArray(v))process.exit(1);process.stdout.write(JSON.stringify(v))})') || exit $?
   PLAN_DELETIONS_JSON=$(printf '%s' "$plan_json" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{const v=JSON.parse(s).files_deleted||[];if(!Array.isArray(v))process.exit(1);process.stdout.write(JSON.stringify(v))})') || exit $?
   PHASE_DIR_REL=$(git -C "$phase_dir" rev-parse --show-prefix) || exit $?
   plan_id=$(engineer_run query json.get --payload "$plan_json" --field id --raw) || exit $?
   SUMMARY_PATH="${PHASE_DIR_REL%/}/${plan_id}-SUMMARY.md"
   ```

   Capture the actual native host agent id from dispatch, and obtain its terminal event through the host wait/status tool. For both isolation modes, run the **Native terminal receipt** procedure in `execute-phase/steps/executor-isolation-dispatch.md` before integration. Use the host-reported checkout path for harness workers and the runtime-returned path for precreated workers; validate branch/head with Git. Reuse this plan's captured base, allowed bases, exact files/deletions, SUMMARY path and `WAVE_WORKTREE_MANIFEST`. Never prefer executor-asserted metadata over the host result. A receipt/record failure preserves the checkout and blocks its merge; no broad worktree discovery or invented stop assertion.

   > **Worktree recovery policy:** See `execute-phase/steps/worktree-recovery-policy.md` — FAIL-CLOSED rule for base/HEAD-namespace mismatches AND isolated-run fail-safe recovery.

   > **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above to spawn executor agent(s), stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available. While waiting, run the step-4 completion surveillance; if the child's session ends abnormally — including `turn_aborted` — reconcile artifacts per `execute-phase/steps/completion-reconciliation.md` before classifying the plan.

   **Orchestrator-managed worktree dispatch** (`ISOLATION=orchestrator-worktree`): read and execute `execute-phase/steps/executor-isolation-dispatch.md`. Engineer creates each worktree (`worktree create`) and spawns the executor into it; the orchestrator performs every git operation. Merge-back and cleanup are the existing manifest-scoped gauntlet, unchanged.


4. **Wait for all agents in wave to complete.**

   **Plan-complete heartbeat:** as each executor returns (or is verified
   via spot-check below), emit one line — `complete` advances `{P}`, `failed`
   and `checkpoint` do not but still warm the stream:

   ```
   [checkpoint] phase {PHASE_NUMBER} wave {N}/{M} plan {plan_id} complete ({P}/{Q} plans done)
   [checkpoint] phase {PHASE_NUMBER} wave {N}/{M} plan {plan_id} failed ({P}/{Q} plans done)
   [checkpoint] phase {PHASE_NUMBER} wave {N}/{M} plan {plan_id} checkpoint ({P}/{Q} plans done)
   ```

   **Completion reconciliation (EVERY runtime — any spawn whose terminal response may not arrive):**

   If a spawned agent does not return a normal terminal completion response — or its session ends abnormally (interrupted, aborted, closed, killed, timed out, `turn_aborted`, including ends the orchestrator itself initiated) — do NOT block indefinitely and do NOT classify the plan as failed yet. Read and execute `engineer/workflows/execute-phase/steps/completion-reconciliation.md` — reconcile the plan artifacts FIRST, classify SECOND: SUMMARY present AND matching recent commits → complete (proceed to step 5, do NOT re-dispatch); no completion evidence → the failure handler. Verify, never wait.

   **Configurable stall surveillance:** Every `${EXECUTOR_STALL_INTERVAL_MINUTES}`
   minutes while waiting, inspect `git log "${EXPECTED_BRANCH}" --since="${DISPATCH_TS}"`
   for activity. If no completion signal, no SUMMARY.md, and no expected-branch
   commits appear for `${EXECUTOR_STALL_THRESHOLD_MINUTES}` minutes, pause and
   ask for one recovery path: `continue waiting`, `kill and retry`, or
   `kill and switch to inline execution`.

   **A working executor is never steered.** The threshold measures time WITHOUT
   PROGRESS, not total runtime. Before treating an executor as stalled — and before sending it
   any message — read and execute `execute-phase/steps/executor-progress-policy.md`.


5.5. **Integrate the isolated wave:**
After every active write-capable worker has joined, record the integration
result/revision in the existing parallel wave status record.
Preserve blocked rows and their evidence; a worker return alone is not acceptance.

The wave's work is on branches, not in your tree — it always is, because every
plan ran isolated. Integrate it into the **session branch** before running
checks, reviewing, or starting the next wave. `merge-wave` merges into whatever
branch is current, which inside the session worktree is the session branch, so
the wave lands in the phase's own pull request and never touches the base:

```bash
git status --porcelain     # must be clean; commit planning records first
engineer_run query worktree.merge-wave --phase "${PHASE_NUMBER}"
```

Read the result rather than assuming it worked:

- `wave_clean: true` — every branch merged. Continue.
- `blocked` non-empty — **stop the wave here.** Each entry says why:

| `status` | Means | What to do |
|---|---|---|
| `blocked` | deleted a path the plan never declared | Do not merge the branch or re-run the merge. Mark the plan blocked, list it with its `undeclared_deletions` in the closing report, and continue the wave. A rename's source path counts as a removal |
| `conflict` | two plans changed the same lines | The merge was aborted and the worktree preserved. This is a wave-grouping defect: plans with overlapping `files_modified` should not have shared a wave |
| `missing` | the branch does not exist | The executor never committed. Treat the plan as blocked |
| `empty` | the branch has no commits | Same: nothing was produced |

A merged entry may also carry `out_of_scope` — paths the plan changed outside
what it declared. That is **advisory**: record it in the phase summary and let
the reviewer weigh it. It never blocks a merge.

Once the wave is clean, release its checkouts:

```bash
engineer_run query worktree.cleanup-wave --phase "${PHASE_NUMBER}"
```

Cleanup is conservative on purpose. It removes a worktree only when git agrees
its branch is an ancestor of HEAD, and reports everything it kept in
`preserved`, with the reason. **Never pass `--force` to get past a preserved
entry** — that discards work whose fate has not been decided. Report what was
preserved and let the user choose.


5.6. **Post-merge build & test gate:**

After merging all worktrees in a wave (parallel mode), or after the last plan completes
(serial mode), run a build and then the project's test suite to catch cross-plan
integration issues that individual worktree self-checks cannot detect (e.g., conflicting
type definitions, removed exports, import changes, link errors).

This addresses the Generator self-evaluation blind spot identified in Anthropic's
harness engineering research: agents reliably report Self-Check: PASSED even when
merging their work creates failures.

Read and execute `engineer/workflows/execute-phase/steps/post-merge-gate.md`.

5.7. **Post-wave shared artifact update (when at least one plan used worktrees, skip if tests failed):**

When **any** executor agent in this wave ran with `isolation="worktree"`, that agent skipped STATE.md and ROADMAP.md updates to avoid last-merge-wins overwrites. The orchestrator is the single writer for these files. After worktrees are merged back, update shared artifacts once for every completed plan in the wave (every completed isolated plan).

**Only update tracking when tests passed (TEST_EXIT=0).**
If tests failed or timed out, skip the tracking update — plans should
not be marked as complete when integration tests are failing or inconclusive.

```bash
# Guard: only update tracking if post-merge tests passed
# Timeout (124) is treated as inconclusive — do NOT mark plans complete
if [ "${TEST_EXIT}" -eq 0 ]; then
  # Update ROADMAP plan progress for each completed plan in this wave
  for plan_id in {completed_plan_ids}; do
    engineer_run query roadmap.update-plan-progress "${PHASE_NUMBER}" "${plan_id}" "complete"
  done

  # Only commit tracking files if they actually changed
  if ! git diff --quiet .planning/ROADMAP.md .planning/STATE.md 2>/dev/null; then
    engineer_run query commit "docs(phase-${PHASE_NUMBER}): update tracking after wave ${N}" --files .planning/ROADMAP.md .planning/STATE.md
  fi
elif [ "${TEST_EXIT}" -eq 124 ]; then
  echo "⚠ Skipping tracking update — test suite timed out. Plans remain in-progress. Run tests manually to confirm."
else
  echo "⚠ Skipping tracking update — post-merge tests failed (exit ${TEST_EXIT}). Plans remain in-progress until tests pass."
fi
```

Where `WAVE_PLAN_IDS` is the space-separated list of plan IDs that completed in this wave.



5.8. **Handle test gate failures (when `WAVE_FAILURE_COUNT > 0`):**

Read the count the post-merge gate recorded; a shell variable set in step 5.6 is gone by now:

```bash
# engineer-handoff:begin wave-failure-read
_ENGINEER_HANDOFF="$( { git rev-parse --absolute-git-dir 2>/dev/null || echo "${TMPDIR:-/tmp}/engineer-$(pwd | cksum | cut -d' ' -f1)"; } )/handoff"; mkdir -p "$_ENGINEER_HANDOFF"
WAVE_FAILURE_COUNT=$(wc -l < "$_ENGINEER_HANDOFF/wave-failures" 2>/dev/null | tr -d ' ' || true); WAVE_FAILURE_COUNT=${WAVE_FAILURE_COUNT:-0}
echo "WAVE_FAILURE_COUNT=${WAVE_FAILURE_COUNT}"
# engineer-handoff:end wave-failure-read
```

```
## ⚠ Post-Merge Test Failure (cumulative failures: ${WAVE_FAILURE_COUNT})

Wave {N} worktrees merged successfully, but {M} tests fail after merge.
This typically indicates conflicting changes across parallel plans
(e.g., type definitions, shared imports, API contracts).

Failed tests:
{first 10 lines of failure output}

Options:
1. Fix now (recommended) — resolve conflicts before next wave
2. Continue — failures may compound in subsequent waves
```

Note: If `WAVE_FAILURE_COUNT > 1`, strongly recommend "Fix now" — compounding
failures across multiple waves become exponentially harder to diagnose.

If "Fix now": diagnose failures (import conflicts, missing types,
or changed function signatures from parallel plans modifying the same module).
Fix, commit as `fix: resolve post-merge conflicts from wave {N}`, re-run tests.

**Why this matters:** Worktree isolation means each agent's Self-Check passes
in isolation. But when merged, add/add conflicts in shared files (models, registries,
CLI entry points) can silently drop code. The post-merge gate catches this before
the next wave builds on a broken foundation.

6. **Report completion — spot-check claims first:**

   **Wave-close heartbeat:** after spot-checks finish (pass or fail),
   before the `## Wave {N} Complete` summary, emit as a literal line:

   ```
   [checkpoint] phase {PHASE_NUMBER} wave {N}/{M} complete, {P}/{Q} plans done ({wave_success}/{wave_plan_count} ok)
   ```

   For each SUMMARY.md:
   - Verify first 2 files from `key-files.created` exist on disk
   - Check `engineer_run check evaluation-scope --plan "{phase}-{plan}" --commits-only --raw` returns `commits` with ≥1 entry (commits on THIS branch only; a commit that lives only on another branch does not satisfy the check; exit `69` means the scope could not be resolved, which fails the spot-check, never "no commits yet")
   - Check for `## Self-Check: FAILED` marker

   If ANY spot-check fails: report which plan failed, route to failure handler — ask "Retry plan?" or "Continue with remaining waves?"

   If pass:

   ```
   ---
   ## Wave {N} Complete

   **{Plan ID}: {Plan Name}**
   {What was built — from SUMMARY.md}
   {Notable deviations, if any}

   {If more waves: what this enables for next wave}
   ---
   ```

7. **Handle failures:**
   **Step 7.0 — classify before branching:**
   ```bash
   CLASS_JSON=$(engineer_run query agent.classify-failure -- "$AGENT_RETURN_BODY")
   CLASS=$(echo "$CLASS_JSON" | jq -r '.class')
   SENTINEL=$(echo "$CLASS_JSON" | jq -r '.sentinel // empty')
   RETRY_AFTER=$(echo "$CLASS_JSON" | jq -r '.retryAfterSeconds // empty')
   if [ -n "$RETRY_AFTER" ]; then RETRY_HINT="  Provider hinted retry-after: ${RETRY_AFTER}s"; else RETRY_HINT=""; fi
   ```
   One classifier branch handles sentinels across Claude/Codex. Reference: `docs/research/provider-rate-limit-signals.md`.
   **Abnormal ends reconcile first:** an abnormal session end (`turn_aborted`-class) routes through the step-4 artifact reconciliation BEFORE classifying the failure — artifacts decide.
   **Step 7.1 — `class == "quota-exceeded"`:** follow the quota-recovery fragment below.
   **Step 7.2 — `class == "classify-handoff-bug"`:**
   If error contains `classifyHandoffIfNeeded is not defined`, treat as Claude runtime bug. Run the same step-5 spot-checks; PASS => treat as success, FAIL => fall through.
   **Step 7.3 — `class == "unknown-failure"`:**
   Report failed plan and ask Continue/Stop; continuing may cascade into dependent plan failures.

@~/.claude/engineer/references/execute-phase-quota-recovery.md

@~/.claude/engineer/references/execute-phase-between-wave-reset.md

8. **Execute checkpoint plans between waves** — see `<checkpoint_handling>`.
9. **Proceed to next wave.**
   </step>
   <step name="checkpoint_handling">
   Plans with `autonomous: false` require user interaction.
   **Auto-mode checkpoint handling:**
   Read the direct auto-advance preference:

```bash
AUTO_MODE=$(engineer_run query config-get workflow.auto_advance --default false --raw)
```

When executor returns a checkpoint AND `AUTO_MODE` is `true`:

- **human-verify** → Auto-spawn continuation agent with `{user_response}` = `"approved"`. Log `⚡ Auto-approved checkpoint`. **Except `blocking-human`.**
- **decision** → `auto_select` present: auto-spawn with `{user_response}` = that option, log `⚡ Auto-selected: [option]`. Absent: present to user. **Except `blocking-human`.**
- **human-action** → Present to user (existing behavior below). Auth gates cannot be automated.

<!-- engineer:protected -->

**Carve-out — overrides all branches above.** If the returned `Gate:` is `blocking-human` (precondition-unmet), or its `<what-built>` mentions `Package verification required before install` or `Package install failed — human verification required`, never auto-approve or auto-select. Present to user (standard flow). Log `⛔ blocking-human gate — auto-mode suspended`.

**Standard flow (not auto-mode, human-action, or blocking-human):**

1. Spawn agent for checkpoint plan
2. Agent runs until checkpoint task or auth gate → returns structured state
3. Agent return includes: completed tasks table, current task + blocker, checkpoint type/details, what's awaited
4. **Present to user:**

   ```
   ## Checkpoint: [Type]

   **Plan:** 03-03 Dashboard Layout
   **Progress:** 2/3 tasks complete

   [Checkpoint Details from agent return]
   [Awaiting section from agent return]
   ```

5. User responds: "approved"/"done" | issue description | decision selection
6. **Spawn continuation agent (NOT resume)** with a prompt built from these placeholders (there is no separate template file; this list is the contract):
   - `{completed_tasks_table}`: From checkpoint return, wrapped in a `<completed_tasks>` tag (the executor's continuation handling keys on it)
   - `{resume_task_number}` + `{resume_task_name}`: Current task
   - `{user_response}`: What user provided
   - `{resume_instructions}`: Based on checkpoint type
7. Continuation agent verifies previous commits, continues from resume point
8. Repeat until plan completes or user stops

**Why fresh agent, not resume:** Resume relies on internal serialization that breaks with parallel tool calls. Fresh agents with explicit state are more reliable.

**Checkpoints in parallel waves:** Agent pauses and returns while other parallel agents may complete. Present checkpoint, spawn continuation, wait for all before next wave.
</step>

<step name="aggregate_results">
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

The direct security/Nyquist gates and SECURITY threats-open check are the first step of the shared
verification step (`verify_post_security_gate` in `verify_phase_goal` below), so verify-work's
re-verification route runs them too.
</step>

<!-- engineer:section id="partial-wave" when="flag:--wave" -->

If `section_manifest` is `null` or `"partial-wave"` is in its `included` list: read and execute `engineer/workflows/execute-phase/steps/partial-wave.md`. Otherwise skip — do not read the file.

<!-- /section -->

<step name="codebase_drift_gate">
Read and execute `@~/.claude/engineer/workflows/execute-phase/steps/codebase-drift-gate.md` in full.
</step>
<step name="verify_phase_goal">
Verify phase achieved its GOAL, not just completed tasks: read and execute
`engineer/workflows/execute-phase/steps/verify-phase-goal.md` — the ONE verification action, the
whole sequence (the `verify:post` dispatch with the SECURITY threats-open gate, `code_review_gate`
with its TDD escalation, the gap-closure parent-artifact close, the manifest-gated `regression_gate`,
the verifier dispatch, the fingerprint, and the owner's `verification.status` read with stderr
kept), shared with verify-work. If it stopped (TDD block, regression abort, refused
report), stop here.

**TDD review escalation:** the `tdd.review-checkpoint` gate is advisory (`blocking: false`)
except when `TDD_MODE=true` AND `GATE_RESULT.block == true` — where the shared
step escalates the end-of-phase review to blocking: refuse to mark the phase complete and present
`Phase blocked: {N} TDD plan(s) violate the RED→GREEN gate sequence under TDD.` Never proceed to
`close_parent_artifacts`, `verify_phase_goal`'s verifier or `phase.complete` past that block. Full
contract: `engineer/references/tdd.md` and the step's `code_review_gate`.

Route on `$STATUS`: if `passed`, proceed to update_roadmap. Otherwise keep the phase pending — present `$NEXT_ACTION` to the user and, when `$NEXT_COMMAND` is non-empty, show it as the next command to run. The query covers every case — including no report (`missing`) and no phase directory (`phase_dir_not_found`) — and a status outside the closed set is a hard error the shared step already halted on, so no per-status arm needs to be listed here.

**If human_needed:**

**Step A: Persist human verification items as UAT file.**

Create `{phase_dir}/{phase_num}-UAT.md` using UAT template format:

```markdown
---
status: testing
phase: {phase_num}-{phase_name}
source: [{phase_num}-VERIFICATION.md]
started: [now ISO]
updated: [now ISO]
---

## Current Test

number: 1
name: {first human_verification item description}
expected: |
{expected behavior from VERIFICATION.md}
awaiting: user response

## Tests

{For each human_verification item from VERIFICATION.md:}

### {N}. {item description}

expected: {expected behavior from VERIFICATION.md}
result: [pending]

## Summary

total: {count}
passed: 0
issues: 0
pending: {count}
skipped: 0
blocked: 0

## Gaps
```

Commit the file:

```bash
engineer_run query commit "test({phase_num}): persist human verification items as UAT" --files "{phase_dir}/{phase_num}-UAT.md"
```

**Step B: Present to user**:

```
## ◷ Phase {X}: {Name} — Human Verification Needed

All automated checks passed. {N} item(s) require human testing before this phase can be marked complete:

{From VERIFICATION.md human_verification section}

Tests saved to `{phase_num}-UAT.md`.

When ready to run the tests:

`/verify-work {X} `

Verify-work will walk you through each item and mark the phase complete when all tests pass.
```

**Do NOT advance the phase from this branch.** Phase completion is handled by verify-work's auto-transition after UAT passes.

**If user acknowledges without reporting issues (including "ok", "noted", "ack", "got it", "approved", "done", "yes", "pass", or similar):** Stop. The phase remains pending. No further orchestrator action — wait for the user to run `/verify-work`.

**If user reports issues now:** Proceed to gap closure.

**If gaps_found:**
@~/.claude/engineer/references/execute-phase-requirement-revert.md

```
## ⚠ Phase {X}: {Name} — Gaps Found

**Score:** {N}/{M} must-haves verified
**Report:** {phase_dir}/{phase_num}-VERIFICATION.md

### What's Missing
{Gap summaries from VERIFICATION.md}

---
## ▶ Next Up — [${PROJECT_CODE}] ${PROJECT_TITLE}

`/clear` then:

`/plan-phase {X} --gaps `

Also: `cat {phase_dir}/{phase_num}-VERIFICATION.md` — full report
Also: `/verify-work {X} ` — manual testing first
```

Gap closure cycle: `/plan-phase {X} --gaps ` reads VERIFICATION.md → creates gap plans with `gap_closure: true` → user runs `/execute-phase {X} --gaps-only ` → verifier re-runs.
</step>

<!-- engineer:section id="gap-closure-artifacts" when="state:gap-closure-phase" -->

The `gap-closure-artifacts` section is evaluated inside the shared verification step
(`verify_phase_goal` above) — between its code-review gate and its regression gate, where it ran
before — gated on this id exactly as every section here is gated.

<!-- /section -->

<!-- engineer:section id="regression-gate" when="state:has-prior-phases" -->

The `regression-gate` section is evaluated inside the shared verification step (`verify_phase_goal`
above), which gates it on this id exactly as every section here is gated.

<!-- /section -->

<step name="update_roadmap">
**Mark phase complete and update all tracking files:**

```bash
COMPLETION=$(engineer_run query phase.complete "${PHASE_NUMBER}")
```

The CLI handles:

- Marking phase checkbox `[x]` with completion date
- Updating Progress table (Status → Complete, date)
- Updating plan count to final
- Advancing STATE.md to next phase
- Updating REQUIREMENTS.md traceability
- Scanning for verification debt (returns `warnings` array)

Extract from result: `next_phase`, `next_phase_name`, `is_last_phase`, `warnings`, `has_warnings`.

**If has_warnings is true**:

```
## Phase {X} marked complete with {N} warnings:

{list each warning}

These items are tracked and will appear in `/progress` and `/audit-uat`.
```

```bash
engineer_run query commit "docs(phase-{X}): complete phase execution" --files .planning/ROADMAP.md .planning/STATE.md .planning/REQUIREMENTS.md {phase_dir}/*-VERIFICATION.md
```

</step>


<step name="graduation_scan">
After canonical phase completion, run the retained `engineer/workflows/graduation.md` method for its bounded improvement scan and disposition. Preserve manual `/extract-learnings` as the explicit learning extraction owner.
</step>

<step name="auto_copy_learnings">
**Auto-extract and copy phase learnings to global store (when enabled).**

This step runs AFTER phase completion and SUMMARY.md is written. It produces the phase's
learnings artifact (the sole producer is otherwise the user-invoked
`/extract-learnings`) and copies it to the global learnings store at
`~/.engineer/knowledge/`.

**Check config gate:**

```bash
GL_ENABLED=$(engineer_run query config-get features.global_learnings --raw 2>/dev/null || echo "false")
```

**If `GL_ENABLED` is not `true`:** Skip this step entirely (feature disabled by default).

**If enabled:**

1. Run the `extract-learnings` workflow for the JUST-COMPLETED phase (its
   `write_learnings` step writes `{phase_dir}/{PADDED_PHASE}-LEARNINGS.md`). Extraction
   failure must NOT block phase completion — report the failure and continue.
2. Copy the phase artifact to the global store:

```bash
engineer_run query learnings.copy --phase "${PHASE_NUMBER}" 2>/dev/null || echo "⚠ Learnings copy failed — continuing"
```

Copy failure must NOT block phase completion.
</step>

<step name="close_phase_todos">
**Auto-close todos whose `resolves_phase` matches this phase **, after `update_roadmap`.

```bash
shopt -s nullglob 2>/dev/null; setopt NULL_GLOB 2>/dev/null
PENDING_DIR=".planning/todos/pending"
COMPLETED_DIR=".planning/todos/completed"
mkdir -p "$COMPLETED_DIR"
PHASE_NUM="${PHASE_NUMBER}"

normalize_phase_num() {
  printf '%s' "${1//\"/}" | sed 's/^0*\([0-9]\)/\1/'
}
PHASE_NUM_NORM=$(normalize_phase_num "$PHASE_NUM")
CLOSED=()
for TODO_FILE in "$PENDING_DIR"/*.md; do
  [ -f "$TODO_FILE" ] || continue
  RP=$(awk '/^---/{c++;next} c==1 && /^resolves_phase:/{print $2;exit} c==2{exit}' "$TODO_FILE" 2>/dev/null || true)
  RP_NORM=$(normalize_phase_num "$RP")
  [ -n "$RP_NORM" ] && [ "$RP_NORM" = "$PHASE_NUM_NORM" ] || continue
  mv "$TODO_FILE" "$COMPLETED_DIR/"
  CLOSED+=("$(basename "$TODO_FILE")")
done
if [ ${#CLOSED[@]} -gt 0 ]; then
  ADDED=(); REMOVED=()
  for f in "${CLOSED[@]}"; do ADDED+=("$COMPLETED_DIR/$f"); REMOVED+=("$PENDING_DIR/$f"); done
  engineer_run query commit "docs(phase-${PHASE_NUMBER}): close ${#CLOSED[@]} resolved todo(s)" --files "${ADDED[@]}" .planning/STATE.md --files-removed "${REMOVED[@]}" || true
  echo "◆ Closed ${#CLOSED[@]} todo(s) for Phase ${PHASE_NUMBER}:"; printf '  ✓ %s\n' "${CLOSED[@]}"
fi
```

No matches: skip silently, never blocks.
</step>


</process>

<context_efficiency>
Orchestrator: ~10-15% context for 200k windows, can use more for 1M+ windows.
Subagents: fresh context each (200k-1M depending on model). No polling (Agent blocks). No context bleed.

For 1M+ context models, consider:

- Passing richer context (code snippets, dependency outputs) directly to executors instead of file paths
- Running small phases (≤3 plans, no dependencies) inline without subagent spawning overhead
- Relaxing /clear recommendations — context rot onset is much further out with 5x window
  </context_efficiency>

<failure_handling>

- **Quota / rate-limit (any runtime):** Agent return body contains a sentinel like `usage limit`, `rate limit`, `429`, `too many requests`, `RESOURCE_EXHAUSTED`, `usage_limit_reached`. Route via `engineer_run query agent.classify-failure` → `class: "quota-exceeded"`. Do not offer retry-now; the right action is wait-for-reset and resume.
- **classifyHandoffIfNeeded false failure:** Agent reports "failed" but error is `classifyHandoffIfNeeded is not defined` → Claude Code bug, not Engineer. Spot-check (SUMMARY exists, commits present) → if pass, treat as success
- **Agent fails mid-plan:** Missing SUMMARY.md → report, ask user how to proceed
- **Dependency chain breaks:** Wave 1 fails → Wave 2 dependents likely fail → user chooses attempt or skip
- **All agents in wave fail:** Systemic issue → stop, report for investigation
- **Checkpoint unresolvable:** "Skip this plan?" or "Abort phase execution?" → record partial progress in STATE.md
  </failure_handling>

<resumption>
Re-run `/execute-phase {phase}` → discover_plans finds completed SUMMARYs → skips them → resumes from first incomplete plan → continues wave execution.

STATE.md tracks: last completed plan, current wave, pending checkpoints.
</resumption>
