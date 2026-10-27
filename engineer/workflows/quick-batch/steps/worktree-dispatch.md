**Step 6: Worktree create + executor dispatch**

This is the batch's mutating wave. Require the previously resolved mandatory worktree mode. A stale fork base fails its worker's branch check and preserves the checkout; never execute on the primary/shared checkout.

**Effective concurrency:** runtime capacity, actual host free slots, requested jobs and task count all bound fan-out.
```bash
QB_EXEC_CONC_JSON=$(engineer_run query quick-batch.effective-concurrency --jobs "$JOBS" --task-count "$ITEM_COUNT" --capacity "$CAPACITY" --isolation "$ISOLATION" --mutating --raw)
EXEC_CONCURRENCY=$(printf '%s' "$QB_EXEC_CONC_JSON" | python -I -c "import json,sys; j=json.load(sys.stdin); print(str(j['concurrency']))")
```

**Dispatch rounds.** Repeat until no item is eligible-and-not-yet-dispatched
(bounded by `$ITEM_COUNT` rounds):

1. Re-derive eligibility (also reconciles crash-window/blocked-propagation —
   safe to call repeatedly, idempotent when nothing changed):
   ```bash
   QB_ELIG_JSON=$(engineer_run query quick-batch.resume --batch "$BATCH_ID" --raw)
   ```
   Parse `eligible` (quick ids ready to execute — every dependency already
   `complete`) and refresh `$BATCH_MANIFEST_JSON` from its `manifest`.

   **Crash-window guard (#3677):** inspect resume.evidence and resume.reconcile. A SUMMARY file merely suppresses duplicate dispatch; it is not proof of success. Require committed complete SUMMARY, source commits, matching branch/base, clean worker tree and host-confirmed stop before moving it to executed or merge. Unknown/active assignments keep their ownership and count against capacity. Reconcile the durable dispatchedWorktree/dispatchedBranch/dispatchedBase triple; do not guess from a slug or abandoned process. Use quick-batch.filter-executed on IDs with reconciled execution evidence. Preserve partial/failed results and continue only genuinely eligible independent entries.

2. **Backpressure.** Not every eligible item necessarily spawns this round —
   cap fan-out at `$EXEC_CONCURRENCY` minus current in-flight count (row
   27/39):
   ```bash
   QB_SPAWN_JSON=$(engineer_run query quick-batch.spawn-plan --eligible "$ELIGIBLE_IDS_JSON" --capacity "$EXEC_CONCURRENCY" --in-flight "$IN_FLIGHT_COUNT" --raw)
   ```
   Parse `spawn` (dispatch these now) and `pending` (leave `pending` in
   `BATCH.json` — already the case, no write needed; NEVER mark these
   `failed`, NEVER increase fan-out to compensate).

3. **Create worktrees + dispatch executors, ONE AT A TIME per `spawn` item**
   (`git worktree add` races on `.git/config.lock` — never simultaneous,
   `execute-phase.md`'s own discipline):

   For each item in `spawn`, in order:

   ```bash
   # ITEM_DIR is this item's runtime-returned directory; never reconstruct it.
   ```

   **`isolation == "harness-worktree"`:** one `Agent()` per message,
   `run_in_background: true`. Same prompt shape as `/quick`'s own
   executor dispatch (Step 6 of `quick.md`) — required_reading, agent skills,
   `<submodule_commit_guard>` using this project's `$SUBMODULE_PATHS`
   (identical block, verbatim) — with these differences:
   ```
   Agent(
     prompt="
   Execute quick-batch item ${quick_id}.

   <required_reading>
   - ${ITEM_DIR}/${quick_id}-PLAN.md (Plan)
   - ${STATE_PATH} (Project state — READ ONLY, do not write it)
   - ./AGENTS.md or ./.claude/AGENTS.md (if exists)
   </required_reading>

   ${AGENT_SKILLS_EXECUTOR}

   <submodule_commit_guard>
   (same SUBMODULE_PATHS fail-loud guard as /quick — see engineer/workflows/quick.md Step 6)
   </submodule_commit_guard>

   <constraints>
   - Execute all tasks in the plan; commit each task atomically
   - Create summary at: ${ITEM_DIR}/${quick_id}-SUMMARY.md with `status: complete` in frontmatter
   - NEVER invoke /quick or any other workflow command — you are a leaf, not a coordinator
   - NEVER write .planning/quick/batches/${BATCH_ID}.json
   - Do NOT update STATE.md or ROADMAP.md — the orchestrator owns those writes after every item in this dispatch round completes (ADR-1239 single-writer invariant)
   - MUST commit your owned source changes and required complete SUMMARY.md before returning complete. STATE.md, ROADMAP.md and batch records remain coordinator-owned; do not edit or commit them. The coordinator commits its own planning and shared-record artifacts separately.
   </constraints>
   ",
     subagent_type="executor",
     model="{resolved_executor_model}",
     effort="{resolved_executor_effort}",
     isolation="worktree",
     description="Execute ${quick_id}: ${description}"
   )
   ```
   Record `{agent_id, worktree_path, branch, expected_base, allowed_bases}`
   from the executor's return into `$QUICK_BATCH_WORKTREE_MANIFEST` (a JSON
   file, initialized `{"worktrees":[]}` before the first round — same shape
   `/quick`'s own `QUICK_WORKTREE_MANIFEST` uses).

   **`isolation == "orchestrator-worktree"`:** coordinator calls `engineer_run query worktree.create "${quick_id}" --phase "batch-${BATCH_ID}-wave-${CUR_WAVE}" --base "${EXPECTED_BASE}" --files "${PLAN_FILES[@]}" --deletions "${PLAN_DELETIONS[@]}"`. Read returned path/branch/base, then dispatch the exact executor through the native Claude/Codex Agent with the full project_root_pin bound to that path. No process-spawn helper is required.

   Resolve executor model AND effort immediately before dispatch using `resolve-model executor --raw` and `resolve-effort executor --raw`. Substitute the actual resolved values inline and omit each parameter whose resolution is `inherit`; the placeholders above are explanatory, never literal host arguments.

   **Harness registration:** dispatch with literal isolation="worktree" and the complete branch-check guard bound to EXPECTED_BASE. Register actual host metadata through `worktree.record-agent "${quick_id}" --phase "batch-${BATCH_ID}-wave-${CUR_WAVE}" --branch "${WORKER_BRANCH}" --path "${WORKER_PATH}" --base "${EXPECTED_BASE}" --files "${PLAN_FILES[@]}" --deletions "${PLAN_DELETIONS[@]}"`. Missing metadata blocks integration; never register the coordinator branch.

   **Durable worktree-recovery persistence (#3677 — `harness-worktree`/
   `orchestrator-worktree`):** immediately after
   recording `{agent_id, worktree_path, branch, expected_base}` into the
   EPHEMERAL `$QUICK_BATCH_WORKTREE_MANIFEST` above, ALSO persist the same
   triple durably onto this item in `BATCH.json`:
   ```bash
   # Build UPDATES_JSON with a JSON serializer from exact runtime metadata, never shell interpolation.
   engineer_run query quick-batch.update --batch "$BATCH_ID" --updates "$UPDATES_JSON"
   ```
   The ephemeral manifest is a per-process `mktemp` file (same shape
   `/quick`'s own `QUICK_WORKTREE_MANIFEST` uses) — it does NOT survive
   a coordinator crash/restart. A RESUMED coordinator's Step 7
   (`merge-wave.md`) reads this durable BATCH.json triple as its fallback
   for any item the crash-window guard above correctly did NOT re-dispatch
   in the current process.

   > **ORCHESTRATOR RULE — CODEX RUNTIME**: serialize worktree creation and registration, while already-created workers run concurrently up to bounded capacity. After dispatch wait before touching owned paths or integration. A timeout is never confirmed stop.

4. **After host-confirmed stop for every item in this round:** inspect the committed complete SUMMARY and source commits in the actual worker checkout. Missing, partial or uncommitted evidence leaves the entry blocked with ownership and worktree preserved. Do not reset it to pending, reassign paths or merge it. Persist workerState stopped/exited/interrupted only from real host confirmation, then status executed with the actual source commit. A file's presence alone never proves completion.

Continue to Step 7 after the selected current wave joins; integrate it before recomputing later eligibility. Capacity-pending entries remain pending, never failed.

Before dispatch commit coordinator-owned plans/quick records at the captured EXPECTED_BASE, validate exact files/deletions/resources and reject submodule intersections. Persist status executing plus the durable worker triple and planDigest as one quick-batch.update transaction; unknown workers retain ownership until a confirmed stop. Join every worker in the current wave, execute merge-wave, selected verification and completion for that wave, then recompute resume eligibility before the next wave. Do not queue dependent waves before predecessor integration.
