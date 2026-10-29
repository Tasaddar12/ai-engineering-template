@~/.claude/engineer/references/response-language-directive.md

<purpose>
Add a new integer phase to the end of the current milestone in the roadmap. Automatically calculates next phase number, creates phase directory, and updates roadmap structure.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="parse_arguments">
Parse the command arguments:
- All arguments become the phase description
- Example: `/phase "Add authentication"` → description = "Add authentication"
- Example: `/phase "Fix critical performance issues"` → description = "Fix critical performance issues"

If no arguments provided:

```
ERROR: Phase description required
Usage: /phase "<description>"
Example: /phase "Add authentication system"
```

Exit.
</step>

<step name="init_context">
Load phase operation context:

```bash
IFS= read -rd '' ENGINEER_ARGS <<'ENGINEER_ARGS_END' || true
$ARGUMENTS
ENGINEER_ARGS_END
ENGINEER_ARGS=${ENGINEER_ARGS%$'\n'}
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
  _engineer_path_escaped=$(printf '%s' "${ENGINEER_RUN%/*}" | LC_ALL=C sed 's/[\\`"$]/\\&/g')
  printf 'export PATH="%s:$PATH"\n' "$_engineer_path_escaped" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true
fi
ENGINEER_WS=$(echo " $ENGINEER_ARGS" | sed -nE 's/.* --ws +([A-Za-z0-9][A-Za-z0-9._-]*).*/--ws \1/p' | head -n 1)
INIT=$(engineer_run query init.phase-op ${ENGINEER_WS:+--ws=${ENGINEER_WS##* }} "0")
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
```

Check `roadmap_exists` from init JSON. If false:
```
ERROR: No roadmap found (.planning/ROADMAP.md)
Run /new-project to initialize.
```
Exit.
</step>

<step name="add_phase">
**Delegate the phase addition to `engineer_run query phase.add`:**

```bash
RESULT=$(engineer_run query phase.add "${description}")
```

The CLI handles:
- Finding the highest existing integer phase number
- Calculating next phase number (max + 1)
- Generating slug from description
- Creating the phase directory (`.planning/phases/{NN}-{slug}/`)
- Inserting the phase entry into ROADMAP.md with Goal, Depends on, and Plans sections

Extract from result: `phase_number`, `padded`, `name`, `slug`, `directory`.

**If result includes a `warning` field:** the description read as goal-shaped (long and/or multi-sentence) rather than title-shaped, and was written verbatim as the `### Phase N:` header. The phase was still created — surface the warning to the user and suggest a short title with the detail moved to `**Goal:**` in ROADMAP.md.
</step>

<step name="update_project_state">
Update STATE.md to reflect the new phase:

1. Read `.planning/STATE.md`
2. Under "## Accumulated Context" → "### Roadmap Evolution" add entry:
   ```
   - Phase {N} added: {description}
   ```

If "Roadmap Evolution" section doesn't exist, create it.
</step>

<step name="completion">
Present completion summary:

```
Phase {N} added to current milestone:
- Description: {description}
- Directory: .planning/phases/{phase-num}-{slug}/
- Status: Not planned yet

Roadmap updated: .planning/ROADMAP.md

---

## ▶ Next Up — [${PROJECT_CODE}] ${PROJECT_TITLE}

**Phase {N}: {description}**

`/clear` then:

`/plan-phase {N}`

---

**Also available:**
- `/phase "<description>"` — add another phase
- Review roadmap

---
```
</step>

</process>

<success_criteria>
- [ ] `engineer_run query phase.add` executed successfully
- [ ] Phase directory created
- [ ] Roadmap updated with new phase entry
- [ ] STATE.md updated with roadmap evolution note
- [ ] User informed of next steps
</success_criteria>
