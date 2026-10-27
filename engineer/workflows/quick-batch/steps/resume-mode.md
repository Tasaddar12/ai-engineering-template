**Step 2a: Resume mode (only when `$RESUME_BATCH_ID` is set)**

Skip this step entirely if `$RESUME_BATCH_ID` is empty.

Resume re-derives eligibility via the batch's own `resumeBatch` propagation —
it is the single source of truth for which items are still runnable. Never
re-parse a task list or re-run `quick-batch create` on resume (row 9/16 of
the design's behavior table).

```bash
source engineer/workflows/_runtime-launcher.snippet.sh
CURRENT_BASE=$(git rev-parse HEAD)
QB_RESUME_JSON=$(engineer_run query quick-batch.resume --batch "$RESUME_BATCH_ID" --current-base-revision "$CURRENT_BASE" --raw)
QB_RESUME_RC=$?
if [[ "$QB_RESUME_JSON" == @file:* ]]; then QB_RESUME_JSON=$(cat "${QB_RESUME_JSON#@file:}"); fi
```

**If `$QB_RESUME_RC` is non-zero or base_compatible is false:** the resume was refused closed — an unknown
batch id (row 18) or a diverged base revision (row 17, ADR-1239 "Base
divergence"). Print the CLI's error message verbatim and STOP. Do not dispatch
anything, do not create a new batch on the user's behalf.

**Otherwise:** parse `$QB_RESUME_JSON` for `eligible` (array of quick ids),
`transitions` (status changes just applied — e.g. a `blocked` item reverting
to `pending`, or a crash-window STATE-row detection completing an item
without re-appending, row 45), and `manifest` (the full, current batch
document).

```bash
BATCH_ID="$RESUME_BATCH_ID"
BATCH_MANIFEST_JSON=$(printf '%s' "$QB_RESUME_JSON" | python -I -c "import json,sys; j=json.load(sys.stdin); print(json.dumps(j['manifest']))")
```

Report to user:
```
Resuming batch ${BATCH_ID}: ${eligible.length} item(s) eligible now.
```

If `transitions` is non-empty, display it as a diagnostic (which items moved
to `blocked`/`complete` since the batch was last touched) — this is expected,
successful crash-window recovery, not an error (per the design's negative-space
note: a `resumeBatch` call producing zero transitions is also success, not a
no-op failure).

Continue to Step 3 in `quick-batch.md` — the DAG-layer loop in `planner-wave.md`
reads `$BATCH_MANIFEST_JSON`/`$BATCH_ID` exactly the same way whether this
batch was just created or just resumed; it reconciles per-item artifact status, committed source revision, fingerprints, Git ancestry and actual host lifecycle. File presence suppresses duplicate dispatch but never proves success. In-flight/unknown entries retain ownership and consume slots. Preserve partial/failed work and inspect it only after host-confirmed stop. A descendant session head is reported as base drift but remains compatible; a divergent base blocks execution, never silently rebases or recreates the batch. Resume performs no implicit state transition or deletion.
