**Step 2b: Create a new batch (only when `$RESUME_BATCH_ID` is empty)**

Skip this step entirely if `$RESUME_BATCH_ID` is set (resume-mode.md owns
that path instead).

**Get the task list.** If `--file <path>` was present in `$ARGUMENTS`, use its
value as `$TASK_FILE`. Otherwise the remaining, non-flag text of `$ARGUMENTS`
IS the inline task list (a bulleted/numbered list, ≥2 items — the same
grammar `parseTaskList` enforces).

If `$TASK_FILE` is set:
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
QB_CREATE_JSON=$(engineer_run quick-batch create --file "$TASK_FILE" --base-revision "$(git rev-parse HEAD)" --raw)
```

Otherwise, the inline list must land on disk first — `quick-batch create`
only accepts `--file` (path-confined, same as `/quick-batch`'s own
security posture): write it to a scratch file under `.planning/` before
calling the verb.
```bash
TASK_FILE="${quick_dir%/quick}/.quick-batch-task-list.tmp"
mkdir -p "$(dirname "$TASK_FILE")"
printf '%s\n' "$INLINE_TASK_LIST" > "$TASK_FILE"
QB_CREATE_JSON=$(engineer_run quick-batch create --file "$TASK_FILE" --base-revision "$(git rev-parse HEAD)" --raw)
rm -f "$TASK_FILE"
```

```bash
QB_CREATE_RC=$?
if [[ "$QB_CREATE_JSON" == @file:* ]]; then QB_CREATE_JSON=$(cat "${QB_CREATE_JSON#@file:}"); fi
```

**If `$QB_CREATE_RC` is non-zero:** the task list failed to parse (fewer than
2 items — row 2/12) or the dependency DAG was invalid. Print the CLI's error
message verbatim and STOP. Do not dispatch anything.

**Otherwise:** parse `$QB_CREATE_JSON` for `batchId` and `manifest` (every
item starts `pending`, wave `0` — no dependency/file-overlap signal exists
yet before planning; this is expected, not a bug, per the design's negative-
space note).

```bash
BATCH_ID="$batchId"
BATCH_MANIFEST_JSON=$(printf '%s' "$QB_CREATE_JSON" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{const j=JSON.parse(s);process.stdout.write(JSON.stringify(j.manifest))}catch{process.stdout.write("")}})')
ITEM_COUNT=$(printf '%s' "$BATCH_MANIFEST_JSON" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{const j=JSON.parse(s);process.stdout.write(String(j.items.length))}catch{process.stdout.write("0")}})')
```

Report to user:
```
Creating quick batch ${BATCH_ID}: ${ITEM_COUNT} item(s).
Manifest: .planning/quick-batches/${BATCH_ID}/BATCH.json
```

Continue to Step 3 in `quick-batch.md`.
