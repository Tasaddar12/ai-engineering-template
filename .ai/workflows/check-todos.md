<!-- workflow
step: check-todos
agent-roles: orchestrator
produces: todo disposition
consumes: .planning/todos/pending/, ROADMAP.md, STATE.md
-->

<purpose>
List pending todos, let the user select one, load its full context and route to
the appropriate action — work it now, fold it into a phase, turn it into its own
phase, or put it back.
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

If valid: load the selected todo and proceed.
If invalid: "Invalid selection. Reply with a number (1–[N]) or `q` to exit."
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

<step name="offer_actions">
**Text mode** (`text_mode` true, or `--text` in the arguments): replace every
AskUserQuestion with a plain-text numbered list and ask the user to type a
number.

**If the todo maps to a roadmap phase:**

Use AskUserQuestion:
- header: "Action"
- question: "This todo relates to Phase [N]: [name]. What would you like to do?"
- options:
  - "Work on it now" — move to completed, start working
  - "Fold into that phase" — leave pending; `/discuss-phase [N]` will offer it
  - "Brainstorm approach" — think it through before deciding
  - "Put it back" — return to the list

**If there is no roadmap match:**

Use AskUserQuestion:
- header: "Action"
- question: "What would you like to do with this todo?"
- options:
  - "Work on it now" — move to completed, start working
  - "Make it a quick task" — `/quick` for a small, self-contained change
  - "Make it a phase" — `/phase` with this scope
  - "Put it back" — return to the list
</step>

<step name="execute_action">
**Work on it now:**

```bash
phase_run query todo.complete "${filename}"
```

Present the problem and solution context, then begin the work or ask how to
proceed.

**Fold into that phase:** keep it pending. `/discuss-phase [N]` cross-references
pending todos and will offer this one at that point. Return to the list or exit.

**Make it a quick task:** display `/quick [description from todo]`. Keep it
pending until the quick task completes, so nothing is lost if the user stops.

**Make it a phase:** display `/phase "[description from todo]" --goal "[problem]"`.
Keep it pending; the user runs the command in a fresh context.

**Brainstorm approach:** keep it pending and start a discussion about the problem
and the candidate approaches.

**Put it back:** return to `list_todos`.
</step>

<step name="update_state">
Whenever a todo moved (completed), refresh the STATE.md section from disk:

```bash
phase_run query state.sync-todos
```
</step>

<step name="git_commit">
```bash
phase_run query commit "docs: resolve todo - ${title}" --files .planning/todos .planning/STATE.md
```

Skip this step when nothing moved.
</step>

</process>

<anti_patterns>
- Don't delete todos — completing moves them to `.planning/todos/completed/`
- Don't start implementing a todo that the user only asked to review
- Don't hand-edit the STATE.md Pending Todos section — use `state.sync-todos`
- Don't fold a todo into a phase by editing its plans here; discussion owns that
</anti_patterns>

<success_criteria>
- [ ] Pending todos listed with area, severity and age
- [ ] Selected todo's full context loaded, including its referenced files
- [ ] Roadmap relationship checked where a roadmap exists
- [ ] Action chosen by the user and executed
- [ ] STATE.md refreshed when a todo moved
- [ ] Movement committed
</success_criteria>
