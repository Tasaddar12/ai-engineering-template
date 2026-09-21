<!-- workflow
step: complete-milestone
agent-roles: orchestrator
produces: MILESTONES.md entry, ROADMAP.md shipped markers, STATE.md update
consumes: ROADMAP.md, STATE.md, phase SUMMARY.md files
-->

<purpose>
Close a milestone: confirm every phase in it is genuinely complete, gather what
shipped, write the MILESTONES.md entry, mark the milestone shipped in the
roadmap, and commit.
</purpose>

<required_reading>
@~/.ai/workflows/_session.snippet.md
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

<step name="open_session">
Open the worktree this work lives in, before writing anything. Read
@~/.ai/workflows/_session.snippet.md for the full contract.

```bash
SESSION=$(phase_run query session.open milestone "${VERSION}")
```

Parse `worktree`, `branch`, `base`, `reused` and `synced`. **Run every
subsequent command in this workflow from `worktree`.** An open session for
this milestone is reused rather than replaced, so the work accumulates onto one branch
and arrives as one pull request.

Report it in one line:

```
Session: {branch} ({reused ? "resumed" : "opened"}) at {worktree}
```

If the verb fails, **stop and report its message**. It means isolation could not
be established, and continuing in the invoking checkout is the one outcome this
project does not allow — the dispatch guard would block the write anyway.
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

<step name="update_state">
```bash
phase_run query state.record-session --stopped-at "Milestone ${VERSION} shipped" --status "Milestone complete"
phase_run query state.add-decision "Milestone ${VERSION} (${NAME}) shipped ${DATE}: phases ${PHASES}"
```
</step>

<step name="git_commit">
```bash
phase_run query commit "docs(milestone): ship ${VERSION} ${NAME}" \
  --files .planning/MILESTONES.md .planning/ROADMAP.md .planning/STATE.md
```
</step>

<step name="deliver_session">
This workflow owns the whole unit of work, so it delivers the session rather
than leaving it open. Follow the delivery sequence in
@~/.ai/workflows/_session.snippet.md exactly and in order: the empty-session
check, `git push -u`, `pr.open`, `pr.checks`, the merge confirmation, then
`pr.merge`, `pr.sync` and `session.close`.

Every command runs from `SESSION.worktree`.

**Title:** `Complete milestone ${VERSION}`

**Body:** what the milestone delivered, the phases it closed, and what verification confirmed. Carry over any gap the archive recorded as accepted, with the reason it was accepted rather than closed.


Report the snippet's delivery line before the output below. A `failing` check
verdict, a declined merge or a preserved session are all reported as they stand
and none of them is worked around — a preserved session is unmerged work.
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
- Don't finish with the session still open — an undelivered session is
  work on a branch nobody merged
- Don't merge past a `failing` or `pending` check verdict, and don't
  `--force` a preserved session away
</anti_patterns>

<success_criteria>
- [ ] Artifact audit run and any gaps reported
- [ ] Every phase in the milestone confirmed complete
- [ ] `milestone.complete` executed with `--confirm`
- [ ] MILESTONES.md entry written and its prose reviewed
- [ ] Roadmap shows the milestone shipped
- [ ] STATE.md updated and everything committed
- [ ] User knows the next step
- [ ] Session delivered: pull request opened, its check verdict judged,
      the merge confirmed, and the session closed or its preservation
      reported
</success_criteria>
