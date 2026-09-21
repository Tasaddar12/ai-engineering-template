<!-- workflow
step: add-phase
agent-roles: orchestrator
produces: ROADMAP.md entry, phase directory
consumes: ROADMAP.md, STATE.md
-->

<purpose>
Add a new integer phase to the end of the current milestone in the roadmap. The
runtime calculates the next phase number, creates the phase directory and
updates the roadmap structure.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="parse_arguments">
Parse the command arguments:
- All positional arguments become the phase title
- `--goal "<text>"` supplies the phase goal; when absent the title is reused as the goal
- `--requirements REQ-01,REQ-02` optionally links requirement ids

Examples:
- `/phase add "API Key Session hardening" --goal "IDP-managed API key sessions"`
- `/phase Add authentication`

If no description is provided:

```
ERROR: Phase description required
Usage: /phase <description> [--goal "<goal>"] [--requirements REQ-01,REQ-02]
Example: /phase "Add authentication system" --goal "Users sign in with an IDP"
```

Exit.
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
INIT=$(phase_run query init.phase-op 0)
```

Check `roadmap_exists` from the init JSON. If false:

```
ERROR: No roadmap found (.planning/ROADMAP.md)
Run onboarding to initialize the project.
```

Exit.

**If `response_language` is set:** all user-facing output of this workflow —
narration, status updates, questions and explanations — MUST be presented in
`{response_language}`. Technical terms, code, file paths and subagent prompts
stay in English.
</step>

<step name="add_phase">
**Delegate the phase addition to `phase_run query phase.add`:**

```bash
RESULT=$(phase_run query phase.add "${description}" --goal "${goal}")
```

The runtime handles:
- Finding the highest existing phase number
- Calculating the next integer phase number (max + 1)
- Generating the slug from the description
- Creating the phase directory (`.planning/phases/{NN}-{slug}/`)
- Inserting the phase entry into ROADMAP.md with Goal, Depends on and Plans sections
- Adding the overview checklist entry and refreshing the Progress table

Extract from the result: `phase_number`, `padded`, `name`, `slug`, `goal`, `directory`.

**If the result includes a `warning` field:** the description read as goal-shaped
(long and/or multi-sentence) rather than title-shaped, and was written verbatim
as the `### Phase N:` header. The phase was still created — surface the warning
and suggest a short title with the detail moved to `**Goal**:` in ROADMAP.md.
</step>

<step name="update_project_state">
Record the roadmap change in STATE.md through the runtime, never with a raw
`Edit`/`Write` — projects may ship a PreToolUse hook that blocks direct writes
to planning records:

```bash
phase_run query state.add-roadmap-evolution "Phase ${phase_number} added: ${description}"
```

The handler creates the `### Roadmap Evolution` subsection under
`## Accumulated Context` when it is missing and skips duplicate entries.
</step>

<step name="commit">
Commit the roadmap and state change:

```bash
phase_run query commit "docs(roadmap): add phase ${padded}" --files .planning/ROADMAP.md .planning/STATE.md
```

The runtime respects `commit_docs` in `.planning/config.yaml` and skips ignored
paths automatically.
</step>

<step name="completion">
Present the completion summary:

```
Phase {phase_number} added to the current milestone:
- Title: {name}
- Goal: {goal}
- Directory: {directory}
- Status: Not planned yet

Roadmap updated: .planning/ROADMAP.md

---

## ▶ Next Up

**Phase {phase_number}: {name}** — {goal}

`/clear` then:

`/discuss-phase {phase_number}`

---

**Also available:**
- `/phase <description>` — add another phase
- `/plan-phase {phase_number}` — plan without discussing first
- Review the roadmap

---
```
</step>

</process>

<anti_patterns>
- Don't hand-edit ROADMAP.md — `phase.add` owns numbering, the checklist and the Progress table
- Don't invent a phase number; the runtime derives it from existing phases
- Don't create plans yet — that is `/plan-phase`
- Don't write STATE.md directly — use `state.add-roadmap-evolution`
</anti_patterns>

<success_criteria>
- [ ] `phase_run query phase.add` executed successfully
- [ ] Phase directory created
- [ ] Roadmap updated with the new phase entry and checklist line
- [ ] STATE.md Roadmap Evolution updated
- [ ] Change committed (unless `commit_docs` is false)
- [ ] User informed of next steps
</success_criteria>
