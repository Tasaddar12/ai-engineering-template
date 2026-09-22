<!-- workflow
step: complete-milestone
agent-roles: orchestrator
produces: MILESTONES.md entry, ROADMAP.md shipped markers, STATE.md update,
  STATE.md Deferred Items rows, REQUIREMENTS.md status for deferred scope
consumes: ROADMAP.md, STATE.md, phase SUMMARY.md files
-->

<purpose>
Close a milestone: confirm every phase in it is genuinely complete, gather what
shipped, write the MILESTONES.md entry, mark the milestone shipped in the
roadmap, and commit.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="init_context">
Parse `$ARGUMENTS`: an optional milestone version/name. When absent, the current
in-progress milestone is used.

```bash
_root="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
for _c in "$_root"/.{ai,claude,codex}/runtime/phase.py "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/runtime/phase.py "${CODEX_HOME:-$HOME/.codex}"/runtime/phase.py; do
  [ -f "$_c" ] && PHASE_RUNTIME="$_c" && break
done
[ -n "${PHASE_RUNTIME:-}" ] || { echo "ERROR: phase runtime not found; run the installer." >&2; exit 1; }
phase_run() { "$(command -v python3 || command -v python)" "$PHASE_RUNTIME" "$@"; }
INIT=$(phase_run query init.complete-milestone "${VERSION}")
```

Extract: `target_milestone`, `milestone_phases`, `incomplete_phases`,
`ready_to_complete`, `commit_docs`, `text_mode`, `response_language`, `paths`.

**If `response_language` is set:** all user-facing output MUST be presented in
`{response_language}`.

If `target_milestone` is empty:

```
No milestone is currently in progress.
Declare one with `/new-milestone "<name>"`, or name the milestone to close.
```

Exit.
</step>

<step name="pre_close_artifact_audit">
Audit the milestone's phases for missing artifacts before claiming completion.
For each phase in `milestone_phases`:

```bash
phase_run query init.phase-op "${PHASE_NUMBER}"
```

Check that `plan_count` and `summary_count` agree, and that
`has_verification` is true where the project verifies phases.

Report every gap found:

```
Artifact gaps before close:
- Phase {N}: {plan_count} plans, {summary_count} summaries
- Phase {M}: no VERIFICATION.md
```

A phase whose plans are ticked in the roadmap but which has no summaries did not
actually execute — say so plainly rather than closing over it.
</step>

<step name="verify_readiness">
If `ready_to_complete` is false:

```
Cannot close {target_milestone} — phases still open: {incomplete_phases}

Finish or remove them first:
- `/next` to continue the earliest open phase
- `/phase --remove {N}` to drop work that is no longer wanted
```

Exit. Do not offer a force path: a milestone entry claiming phases shipped when
they did not is exactly the record this workflow exists to keep honest.
</step>

<step name="gather_stats">
Collect the numbers for the entry:

```bash
git log --oneline --since="{milestone start date}" | wc -l
git diff --stat {first milestone commit}..HEAD | tail -1
```

Take phase and plan counts from `milestone_phases` rather than counting by hand.
</step>

<step name="extract_accomplishments">
Read the `**Delivered:**` line (or the leading heading) from each phase
SUMMARY.md in the milestone. These become the entry's key accomplishments. The
runtime extracts the same lines; use its list and edit it for readability rather
than inventing achievements.
</step>

<step name="archive_milestone">
**Delegate the close to the runtime:**

```bash
ARCHIVE=$(phase_run query milestone.complete "${VERSION}" --name "${NAME}" --confirm)
```

`--confirm` is required; the runtime refuses without it. It:
- Re-checks that every phase in the milestone is complete and refuses otherwise
- Marks the milestone shipped in the roadmap's `## Milestones` list and section
- Writes the MILESTONES.md entry, creating the file if needed, newest first

Extract: `version`, `name`, `date`, `phases`, `plans`, `accomplishments`,
`archived`.
</step>

<step name="review_entry">
Read the generated MILESTONES.md entry and improve its prose — the runtime
produces accurate structure, not good writing. Keep every fact it recorded;
rewrite the `**Delivered:**` line and the accomplishments so a reader who was not
present understands what shipped.

Add `**What's next:**` describing the next milestone's goals, or "Project
complete".
</step>

<step name="record_deferrals">
Scope that was acknowledged and not delivered is deferred, not dropped and not
struck through. Write each one to the Deferred Items table so it survives the
milestone close in a form the next milestone can read:

```bash
phase_run query state.add-deferred "{category}" "{item}" \
  --status Deferred --milestone "${VERSION}"
```

Where the deferred scope has a requirement id, say so in REQUIREMENTS.md too, so
the Traceability table does not leave it reading `Pending` indefinitely:

```bash
phase_run query requirements.set-status "{REQ-ID}" Deferred
```

Deferring is a decision about scope. Confirm the list with the user before
writing it; do not infer a deferral from a phase that simply did not mention a
requirement.
</step>

<step name="update_state">
```bash
phase_run query state.record-session --stopped-at "Milestone ${VERSION} shipped" --status "Milestone complete"
phase_run query state.add-decision "Milestone ${VERSION} (${NAME}) shipped ${DATE}: phases ${PHASES}" \
  --rationale "Milestone close" --outcome "Shipped"
```

`state.add-decision` records the decision in PROJECT.md's Key Decisions table as
well as the digest, so it survives the digest being trimmed.
</step>

<step name="git_commit">
```bash
phase_run query commit "docs(milestone): ship ${VERSION} ${NAME}" \
  --files .planning/MILESTONES.md .planning/ROADMAP.md .planning/STATE.md \
  .planning/PROJECT.md .planning/REQUIREMENTS.md
```

Then report drift, warn-only:

```bash
phase_run query planning.validate
```

A milestone close is the natural point to see the records' shape. Present the
warnings; fixing them is separate work, not part of the close.
</step>

<step name="offer_next">
```
Milestone shipped: {version} {name} ({date})

Phases: {phases}
Plans: {plans}
Recorded: .planning/MILESTONES.md

---

## What's Next

- `/new-milestone "<name>"` — start the next cycle
- `/progress` — where the project stands now
- Nothing further, if the project is complete

---
```
</step>

</process>

<anti_patterns>
- Don't close a milestone with open phases; there is no force path for a reason
- Don't write the MILESTONES.md entry by hand — `milestone.complete` owns its structure
- Don't claim accomplishments that no SUMMARY.md supports
- Don't delete phase directories on close; they are the evidence behind the entry
- Don't renumber phases — numbering stays continuous across milestones
</anti_patterns>

<success_criteria>
- [ ] Artifact audit run and any gaps reported
- [ ] Every phase in the milestone confirmed complete
- [ ] `milestone.complete` executed with `--confirm`
- [ ] MILESTONES.md entry written and its prose reviewed
- [ ] Roadmap shows the milestone shipped
- [ ] STATE.md updated and everything committed
- [ ] User knows the next step
</success_criteria>
