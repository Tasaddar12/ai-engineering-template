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
@~/.ai/workflows/_session.snippet.md
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

<step name="open_session">
Open the worktree this work lives in, before writing anything. Read
@~/.ai/workflows/_session.snippet.md for the full contract.

```bash
SESSION=$(phase_run query session.open milestone "roadmap")
```

Parse `worktree`, `branch`, `base`, `reused` and `synced`. **Run every
subsequent command in this workflow from `worktree`.** An open session for
roadmap changes is reused rather than replaced, so the work accumulates onto one branch
and arrives as one pull request.

Report it in one line:

```
Session: {branch} ({reused ? "resumed" : "opened"}) at {worktree}
```

If the verb fails, **stop and report its message**. It means isolation could not
be established, and continuing in the invoking checkout is the one outcome this
project does not allow — the dispatch guard would block the write anyway.
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

<step name="deliver_session">
This workflow owns the whole unit of work, so it delivers the session rather
than leaving it open. Follow the delivery sequence in
@~/.ai/workflows/_session.snippet.md exactly and in order: the empty-session
check, `git push -u`, `pr.open`, `pr.checks`, the merge confirmation, then
`pr.merge`, `pr.sync` and `session.close`.

Every command runs from `SESSION.worktree`.

**Title:** `Roadmap: insert phase ${phase_number} ${phase_name}`

**Body:** the phase that was inserted, where it landed, and what it depends on. If insertion renumbered later phases, say which ones — that is the part a reviewer most needs to see.

The `roadmap` session is shared across every roadmap edit, so a resumed one may already hold other changes. Describe every edit in the range.


Report the snippet's delivery line before the output below. A `failing` check
verdict, a declined merge or a preserved session are all reported as they stand
and none of them is worked around — a preserved session is unmerged work.
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
- Don't finish with the session still open — an undelivered session is
  work on a branch nobody merged
- Don't merge past a `failing` or `pending` check verdict, and don't
  `--force` a preserved session away
</anti_patterns>

<success_criteria>
- [ ] `phase_run query phase.insert` executed successfully
- [ ] Phase directory created
- [ ] Roadmap updated with the new entry, carrying the `(INSERTED)` marker
- [ ] STATE.md Roadmap Evolution updated
- [ ] User informed of next steps and dependency implications
- [ ] Session delivered: pull request opened, its check verdict judged,
      the merge confirmed, and the session closed or its preservation
      reported
</success_criteria>
