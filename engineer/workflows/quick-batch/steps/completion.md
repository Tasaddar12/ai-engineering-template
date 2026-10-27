**Step 9: Completion**

For each actually integrated item whose selected acceptance/checks/verification passed, run `engineer_run query quick.update "${quick_id}" --status complete --commit "${INTEGRATED_COMMIT}"`, adding supported verification/issue/PR evidence. Persist its batch status complete with quick-batch.update and actual source/verification evidence. Unselected independent verification is not invented: a complete implementation record may retain a draft, while readiness still requires canonical current independent evidence. Run state.record-session with the actual result. The runtime owns completed-task/state records; do not append a table manually.

Call `engineer_run query quick-batch.complete "${BATCH_ID}"` only after reconciling all entries. All complete yields complete; terminal failed/blocked/human-needed entries yield partial, never a clean finish. Pending/active/unknown entries keep the batch open. Explicitly report that result without treating the existence of artifacts as success.

Items NOT reaching this call — `human_needed`, `failed` (planner/checker/
merge/verification failure), or still `blocked`/`pending` (a dependency
failed, row 32) — are left exactly as their respective routing step set
them. No STATE row, no `complete` status, worktree preserved where
applicable.

**Final commit.** Stage only exact coordinator-owned artifacts produced this run: integrated planning/research records where their producing artifact contract assigns them to the coordinator, full persisted `--validate` VERIFICATION.md, batch records and
`.planning/STATE.md`. Worker-owned complete SUMMARY.md is already committed by its source worker; inspect/integrate it, never reserve its first commit for this final step. Commit:
`$BATCH_ARTIFACT_FILES` is a bash ARRAY (not a plain string — a plain
space-joined string re-splits unpredictably under `set -f`/globbing and
diverges between bash and zsh, the #4109 word-splitting bug class):
```bash
COMMIT_DOCS=$(engineer_run query config-get commit_docs --raw 2>/dev/null || echo "true")
if [ "$COMMIT_DOCS" != "false" ]; then
  engineer_run query commit "docs(quick-batch-${BATCH_ID}): ${ITEM_COUNT} item(s)" --files "${BATCH_ARTIFACT_FILES[@]}"
fi
```

**Final report.** Re-load the batch (`engineer_run query quick-batch.resume --batch
"$BATCH_ID" --raw` — read-only in effect when nothing changed) and summarize
by status:

```
---
ENGINEER > QUICK BATCH ${ACTUAL_BATCH_STATUS}

Batch ${BATCH_ID}: ${ITEM_COUNT} item(s)
  Complete: ${complete_count}
  Failed: ${failed_count}${failed_count > 0 ? ' (' + failed_reasons + ')' : ''}
  Needs review: ${human_needed_count}
  Blocked: ${blocked_count}

{List each unfinished entry, source branch/path, reason, options and recommended recovery; no routine command handoff.}
---
```

If EVERY item is complete, report the actual delivery state separately. Otherwise preserve the batch/session and every incomplete source checkout, continue independent authorized entries, and list concrete remaining recovery or human action. A human-needed acceptance cannot be auto-approved. A failed item is resumed only after its cause is corrected and the stopped worker's committed/dirty handoff is reconciled; never restart an active or unknown assignment.

<step name="deliver_session">
When delivery is authorized, push the exact session branch without force, open/update its draft through `pr.open BRANCH --title TITLE --body-file BODY_FILE` using the full validated canonical PR template and read back provider state. First push opens the draft; every slice refreshes it. Observe actual `pr.checks BRANCH --timeout N` results, retaining pending/failure blockers. Reconcile every item's threats through real quick.threat-* APIs and _canonical-threat-tracking.md, including the complete planned checklist, Security risk schema, reviewed matches, rendered anchors and independent audit. No fake phase IDs.

A batch is not a verification target that can stand in for its entries. For each real QUICK_ID require canonical current verification.resolve-file/status/fingerprint/current --quick ID and the actual provider/check readiness gates. `pr.ready BRANCH --quick ID` checks that real quick scope; do not claim that one item proves the others. A batch with any uncovered entry remains draft. Merge requires actual aggregate entry coverage and an explicit human instruction, then `pr.merge BRANCH --quick ID --confirm` only when its real verification coverage supports the full branch. Never invent a phase to bypass this boundary. If the runtime cannot prove whole-branch coverage, preserve the draft and report that blocker.

After provider-confirmed merge, pr.sync reads remote state; session.close BRANCH runs only from another clean checkout whose HEAD contains session HEAD. Preserve dirty, active, blocked and unintegrated worktrees; never force cleanup.
</step>
