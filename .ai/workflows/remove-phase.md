<!-- workflow
step: remove-phase
agent-roles: orchestrator
produces: ROADMAP.md edit, removed phase directory
consumes: ROADMAP.md, STATE.md
-->

<purpose>
Remove an unstarted future phase from the roadmap, delete its directory, renumber
subsequent phases to keep a clean linear sequence, and commit the change. The git
commit is the historical record of the removal.
</purpose>

<required_reading>
@~/.ai/workflows/_session.snippet.md
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="parse_arguments">
Parse the command arguments:
- The argument is the phase number to remove (integer or decimal)
- `--force` removes a phase that has completed plans or artifacts
- `--no-renumber` leaves later phases at their current numbers

Examples:
- `/phase --remove 17` → phase = 17
- `/phase --remove 16.1` → phase = 16.1

If no argument is provided:

```
ERROR: Phase number required
Usage: /phase --remove <phase-number> [--force] [--no-renumber]
Example: /phase --remove 17
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
INIT=$(phase_run query init.phase-op "${target}")
```

Extract: `phase_found`, `phase_dir`, `phase_number`, `phase_name`, `status`,
`plans_complete`, `summary_count`, `commit_docs`, `roadmap_exists`, `state`.

If `phase_found` is false:

```
ERROR: Phase {target} not found in roadmap.
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

<step name="validate_future_phase">
Verify the phase is a future phase, not started:

1. Compare the target phase to the current phase from `state.position.Phase`
2. The target must be later than the current phase
3. `plans_complete` must be 0 and `summary_count` must be 0

If the target is the current or an earlier phase:

```
ERROR: Cannot remove Phase {target}

Only future phases can be removed:
- Current phase: {current}
- Phase {target} is current or completed

To abandon current work, stop the phase instead of removing it.
```

Exit.
</step>

<step name="confirm_removal">
Present the removal summary and confirm:

```
Removing Phase {target}: {phase_name}

This will:
- Delete: {phase_dir}
- Renumber subsequent phases (unless --no-renumber)
- Update: ROADMAP.md, STATE.md

Proceed? (y/n)
```

Wait for confirmation. Do not proceed on anything other than an explicit yes.
</step>

<step name="execute_removal">
**Delegate the whole removal to `phase_run query phase.remove`:**

```bash
RESULT=$(phase_run query phase.remove "${target}")
```

If the phase has completed plans or a non-empty directory, the runtime refuses.
Pass `--force` only when the user has confirmed that specifically:

```bash
RESULT=$(phase_run query phase.remove "${target}" --force)
```

The runtime handles:
- Deleting the phase directory
- Renumbering later phases and renaming their directories and artifact files
- Updating ROADMAP.md: removing the section, the checklist entry, renumbering
  phase references and plan ids, and refreshing the Progress table

Extract from the result: `removed`, `name`, `directory`, `renumbered`.
</step>

<step name="commit">
Stage and commit the removal. The commit message preserves the record of what
was removed:

```bash
phase_run query commit "chore(roadmap): remove phase ${removed} (${name})" --files .planning
```
</step>

<step name="deliver_session">
This workflow owns the whole unit of work, so it delivers the session rather
than leaving it open. Follow the delivery sequence in
@~/.ai/workflows/_session.snippet.md exactly and in order: the empty-session
check, `git push -u`, `pr.open`, `pr.checks`, the merge confirmation, then
`pr.merge`, `pr.sync` and `session.close`.

Every command runs from `SESSION.worktree`.

**Title:** `Roadmap: remove phase ${phase_number}`

**Body:** the phase that was removed and why, plus any renumbering the removal caused and any dependency that had to be repointed. Removal is the roadmap edit most likely to surprise a reviewer, so state its consequences plainly.

The `roadmap` session is shared across every roadmap edit, so a resumed one may already hold other changes. Describe every edit in the range.


Report the snippet's delivery line before the output below. A `failing` check
verdict, a declined merge or a preserved session are all reported as they stand
and none of them is worked around — a preserved session is unmerged work.
</step>

<step name="completion">
Present the completion summary:

```
Phase {removed} ({name}) removed.

Changes:
- Deleted: {directory}
- Renumbered: {count} phase(s)
- Updated: ROADMAP.md, STATE.md
- Committed: chore(roadmap): remove phase {removed} ({name})

---

## What's Next

- `/progress` — see updated roadmap status
- Continue with the current phase
- Review the roadmap

---
```
</step>

</process>

<anti_patterns>
- Don't remove completed phases (those with SUMMARY.md files) without `--force`
- Don't remove the current or past phases
- Don't renumber by hand — `phase.remove` owns renumbering of directories, files and references
- Don't add "removed phase" notes to STATE.md — the git commit is the record
- Don't modify completed phase directories
- Don't finish with the session still open — an undelivered session is
  work on a branch nobody merged
- Don't merge past a `failing` or `pending` check verdict, and don't
  `--force` a preserved session away
</anti_patterns>

<success_criteria>
- [ ] Target phase validated as future and unstarted
- [ ] User confirmed the removal
- [ ] `phase_run query phase.remove` executed successfully
- [ ] Change committed with a descriptive message
- [ ] User informed of changes
- [ ] Session delivered: pull request opened, its check verdict judged,
      the merge confirmed, and the session closed or its preservation
      reported
</success_criteria>
