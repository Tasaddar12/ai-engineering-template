@~/.claude/engineer/references/response-language-directive.md

<purpose>
Insert a decimal phase for urgent work discovered mid-milestone between existing integer phases. Uses decimal numbering (72.1, 72.2, etc.) to preserve the logical sequence of planned phases while accommodating urgent insertions without renumbering the entire roadmap.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="parse_arguments">
Parse the command arguments:
- First argument: integer phase number to insert after
- Remaining arguments: phase description

Example: `/phase --insert 72 Fix critical auth bug`
-> after = 72
-> description = "Fix critical auth bug"

If arguments missing:

```
ERROR: Both phase number and description required
Usage: /phase --insert <after> <description>
Example: /phase --insert 72 Fix critical auth bug
```

Exit.

Validate first argument is an integer.
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
INIT=$(engineer_run query init.phase-op ${ENGINEER_WS:+--ws=${ENGINEER_WS##* }} "${after_phase}")
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
```

Check `roadmap_exists` from init JSON. If false:
```
ERROR: No roadmap found (.planning/ROADMAP.md)
```
Exit.
</step>

<step name="insert_phase">
**Delegate the phase insertion to `engineer_run query phase.insert`:**

```bash
RESULT=$(engineer_run query phase.insert "${after_phase}" "${description}")
```

The CLI handles:
- Verifying target phase exists in ROADMAP.md
- Calculating next decimal phase number (checking existing decimals on disk)
- Generating slug from description
- Creating the phase directory (`.planning/phases/{N.M}-{slug}/`)
- Inserting the phase entry into ROADMAP.md after the target phase with (INSERTED) marker

Extract from result: `phase_number`, `after_phase`, `name`, `slug`, `directory`.
</step>

<step name="update_project_state">
Update STATE.md to reflect the inserted phase via SDK handlers (never raw
`Edit`/`Write` — projects may ship a `protect-files.sh` PreToolUse hook that
blocks direct STATE.md writes):

1. Update STATE.md's next-phase pointer(s) to the newly inserted phase
   `{decimal_phase}`:

   ```bash
   engineer_run query state.patch '{"Current Phase":"{decimal_phase}","Next recommended run":"/plan-phase {decimal_phase}"}'
   ```

   (Adjust field names to whatever pointers STATE.md exposes — the handler
   reports which fields it matched.)

2. Append a Roadmap Evolution entry via the dedicated handler. It creates the
   `### Roadmap Evolution` subsection under `## Accumulated Context` if missing
   and dedupes identical entries:

   ```bash
   engineer_run query state.add-roadmap-evolution \
     --phase {decimal_phase} \
     --action inserted \
     --after {after_phase} \
     --note "{description}" \
     --urgent
   ```

   Expected response shape: `{ added: true, entry: "- Phase ... (URGENT)" }`
   (or `{ added: false, reason: "duplicate", entry: ... }` on replay).
</step>

<step name="completion">
Present completion summary:

```
Phase {decimal_phase} inserted after Phase {after_phase}:
- Description: {description}
- Directory: .planning/phases/{decimal-phase}-{slug}/
- Status: Not planned yet
- Marker: (INSERTED) - indicates urgent work

Roadmap updated: .planning/ROADMAP.md
Project state updated: .planning/STATE.md

---

## Next Up

**Phase {decimal_phase}: {description}** -- urgent insertion

`/clear` then:

`/plan-phase {decimal_phase}`

---

**Also available:**
- Review insertion impact: Check if Phase {next_integer} dependencies still make sense
- Review roadmap

---
```
</step>

</process>

<anti_patterns>

- Don't use this for planned work at end of milestone (use /phase without --insert)
- Don't insert before Phase 1 (decimal 0.1 makes no sense)
- Don't renumber existing phases
- Don't modify the target phase content
- Don't create plans yet (that's /plan-phase)
- Don't commit changes (user decides when to commit)
</anti_patterns>

<success_criteria>
Phase insertion is complete when:

- [ ] `engineer_run query phase.insert` executed successfully
- [ ] Phase directory created
- [ ] Roadmap updated with new phase entry (includes "(INSERTED)" marker)
- [ ] `engineer_run query state.add-roadmap-evolution ...` returned `{ added: true }` or `{ added: false, reason: "duplicate" }`
- [ ] `engineer_run query state.patch` returned matched next-phase pointer field(s)
- [ ] User informed of next steps and dependency implications
</success_criteria>
