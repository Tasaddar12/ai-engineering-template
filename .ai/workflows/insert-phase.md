<!-- workflow
step: insert-phase
agent-roles: orchestrator
produces: ROADMAP.md entry, phase directory
consumes: ROADMAP.md, STATE.md
-->

<purpose>
Insert a decimal phase for urgent work discovered mid-milestone, between existing
integer phases. Decimal numbering (2.1, 2.2, …) preserves the logical sequence of
planned phases while accommodating urgent insertions without renumbering the
whole roadmap.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="parse_arguments">
Parse the command arguments:
- First argument: the phase number to insert after
- Remaining arguments: the phase description
- `--goal "<text>"` optionally supplies the goal

Example: `/phase --insert 2 "Rotate leaked key" --goal "Emergency credential rotation"`
→ after = 2, description = "Rotate leaked key"

If arguments are missing:

```
ERROR: Both phase number and description required
Usage: /phase --insert <after> <description> [--goal "<goal>"]
Example: /phase --insert 2 "Fix critical auth bug"
```

Exit.

Validate the first argument is a phase number.
</step>

<step name="init_context">
Load phase operation context:

```bash
_root="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
for _c in "$_root"/.{ai,claude,codex}/runtime/phase.py "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/runtime/phase.py "${CODEX_HOME:-$HOME/.codex}"/runtime/phase.py; do
  [ -f "$_c" ] && PHASE_RUNTIME="$_c" && break
done
[ -n "${PHASE_RUNTIME:-}" ] || { echo "ERROR: phase runtime not found; run the installer." >&2; exit 1; }
phase_run() { "$(command -v python3 || command -v python)" "$PHASE_RUNTIME" "$@"; }
INIT=$(phase_run query init.phase-op "${after_phase}")
```

Check `roadmap_exists` from the init JSON. If false:

```
ERROR: No roadmap found (.planning/ROADMAP.md)
```

Exit.

Check `phase_found`. If false:

```
ERROR: Phase {after_phase} not found in roadmap.
Use /progress to see available phases.
```

Exit.
</step>

<step name="insert_phase">
**Delegate the insertion to `phase_run query phase.insert`:**

```bash
RESULT=$(phase_run query phase.insert "${after_phase}" "${description}" --goal "${goal}")
```

The runtime handles:
- Verifying the target phase exists in ROADMAP.md
- Calculating the next decimal phase number from existing decimals
- Generating the slug from the description
- Creating the phase directory (`.planning/phases/{NN.M}-{slug}/`)
- Inserting the phase entry after the target phase with the `(INSERTED)` marker
- Refreshing the Progress table

Extract from the result: `phase_number`, `after`, `name`, `slug`, `directory`.
</step>

<step name="update_project_state">
Record the insertion in STATE.md through the runtime, never with a raw
`Edit`/`Write`:

```bash
phase_run query state.add-roadmap-evolution "Phase ${phase_number} inserted after Phase ${after} (URGENT): ${description}"
```
</step>

<step name="commit">
```bash
phase_run query commit "docs(roadmap): insert phase ${phase_number}" --files .planning/ROADMAP.md .planning/STATE.md
```
</step>

<step name="completion">
Present the completion summary:

```
Phase {phase_number} inserted after Phase {after}:
- Title: {name}
- Directory: {directory}
- Status: Not planned yet
- Marker: (INSERTED) — indicates urgent work

Roadmap updated: .planning/ROADMAP.md

---

## ▶ Next Up

**Phase {phase_number}: {name}** — urgent insertion

`/clear` then:

`/discuss-phase {phase_number}`

---

**Also available:**
- Review insertion impact: check whether the following phase's dependencies still hold
- Review the roadmap

---
```
</step>

</process>

<anti_patterns>
- Don't use this for planned work at the end of a milestone — use `/phase <description>`
- Don't insert before Phase 1 (decimal 0.1 makes no sense)
- Don't renumber existing phases — insertion exists precisely to avoid that
- Don't modify the target phase's content
- Don't create plans yet — that is `/plan-phase`
</anti_patterns>

<success_criteria>
- [ ] `phase_run query phase.insert` executed successfully
- [ ] Phase directory created
- [ ] Roadmap updated with the new entry, carrying the `(INSERTED)` marker
- [ ] STATE.md Roadmap Evolution updated
- [ ] User informed of next steps and dependency implications
</success_criteria>
