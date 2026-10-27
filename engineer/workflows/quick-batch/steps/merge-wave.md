**Step 7: Deterministic merge**

**Merge rounds.** Repeat until no wave has a mergeable prefix left (bounded
by `$ITEM_COUNT` rounds):

1. For each DISTINCT `wave` value present among items that are
   `status == "executed"` with independently reconciled committed complete SUMMARY and host-confirmed worker stop and NOT yet merged: build `$WAVE_ORDER_JSON` — the
   `quick_id`s of every item AT THAT WAVE, in `$BATCH_MANIFEST_JSON.items`
   array order (this IS the order `computeWaves`/`partitionByFileOverlap`
   assigned — never re-sort it).

2. Build `$READY_JSON` — the subset of that wave's items whose
   `SUMMARY.md` already exists (an executor may still be mid-flight for a
   sibling in the same wave; row 33 — merges happen strictly in wave order,
   an out-of-order finisher waits):
   ```bash
source engineer/workflows/_runtime-launcher.snippet.sh
   QB_MERGE_ELIG_JSON=$(engineer_run query quick-batch.merge-eligible --wave-order "$WAVE_ORDER_JSON" --ready "$READY_JSON" --raw)
   ```
   Parse `mergeable` — the PREFIX of `$WAVE_ORDER_JSON` currently mergeable.
   If empty, skip this wave this round (its first item hasn't finished yet).

3. **Reconcile registry entries for mergeable, IN THAT ORDER.** Freshly parse each committed PLAN's exact paths/deletions/resources, not only BATCH plannedFiles. Use the worktree.create/record-agent registry under `batch-${BATCH_ID}-wave-${CUR_WAVE}`. Every selected worker must be registered and complete; never invent a plan-filter or manifest argument. The registry contains only this wave's workers. Preserve the shell array discipline: `for quick_id in "${mergeable[@]}"; do ...; done`, never a space-joined string.

   `quick-batch.cleanup-entry QUICK_ID --path WORKER_PATH --branch WORKER_BRANCH` is a diagnostic only: it reads real Git ancestry and dirt and does not merge or claim success. Cleanup is permitted only later, after complete evidence and ancestry.

   **Durable fallback (#3677):** for an item Step 6 did NOT dispatch this
   process — the crash-window guard correctly skipped it because
   `SUMMARY.md` already existed from a PRIOR, now-dead coordinator process —
   `$QUICK_BATCH_WORKTREE_MANIFEST` has no entry for it at all (it is a
   fresh per-process `mktemp` file). Read `$WT_PATH`/`$WT_BRANCH`/
   `$EXPECTED_BASE` from that item's OWN durable
   `dispatchedWorktree`/`dispatchedBranch`/`dispatchedBase` fields in
   `$BATCH_MANIFEST_JSON` instead — persisted by Step 6's own durable-
   persistence step at the time it actually created the worktree, in
   whichever process that was. If ALL THREE are still `null` (the item was
   never durably recorded — should not happen once Step 6 always persists
   on dispatch, but fail closed rather than guess): route this entry via
   `merge-routing --kind merge_failed --detail "missing durable worktree
   record"` the same as any other blocked entry below, and do NOT attempt
   the cleanup-wave call for it.)

4. **Integrate through the runtime primitive:**
   ```bash
   QB_MERGE_RESULT=$(engineer_run query worktree.merge-wave --phase "batch-${BATCH_ID}-wave-${CUR_WAVE}")
   ```
   Inspect every returned entry and error; never swallow a failed command. No --manifest or --force exists here. A source rename requires its old path in files_deleted. Conflicts/scope violations preserve the worker and block the affected entry; abort a real mid-merge and preserve all evidence before independent work continues.

5. **Route each entry's result:**
   - Actual successful merge result with integrated commit ancestry: persist status merged and commit through quick-batch.update. Preserve the durable worker triple until completion/verification evidence is captured. Do not claim cleanup from a merge result. After selected validation and complete quick/batch records are committed, run `worktree.cleanup-wave --phase "batch-${BATCH_ID}-wave-${CUR_WAVE}"`; inspect its actual preserved/cleaned result. Never remove an unmerged, dirty or active worker, never clear recovery identity merely because a cleanup was attempted.
   - Any other status: route via
     ```bash
     engineer_run query quick-batch.merge-routing --kind merge_failed --detail "$reason" --raw
     ```
     (or `--kind scope_violation` when `$reason` names an undeclared
     deletion — `partitionDeclaredDeletions`'s own guard). The routing result
     always carries `preserveWorktree: true` — do NOT remove the worktree or
     branch for this item; leave it for diagnosis (row 28/34/35). Do NOT call
     `quick-batch complete` for it. Continue with the rest of the batch (row
     33 — unrelated items are unaffected).

Continue to Step 9 (`--validate` routes through the verification step first)
once every wave with a mergeable prefix has been processed this round.
