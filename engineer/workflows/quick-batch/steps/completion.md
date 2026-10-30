**Step 9: Completion**

For every item that merged successfully in Step 7 AND (NOT `$VALIDATE_MODE`,
OR Step 8 routed it to `complete`): call `quick-batch complete`. The runtime
first records a durable `completionTransaction` intent in `BATCH.json`, then
updates that item's authoritative `QUICK.md` status and commit, and finalizes
the batch record. If interrupted between those writes, `quick-batch resume`
replays the recorded intent after checking the completion evidence. Repeating
completion for an already-complete item is a no-op:

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
engineer_run quick-batch complete \
  --batch "$BATCH_ID" \
  --quick-id "$quick_id" \
  --description "$description" \
  --date "$date" \
  --commit "$commit_hash" \
  --directory "$ITEM_DIR" \
  --raw
```

Items NOT reaching this call — `human_needed`, `failed` (planner/checker/
merge/verification failure), or still `blocked`/`pending` (a dependency
failed, row 32) — remain at their respective batch status. They do not receive
a completion intent or a `complete` status in `QUICK.md`; preserve a worktree
where applicable.

**Final commit.** Stage every artifact produced this run (PLAN.md, SUMMARY.md,
`--research` RESEARCH.md, `--validate` VERIFICATION.md, each affected task
`QUICK.md`, and the batch `BATCH.json`) and commit:
`$BATCH_ARTIFACT_FILES` is a bash ARRAY (not a plain string — a plain
space-joined string re-splits unpredictably under `set -f`/globbing and
diverges between bash and zsh, the word-splitting bug class):
```bash
COMMIT_DOCS=$(engineer_run query config-get commit_docs --raw 2>/dev/null || echo "true")
if [ "$COMMIT_DOCS" != "false" ]; then
  git add "${BATCH_ARTIFACT_FILES[@]}" 2>/dev/null
  engineer_run query commit "docs(quick-batch-${BATCH_ID}): ${ITEM_COUNT} item(s)" --files "${BATCH_ARTIFACT_FILES[@]}"
fi
```

**Final report.** Re-load the batch (`engineer_run quick-batch resume --batch
"$BATCH_ID" --raw` — read-only in effect when nothing changed) and summarize
by status:

```
---
Engineer > QUICK BATCH COMPLETE

Batch ${BATCH_ID}: ${ITEM_COUNT} item(s)
  Complete: ${complete_count}
  Failed: ${failed_count}${failed_count > 0 ? ' (' + failed_reasons + ')' : ''}
  Needs review: ${human_needed_count}
  Blocked: ${blocked_count}

${failed_count + human_needed_count > 0 ? 'Resume after resolving: /quick-batch --resume ' + BATCH_ID : ''}
---
```

If EVERY item is `complete`, this is a clean finish — no further action
needed. If any item is `failed`/`human_needed`/`blocked`, the batch stays
resumable: fix the underlying issue (or accept the failure), then re-run
`/quick-batch --resume ${BATCH_ID}` — `resumeBatch`'s own propagation
(unmodified from Phase 3) re-evaluates eligibility from the current state, no
special quick-batch-side recovery logic needed.
