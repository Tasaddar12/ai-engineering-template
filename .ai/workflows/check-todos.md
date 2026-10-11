<!-- workflow
step: check-todos
agent-roles: orchestrator
produces: todo disposition
consumes: .planning/todos/pending/, ROADMAP.md, STATE.md
-->

<purpose>
List pending todos, let the user select one, load its full context, publish or link that
selected TODO through reviewed issue context, then route it to an appropriate action.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="init_context">
```bash
_root="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
for _c in "$_root"/.{ai,claude,codex}/runtime/phase.py "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/runtime/phase.py "${CODEX_HOME:-$HOME/.codex}"/runtime/phase.py; do
  [ -f "$_c" ] && PHASE_RUNTIME="$_c" && break
done
[ -n "${PHASE_RUNTIME:-}" ] || { echo "ERROR: phase runtime not found; run the installer." >&2; exit 1; }
phase_run() { "$(command -v python3 || command -v python)" "$PHASE_RUNTIME" "$@"; }
INIT=$(phase_run query init.todos)
```

Extract: `todo_count`, `todos`, `pending_dir`, `commit_docs`, `text_mode`,
`response_language`, `roadmap_exists`.

**If `response_language` is set:** all user-facing output MUST be presented in
`{response_language}`; technical terms, code and file paths stay in English.

If `todo_count` is 0:

```
No pending todos.

Capture one with `/capture <description>` whenever an idea surfaces mid-session.
```

Exit.
</step>

<step name="parse_filter">
An optional argument filters by area: `/capture --list api` → area = `api`.
Filter the `todos` array from init; the runtime returns them sorted by severity
then creation time.

If the filter matches nothing, say so and list the areas that do exist.
</step>

<step name="list_todos">
Display the filtered todos as a numbered list:

```
Pending Todos:

1. Add auth token refresh (api, blocker, 2d ago)
2. Fix modal z-index issue (ui, cosmetic, 1d ago)
3. Refactor database connection pool (database, minor, 5h ago)

---

Reply with a number to view details, or:
- `/capture --list [area]` to filter by area
- `q` to exit
```

Format age as relative time from the `created` timestamp.
</step>

<step name="handle_selection">
Wait for the user to reply with a number.

If valid: keep the selected entry's exact relative `file` path as `todo_file`;
set `todo_name` to its basename for TODO runtime verbs, then load it and proceed.
If invalid: reply that the selection must be a number in the displayed range or `q`.
</step>

<step name="load_context">
Read the todo file completely and display:

```
## [title]

**Area:** [area]
**Severity:** [severity]
**Created:** [date] ([relative time] ago)
**Files:** [list or "None"]

### Problem
[problem section content]

### Solution
[solution section content]
```

If the `files` field has entries, read and briefly summarise each one so the
user is deciding against the current code, not the code as it was when captured.
</step>

<step name="check_roadmap">
If `roadmap_exists` is true, check whether the todo belongs to a planned phase:

```bash
for phase in $(phase_run query phases.list --raw | ...); do :; done
MATCHES=$(phase_run query todo.match-phase "${candidate_phase}")
```

In practice, run `todo.match-phase` for the next one or two open phases and look
for this todo in the `matches` array. Each match carries `score` and `reasons`
(the shared keywords). Note any match for the action options below.
</step>

<step name="publish_selected_issue">
Listing is read-only. Selection through `/capture --list` authorizes publication
of this one TODO in the current repository; do not ask for another publication
permission or publish any other pending record.

Set `related_pr` to the same-repository PR URL when provided; otherwise leave it
unset.

After loading the complete TODO and referenced files, preview only the selected
pending basename:

```bash
if [[ -n "${related_pr:-}" ]]; then
  PREVIEW=$(phase_run query todo.issue-preview "${todo_name}" --related-pr "${related_pr}")
else
  PREVIEW=$(phase_run query todo.issue-preview "${todo_name}")
fi
```

Read `previewToken`, `privateLocal`, `candidates` and `relatedPRs` from the JSON;
use `previewToken` as `preview_token`.

Compare its private local input with all open and closed issue candidates and
related PR context. Runtime supplies candidates but does not semantically dedupe.
Use the existing issue template to prepare a separately reviewed public title
and body; keep private metadata and sensitive context out. Reuse the local title
only if safe after review. If no safe, actionable public text is available, stop
with publication blocked and leave the TODO pending. Choose one of
`--existing-issue "${issue_url}"` or `--no-match`; reuse only an
actionable issue and never edit or close it as part of linking. For a closed
match, compare closure evidence with the full TODO scope; closed status alone
never proves resolution. Keep mismatches pending, and reopen only with separate
authorization or choose the appropriate issue/scope. If safe context must be
added, add only reviewed details explicitly, then preview again or stop with
publication blocked.

```bash
PUBLISH=$(phase_run query todo.issue-publish "${todo_name}" \
  --preview-token "${preview_token}" \
  --title "${public_title}" \
  --body-file "${public_body_file}" \
  --existing-issue "${issue_url}")
```

For an explicit no-match, use `--no-match` instead of the final
`--existing-issue` option.

The body file must be separate from the private TODO. A successful result must
include `linked: true` and a verified `issueURL`; extract it for reporting.
Linking leaves the TODO pending.
On any auth, lookup, create, readback or recovery failure, stop before offering
actions. Preserve the complete TODO and report no issue URL. If `issue-publish`
recorded an attempted create, only a fresh preview and the identical reviewed
intent may recover one exact marker; never issue a second create. Block on
uncertain, zero, multiple, unreadable or mismatched results. If publication
changed local metadata before failing, sync STATE and commit only the selected
TODO file and `.planning/STATE.md` before stopping; do not commit when neither
path changed.

After a successful link, sync STATE. Commit the exact selected TODO path and
`.planning/STATE.md` whenever either changed; do not skip the commit just because
the TODO remains pending:

```bash
phase_run query state.sync-todos
phase_run query commit "docs: link todo issue - ${title}" --files "${todo_file}" .planning/STATE.md
```
</step>

<step name="offer_actions">
**Text mode** (`text_mode` true, or `--text` in the arguments): replace every
AskUserQuestion with a plain-text numbered list and ask the user to type a
number.

**If the todo maps to a roadmap phase:**

Use AskUserQuestion:
- header: "Action"
- question: "This todo relates to Phase [N]: [name]. What would you like to do?"
- options:
  - "Work on it now" - start work; keep the TODO pending
  - "Fold into that phase" — leave pending; `/discuss-phase [N]` will offer it
  - "Brainstorm approach" — think it through before deciding
  - "Put it back" — return to the list

**If there is no roadmap match:**

Use AskUserQuestion:
- header: "Action"
- question: "What would you like to do with this todo?"
- options:
  - "Work on it now" - start work; keep the TODO pending
  - "Make it a quick task" — `/quick` for a small, self-contained change
  - "Make it a phase" — `/phase` with this scope
  - "Put it back" — return to the list
</step>

<step name="execute_action">
**Work on it now:** keep the TODO pending. Present its full context and begin
only within the existing phase and implementation authorization rules.

After the work is demonstrated resolved, explicitly call:

```bash
COMPLETE=$(phase_run query todo.complete "${todo_name}")
# Read `completed` from the result into `completed_file`.
```

The runtime refuses completion while publication is attempted or unresolved. A
linked TODO can move only after the same-repository issue is verified `CLOSED`.
If status is open, unavailable or uncertain, preserve the TODO as pending. Capture
does not close issues; issue closure still requires its own authorization.

**Fold into that phase:** keep it pending. `/discuss-phase [N]` cross-references
pending todos and will offer this one at that point. Return to the list or exit.

**Make it a quick task:** display `/quick [description from todo]`. Keep it
pending until the quick task completes, so nothing is lost if the user stops.

**Make it a phase:** display `/phase "[description from todo]" --goal "[problem]"`.
Keep it pending; the user runs the command in a fresh context.

**Brainstorm approach:** keep it pending and start a discussion about the problem
and the candidate approaches.

**Put it back:** return to `list_todos`; the linked TODO stays pending.
</step>

<step name="update_state">
After a TODO is explicitly completed, refresh the STATE.md section from disk:

```bash
phase_run query state.sync-todos
```
</step>

<step name="git_commit">
For completion, commit only the selected source path, returned completed path,
and STATE:

```bash
phase_run query commit "docs: resolve todo - ${title}" --files "${todo_file}" "${completed_file}" .planning/STATE.md
```

The earlier issue-link commit includes only the selected TODO and STATE. Do not
stage the whole pending directory. Commit metadata changes even when no TODO
moved; skip a later completion commit when no additional paths changed.
</step>

</process>

<anti_patterns>
- Don't delete todos — completing moves them to `.planning/todos/completed/`
- Don't start implementing a todo that the user only asked to review
- Don't hand-edit the STATE.md Pending Todos section — use `state.sync-todos`
- Don't fold a todo into a phase by editing its plans here; discussion owns that
</anti_patterns>

<success_criteria>
- [ ] Pending todos listed with area, severity and age; listing alone is read-only
- [ ] Selected TODO's full context and referenced files loaded
- [ ] Selected TODO linked to a verified issue before action routing, or failure stops routing with full pending context preserved
- [ ] Work, planning and discussion leave the TODO pending; completion follows demonstrated resolution and linked-status guard
- [ ] STATE.md refreshed and exact changed TODO paths committed
</success_criteria>
