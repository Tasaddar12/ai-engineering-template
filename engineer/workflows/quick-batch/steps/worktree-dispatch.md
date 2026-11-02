**Step 6: Worktree create + executor dispatch**

This is the batch's MUTATING wave — worktree create/executor dispatch/merge
require mandatory worktree isolation,
unlike planning/research above.

```bash
_engineer_identity_ok() {
  [ -f "$1" ] || return 1
  [ "$(sh "$1" query runtime-identity --pick packageName --raw 2>/dev/null)" = "engineer-runtime" ]
}
_engineer_select() {
  for _engineer_candidate do
    if _engineer_identity_ok "$_engineer_candidate"; then
      ENGINEER_RUN="$_engineer_candidate"
      return 0
    fi
  done
  return 1
}
if [ -n "${ENGINEER_RUN:-}" ]; then
  _engineer_identity_ok "$ENGINEER_RUN" || {
    printf '%s\n' "ERROR: ENGINEER_RUN does not identify engineer-runtime: $ENGINEER_RUN" >&2
    exit 1
  }
else
  _engineer_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
  _engineer_runtime_root=${RUNTIME_DIR:-$_engineer_root}
  _engineer_path_candidate=$(command -v engineer_run 2>/dev/null || true)
  _engineer_select \
    "$_engineer_root/engineer/bin/engineer_run" \
    "$_engineer_runtime_root/engineer/bin/engineer_run" \
    "$_engineer_root/.claude/engineer/bin/engineer_run" \
    "$_engineer_root/.codex/engineer/bin/engineer_run" \
    "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/engineer/bin/engineer_run" \
    "${CODEX_HOME:-$HOME/.codex}/engineer/bin/engineer_run" \
    "$_engineer_path_candidate" || {
    printf '%s\n' 'ERROR: No engineer-runtime launcher was found. Install the Claude or Codex workflow runtime or set ENGINEER_RUN.' >&2
    exit 1
  }
fi
export ENGINEER_RUN
engineer_run() {
  sh "$ENGINEER_RUN" "$@"
}
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  _engineer_path_escaped=$(printf '%s' "${ENGINEER_RUN%/*}" | sed 's/[\\`"$]/\\&/g')
  printf 'export PATH="%s:$PATH"\n' "$_engineer_path_escaped" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true
fi
```

Resolve mandatory isolation before dispatch. Accept only the two supported worktree modes; unavailable isolation blocks execution. Capture the expected base for branch verification.

**Effective concurrency for this MUTATING wave** (`mutating` forces
declared capacity for the isolated native agents):
```bash
QB_EXEC_CONC_JSON=$(engineer_run quick-batch effective-concurrency --jobs "$JOBS" --task-count "$ITEM_COUNT" --capacity "$CAPACITY" --isolation "$ISOLATION" --mutating --raw)
EXEC_CONCURRENCY=$(printf '%s' "$QB_EXEC_CONC_JSON" | engineer_run query json.get --field concurrency --default 1 --raw 2>/dev/null || printf 1)
```

Initialize the owned manifest before dispatch; keep the returned path across every item and receipt:

```bash
ORCH_ROOT=$(git rev-parse --show-toplevel) || exit $?
QB_WORKTREE_STATE=$(engineer_run query worktree.manifest init --phase "quick-batch-${BATCH_ID}" --root "$ORCH_ROOT") || exit $?
QUICK_BATCH_WORKTREE_MANIFEST=$(engineer_run query json.get --payload "$QB_WORKTREE_STATE" --field manifest --raw) || exit $?
```

**Dispatch rounds.** Repeat until no item is eligible-and-not-yet-dispatched
(bounded by `$ITEM_COUNT` rounds):

1. Re-derive eligibility (also reconciles crash-window/blocked-propagation —
   safe to call repeatedly, idempotent when nothing changed):
   ```bash
   QB_ELIG_JSON=$(engineer_run quick-batch resume --batch "$BATCH_ID" --raw)
   ```
   Parse `eligible` (quick ids ready to execute — every dependency already
   `complete`) and refresh `$BATCH_MANIFEST_JSON` from its `manifest`.

   **Crash-window guard (mirrors `planner-wave.md`'s PLAN.md-existence
   check one layer earlier):** `quick-batch resume`'s `eligible` is
   purely status/dependency-derived; it does NOT know an item already
   finished executing. A coordinator crash between this step returning
   (executor committed, `SUMMARY.md` written) and Step 7's merge leaves
   `BATCH.json` at `pending`; completion has not run, so the task's `QUICK.md`
   also remains unchanged. On `--resume`, such an item still comes back
   `eligible` here. Separately, if Step 9 is interrupted after writing a
   `completionTransaction`, resume replays that durable intent against the
   `QUICK.md` record after rechecking completion evidence. Before computing `spawn-plan`, determine which eligible
   items already have `${item_dir}/${quick_id}-SUMMARY.md` on disk (same
   `item_dir` derivation via `generate-slug` every other step uses), then
   let the PURE `quick-batch filter-executed` verb
   (`filterAlreadyExecuted`, `src/quick-batch-dispatch.cts`) decide which
   ids are actually safe to spawn — never re-derive that split inline:
   ```bash
   EXECUTED_IDS_JSON="[]" # JSON array of quick_ids whose SUMMARY.md already exists on disk this round
   QB_FILTER_JSON=$(engineer_run quick-batch filter-executed --eligible "$ELIGIBLE_IDS_JSON" --executed "$EXECUTED_IDS_JSON" --raw)
   ```
   Parse `spawnEligible` (safe to spawn this round) and `alreadyExecuted`
   (diagnostic only — report these as "already executed, routing to merge"
   rather than dispatching them). Replace `$ELIGIBLE_IDS_JSON` with
   `spawnEligible` before continuing to backpressure below.

   NEVER re-dispatch it into a second worktree for any id `filter-executed`
   returns in `alreadyExecuted`. It is not lost: Step 7's own mergeable-wave
   criterion
   (`engineer/workflows/quick-batch/steps/merge-wave.md` Step 1) already
   picks up any `pending` item with an on-disk `SUMMARY.md` that isn't yet
   merged, independent of this eligible/spawn list — dropping it here only
   prevents the duplicate dispatch, it does not remove it from the batch.

2. **Backpressure.** Not every eligible item necessarily spawns this round —
   cap fan-out at `$EXEC_CONCURRENCY` minus current in-flight count (row
   27/39):
   ```bash
   QB_SPAWN_JSON=$(engineer_run quick-batch spawn-plan --eligible "$ELIGIBLE_IDS_JSON" --capacity "$EXEC_CONCURRENCY" --in-flight "$IN_FLIGHT_COUNT" --raw)
   ```
   Parse `spawn` (dispatch these now) and `pending` (leave `pending` in
   `BATCH.json` — already the case, no write needed; NEVER mark these
   `failed`, NEVER increase fan-out to compensate).

3. **Create worktrees + dispatch executors, ONE AT A TIME per `spawn` item**
   (`git worktree add` races on `.git/config.lock` — never simultaneous,
   `execute-phase.md`'s own discipline):

   For each item in `spawn`, in order:

   ```bash
   SLUG=$(engineer_run query generate-slug "$description" --raw)
   ITEM_DIR="${quick_dir}/${quick_id}-${SLUG}"
   ORCH_ROOT=$(git rev-parse --show-toplevel) || exit $?
   EXPECTED_BASE=$(git rev-parse HEAD) || exit $?
   ALLOWED_BASES_JSON=$(EXPECTED_BASE="$EXPECTED_BASE" node -e 'process.stdout.write(JSON.stringify([process.env.EXPECTED_BASE]))') || exit $?
   ITEM_DIR_REL=$(git -C "$ITEM_DIR" rev-parse --show-prefix) || exit $?
   ITEM_DIR_REL="${ITEM_DIR_REL%/}"
   [ "$(git -C "$ITEM_DIR" rev-parse --show-toplevel)" = "$ORCH_ROOT" ] || exit 42
   SUMMARY_PATH="${ITEM_DIR_REL}/${quick_id}-SUMMARY.md"
   plan_id="quick-${quick_id}"
   PLAN_JSON=$(engineer_run query frontmatter.get "${ITEM_DIR}/${quick_id}-PLAN.md") || exit $?
   PLAN_FILES_JSON=$(printf '%s' "$PLAN_JSON" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{const v=JSON.parse(s).files_modified;if(!Array.isArray(v))process.exit(1);process.stdout.write(JSON.stringify(v))})') || exit $?
   PLAN_DELETIONS_JSON=$(printf '%s' "$PLAN_JSON" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{const v=JSON.parse(s).files_deleted||[];if(!Array.isArray(v))process.exit(1);process.stdout.write(JSON.stringify(v))})') || exit $?
   WAVE_WORKTREE_MANIFEST="$QUICK_BATCH_WORKTREE_MANIFEST"
   engineer_run query worktree.manifest init --manifest "$WAVE_WORKTREE_MANIFEST" --root "$ORCH_ROOT" || exit $?
   if [ "$ISOLATION" = "orchestrator-worktree" ]; then
     ITEM_WORKTREE=$(engineer_run query worktree.create "$plan_id" --phase "quick-batch-${BATCH_ID}" --manifest "$WAVE_WORKTREE_MANIFEST" --root "$ORCH_ROOT" --base "$EXPECTED_BASE" --files-json "$PLAN_FILES_JSON" --deletions-json "$PLAN_DELETIONS_JSON" --summary-path "$SUMMARY_PATH") || exit $?
     WORKTREE_PATH=$(engineer_run query json.get --payload "$ITEM_WORKTREE" --field worktree_path --raw) || exit $?
     WORKTREE_BRANCH=$(engineer_run query json.get --payload "$ITEM_WORKTREE" --field branch --raw) || exit $?
     EXPECTED_BASE=$(engineer_run query json.get --payload "$ITEM_WORKTREE" --field expected_base --raw) || exit $?
     ALLOWED_BASES_JSON=$(engineer_run query json.get --payload "$ITEM_WORKTREE" --field allowed_bases) || exit $?
     [ "$(git -C "$WORKTREE_PATH" rev-parse HEAD)" = "$EXPECTED_BASE" ] || exit 42
     [ "$(git -C "$WORKTREE_PATH" branch --show-current)" = "$WORKTREE_BRANCH" ] || exit 42
   fi
   ```

   For orchestrator isolation, generate the actual root guard before composing this item prompt:

   ```bash
   BATCH_ROOT_GUARD=""
   if [ "$ISOLATION" = "orchestrator-worktree" ]; then
     BATCH_ROOT_GUARD=$(WORKTREE_PATH="$WORKTREE_PATH" node <<'NODE'
const q = value => "'" + value.replaceAll("'", "'\\''") + "'";
process.stdout.write(`PINNED_ROOT=${q(process.env.WORKTREE_PATH)}
ACTUAL_ROOT=$(git rev-parse --show-toplevel) || exit 42
PINNED_TL=$(git -C "$PINNED_ROOT" rev-parse --show-toplevel) || exit 42
[ "$ACTUAL_ROOT" = "$PINNED_TL" ] || { echo "FATAL: batch executor root differs from assigned checkout" >&2; exit 42; }
`);
NODE
     ) || exit $?
   fi
   ```

   **Native executor prompt (both modes):** omit the empty project_root_pin block for harness isolation and embed its existing literal branch/base guard before dispatch. For harness isolation use one `Agent()` per message,
   `run_in_background: true`. Same prompt shape as `/quick`'s own
   executor dispatch (Step 6 of `quick.md`) — required_reading, agent skills,
   `<submodule_commit_guard>` using this project's `$SUBMODULE_PATHS`
   (identical block, verbatim) — with these differences:
   ```
   Agent(
     prompt="
   Execute quick-batch item ${quick_id}.

   <project_root_pin>
   ${BATCH_ROOT_GUARD}
   </project_root_pin>
   Under orchestrator isolation run the supplied literal guard before the first read/write and every commit. Checkout creation, host dispatch and receipt recording belong to the coordinator.

   <required_reading>
   - ${ITEM_DIR_REL}/${quick_id}-PLAN.md (Plan)
   - ${STATE_PATH} (Project state — READ ONLY, do not write it)
   - ./CLAUDE.md or ./.claude/CLAUDE.md (if exists)
   </required_reading>

   ${AGENT_SKILLS_EXECUTOR}

   <submodule_commit_guard>
   (same SUBMODULE_PATHS fail-loud guard as /quick — see engineer/workflows/quick.md Step 6)
   </submodule_commit_guard>

   <constraints>
   - Execute all tasks in the plan; commit each task atomically
   - Create summary at: ${ITEM_DIR_REL}/${quick_id}-SUMMARY.md with `status: complete` in frontmatter
   - NEVER invoke /quick or any other Engineer command — you are a leaf, not a coordinator
   - NEVER write .planning/quick-batches/${BATCH_ID}/BATCH.json
   - Do NOT update shared STATE.md or ROADMAP.md; quick-batch completion is tracked in BATCH.json and each task's QUICK.md
   - Commit this assigned SUMMARY.md with status complete before returning. Completion requires source and SUMMARY committed in this attempt. Do NOT modify shared STATE.md, ROADMAP.md, REQUIREMENTS.md or config; the coordinator owns those records.
   </constraints>
   ",
     subagent_type="executor",
     model="{executor_model}",
     {harnessFlag}
     description="Execute ${quick_id}: ${description}"
   )
   ```
   Under orchestrator isolation, setup above already created the checkout. Bind the native executor's working-directory/workspace input to the returned `WORKTREE_PATH` and embed the complete runnable root pin before composing its prompt, following `execute-phase/steps/sequential-root-pin.md`. Do not delegate checkout creation or another dispatch to the child. If binding is unavailable, preserve the checkout and block this item.

   For **both** modes, capture the actual host agent id from dispatch and keep each item's plan id, path, branch, captured base/allowed bases, exact files/deletions, SUMMARY path and manifest in coordinator state keyed to that host id. Do not take termination from the executor's text. Obtain the native host's terminal event through its wait/status tool, preserve that original JSON outside the checkout and bind the host-observed status/id/kind for the shared **Native terminal receipt** procedure in `execute-phase/steps/executor-isolation-dispatch.md`. For harness mode get the actual checkout path from host metadata and branch from Git; allowed bases remain the pre-dispatch capture. For orchestrator mode reuse the exact create result. Restore the specific item's inputs before recording; another item's shell variables are not its identity.

   Run `engineer_run query worktree.record-agent "$plan_id" --manifest "$QUICK_BATCH_WORKTREE_MANIFEST" --agent-id "$HOST_AGENT_ID" --path "$WORKTREE_PATH" --branch "$WORKTREE_BRANCH" --base "$EXPECTED_BASE" --allowed-bases "$ALLOWED_BASES_JSON" --files-json "$PLAN_FILES_JSON" --deletions-json "$PLAN_DELETIONS_JSON" --summary-path "$SUMMARY_PATH" --terminal-receipt "$NATIVE_TERMINAL_RECEIPT"` using the receipt generated from that actual host event. This records/attaches the validated terminal receipt in the same ownership manifest before any merge. Missing stop proof or a rejected receipt preserves the item and blocks its merge; do not substitute `--completed` or a retired worker-process verb.

   The runtime-owned manifest now contains the actual `agent_id`, `worktree_path`, `branch`, `expected_base`, `allowed_bases` and terminal receipt. Read it through `worktree.manifest read`; do not hand-write a competing ownerless `{"worktrees":[]}` file. For the existing durable BATCH update below set `worktree_path=WORKTREE_PATH` and `branch=WORKTREE_BRANCH`; retain this item's actual expected base.

   **Durable worktree-recovery persistence (`harness-worktree`/
   `orchestrator-worktree` only):** immediately after
   recording `{agent_id, worktree_path, branch, expected_base}` into the
   EPHEMERAL `$QUICK_BATCH_WORKTREE_MANIFEST` above, ALSO persist the same
   triple durably onto this item in `BATCH.json`:
   ```bash
   engineer_run quick-batch update --batch "$BATCH_ID" --updates '[{"quickId":"'"$quick_id"'","dispatchedWorktree":"'"$worktree_path"'","dispatchedBranch":"'"$branch"'","dispatchedBase":"'"$expected_base"'"}]'
   ```
   The ephemeral manifest is a per-process `mktemp` file (same shape
   `/quick`'s own `QUICK_WORKTREE_MANIFEST` uses) — it does NOT survive
   a coordinator crash/restart. A RESUMED coordinator's Step 7
   (`merge-wave.md`) reads this durable BATCH.json triple as its fallback
   for any item the crash-window guard above correctly did NOT re-dispatch
   in the current process.

   > **ORCHESTRATOR RULE — CODEX RUNTIME**: after each `Agent()` call above, wait for it to return before starting the next worktree create.

4. **After every item has a recorded native terminal receipt:** verify
   `${SUMMARY_PATH}` is committed in that worker's actual branch and the ownership scope passes. Mere file presence is insufficient. If missing, the item stays
   `pending`/its worktree preserved for diagnosis rather than guessing
   completion — do not proceed to merge for it this round.

Continue to Step 7 once every eligible item has been dispatched (across
however many rounds backpressure required) and returned.
