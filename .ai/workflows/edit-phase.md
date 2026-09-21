<!-- workflow
step: edit-phase
agent-roles: orchestrator
produces: ROADMAP.md edit
consumes: ROADMAP.md, STATE.md
-->

<purpose>
Edit fields of an existing phase in ROADMAP.md in place. The phase number and
position are always preserved. In-progress and completed phases are guarded
unless `--force` is passed. Dependency references are validated before writing,
and a diff is shown for confirmation.
</purpose>

<required_reading>
@~/.ai/workflows/_session.snippet.md
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="parse_arguments">
Parse the command arguments:
- First argument: the phase number to edit (integer or decimal)
- Optional `--force`: allow editing an in-progress or completed phase

Examples:
- `/phase --edit 5` → phase = 5, force = false
- `/phase --edit 5 --force` → phase = 5, force = true
- `/phase --edit 12.1` → phase = 12.1

If no argument is provided:

```
ERROR: Phase number required
Usage: /phase --edit <phase-number> [--force]
Example: /phase --edit 5
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

Check `roadmap_exists`. If false:

```
ERROR: No roadmap found (.planning/ROADMAP.md)
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

<step name="load_phase">
Read the current phase entry:

```bash
PHASE_DATA=$(phase_run query roadmap.get-phase "${target}")
```

If the call fails with `phase-not-found`:

```
ERROR: Phase {target} not found in ROADMAP.md
Available phases can be seen with /progress.
```

Exit.

Extract from the result: `name`, `goal`, `depends_on`, `requirements`,
`status`, `plan_count`, `plans_complete`, `inserted`.
</step>

<step name="check_phase_status">
Determine the phase status from the loaded entry:

- `status` = `Complete` → completed
- `status` = `In progress` → in progress
- `status` = `Not started` → future

If the phase is in progress or completed AND `--force` was NOT passed:

```
ERROR: Cannot edit Phase {target} — status is {status}

Editing an in-progress or completed phase may invalidate executed plans.

To edit anyway, run:
  /phase --edit {target} --force
```

Exit.

If `--force` was passed for such a phase, continue and print:

```
WARNING: Editing Phase {target} which is {status}. Proceeding due to --force.
```
</step>

<step name="present_current_values">
Display the current phase fields:

```
Current values for Phase {target}: {name}

Title:        {name}
Goal:         {goal}
Depends on:   {depends_on or "(none)"}
Requirements: {requirements or "(none)"}
Plans:        {plans_complete}/{plan_count} complete
```

Then ask what to change. Use AskUserQuestion (header: "Edit"; question: "What
do you want to change for Phase {target}?"; options: "Specific fields" /
"Rewrite from a clarified intent" / "Cancel").
</step>

<step name="collect_edits">
**If the user cancelled:** exit cleanly without writing.

**If the user chose specific fields:** ask which of `title`, `goal`,
`depends_on`, `requirements` to change, then prompt for each new value showing
the current one. Only fields the user explicitly answers become updates; empty
answers preserve the existing value.

**If the user chose a rewrite:** ask for the revised intent, then derive a
concise `title`, a complete `goal` statement and updated `requirements` from it.
Preserve `depends_on` unless the user explicitly changed it.

Build an `updates` map of {field → new value}.
</step>

<step name="validate_depends_on">
If `depends_on` is being updated, validate every referenced phase number:

```bash
ALL_PHASES=$(phase_run query roadmap.analyze)
```

For each phase number referenced in the new `depends_on`:
- Normalize it (strip whitespace and any `Phase` prefix)
- Check it appears in the roadmap
- It must not reference the phase being edited

If any reference is invalid:

```
ERROR: depends_on references invalid phase(s): {bad_refs}
Valid phase numbers: {valid_list}
Fix the depends_on field and try again.
```

Exit without writing.
</step>

<step name="show_diff_and_confirm">
Show the old and new values for every field being changed:

```
Proposed changes to Phase {target}:

- Goal: {old_goal}
+ Goal: {new_goal}
- Depends on: {old_depends}
+ Depends on: {new_depends}

Apply these changes? (y/n):
```

Wait for confirmation. On `n`, exit without writing.
</step>

<step name="write_updated_phase">
**Delegate the in-place edit to `phase_run query phase.edit`.** Pass only the
fields that changed — the runtime preserves the number, position, success
criteria and plan checklist:

```bash
RESULT=$(phase_run query phase.edit "${target}" \
  --name "${new_title}" \
  --goal "${new_goal}" \
  --depends-on "${new_depends_on}" \
  --requirements "${new_requirements}")
```

Extract from the result: `phase_number`, `changed`.

When the title changed, the runtime also renames the phase directory to match
the new slug.

Verify the write by re-reading the entry, and confirm the number and plan
checklist are unchanged:

```bash
phase_run query roadmap.get-phase "${target}"
```

Then record the change in STATE.md:

```bash
phase_run query state.add-roadmap-evolution "Phase ${target} edited: ${changed_field_list}"
```
</step>

<step name="deliver_session">
This workflow owns the whole unit of work, so it delivers the session rather
than leaving it open. Follow the delivery sequence in
@~/.ai/workflows/_session.snippet.md exactly and in order: the empty-session
check, `git push -u`, `pr.open`, `pr.checks`, the merge confirmation, then
`pr.merge`, `pr.sync` and `session.close`.

Every command runs from `SESSION.worktree`.

**Title:** `Roadmap: edit phase ${phase_number}`

**Body:** each field that changed, with its before and after value, and the reason for the change. A roadmap edit is judged on intent, which the diff alone does not carry.

The `roadmap` session is shared across every roadmap edit, so a resumed one may already hold other changes. Describe every edit in the range.


Report the snippet's delivery line before the output below. A `failing` check
verdict, a declined merge or a preserved session are all reported as they stand
and none of them is worked around — a preserved session is unmerged work.
</step>

<step name="completion">
Present the completion summary:

```
Phase {target} updated in ROADMAP.md.

Fields changed: {changed_field_list}

---

## What's Next

- `/progress` — view the updated roadmap
- `/discuss-phase {target}` — discuss the implementation approach
- `/plan-phase {target}` — re-plan this phase if its scope moved

---
```
</step>

</process>

<anti_patterns>
- Don't renumber the phase — number and position must be preserved exactly
- Don't modify other phases when editing one
- Don't skip depends_on validation; invalid references block the write
- Don't write without showing a diff and getting confirmation
- Don't edit in-progress or completed phases without `--force`
- Don't use raw `Write` on ROADMAP.md — `phase.edit` replaces the entry in place
- Don't change the phase directory by hand; the runtime renames it with the title
- Don't finish with the session still open — an undelivered session is
  work on a branch nobody merged
- Don't merge past a `failing` or `pending` check verdict, and don't
  `--force` a preserved session away
</anti_patterns>

<success_criteria>
- [ ] Phase {target} found and loaded from ROADMAP.md
- [ ] Status check performed; in-progress/completed blocked without `--force`
- [ ] Current values presented to the user
- [ ] depends_on references validated
- [ ] Diff shown and confirmed
- [ ] `phase_run query phase.edit` applied the change in place
- [ ] Number, position and plan checklist preserved
- [ ] STATE.md Roadmap Evolution updated
- [ ] User informed of next steps
- [ ] Session delivered: pull request opened, its check verdict judged,
      the merge confirmed, and the session closed or its preservation
      reported
</success_criteria>
