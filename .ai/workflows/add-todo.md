<!-- workflow
step: add-todo
agent-roles: orchestrator
produces: .planning/todos/pending/{date}-{slug}.md
consumes: STATE.md
-->

<purpose>
Capture an idea, task or issue that surfaces mid-session as a structured todo for
later work. Enables "thought → capture → continue" without losing context or
derailing the current phase.
</purpose>

<required_reading>
@~/.ai/workflows/_session.snippet.md
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="init_context">
Load todo context:

```bash
_root="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
for _c in "$_root"/.{ai,claude,codex}/runtime/phase.py "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/runtime/phase.py "${CODEX_HOME:-$HOME/.codex}"/runtime/phase.py; do
  [ -f "$_c" ] && PHASE_RUNTIME="$_c" && break
done
[ -n "${PHASE_RUNTIME:-}" ] || { echo "ERROR: phase runtime not found; run the installer." >&2; exit 1; }
phase_run() { "$(command -v python3 || command -v python)" "$PHASE_RUNTIME" "$@"; }
INIT=$(phase_run query init.todos)
```

Extract from the init JSON: `commit_docs`, `date`, `timestamp`, `todo_count`,
`todos`, `pending_dir`, `todos_dir_exists`, `text_mode`, `response_language`.

**If `response_language` is set:** all user-facing output of this workflow MUST
be presented in `{response_language}`. Technical terms, code, file paths and
subagent prompts stay in English.

Note the existing areas in the `todos` array — reuse one in `infer_area` rather
than coining a near-duplicate.
</step>

<step name="open_session">
Open the worktree this work lives in, before writing anything. Read
@~/.ai/workflows/_session.snippet.md for the full contract.

```bash
SESSION=$(phase_run query session.open milestone "todos")
```

Parse `worktree`, `branch`, `base`, `reused` and `synced`. **Run every
subsequent command in this workflow from `worktree`.** An open session for
captured ideas is reused rather than replaced, so the work accumulates onto one branch
and arrives as one pull request.

Report it in one line:

```
Session: {branch} ({reused ? "resumed" : "opened"}) at {worktree}
```

If the verb fails, **stop and report its message**. It means isolation could not
be established, and continuing in the invoking checkout is the one outcome this
project does not allow — the dispatch guard would block the write anyway.
</step>


<step name="extract_content">
**With arguments:** use them as the title/focus.
- `/capture Add auth token refresh` → title = "Add auth token refresh"

**Without arguments:** analyse the recent conversation to extract:
- The specific problem, idea or task discussed
- Relevant file paths mentioned
- Technical details (error messages, line numbers, constraints)

Formulate:
- `title`: a 3–10 word descriptive title (action verb preferred)
- `problem`: what is wrong, or why this is needed
- `solution`: approach hints, or "TBD" if it is only an idea
- `files`: relevant paths with line numbers from the conversation
</step>

<step name="infer_area">
The runtime infers the area from file paths using this table. Pass `--area`
explicitly only when you are overriding it:

| Path pattern | Area |
|--------------|------|
| `src/api/*`, `api/*` | `api` |
| `src/components/*`, `src/ui/*` | `ui` |
| `src/auth/*`, `auth/*` | `auth` |
| `src/db/*`, `database/*` | `database` |
| `tests/*`, `__tests__/*` | `testing` |
| `docs/*` | `docs` |
| `.planning/*` | `planning` |
| `scripts/*`, `bin/*` | `tooling` |
| No files or unclear | `general` |

Prefer an existing area from the init `todos` array when one matches.
</step>

<step name="infer_severity">
Infer a **suggested** severity, then CONFIRM it with the user before writing.
Never silently auto-assign: a mis-tagged severity quietly corrupts backlog
triage, which is the signal this field exists to provide.

| User says | Suggest |
|-----------|---------|
| "crashes", "error", "exception", "fails completely", "data loss" | blocker |
| "doesn't work", "nothing happens", "wrong behavior" | major |
| "works but…", "slow", "weird", "minor issue" | minor |
| "color", "spacing", "alignment", "looks off" | cosmetic |

Default the suggestion to **major** when unclear.

Confirm with AskUserQuestion, presenting the suggested value first:
- header: "Severity"
- question: "Suggested severity: [suggested]. Confirm or change:"
- options:
  - "blocker" — breaks a workflow or loses data; fix first
  - "major" — wrong behavior with no workaround
  - "minor" — works, but with a workaround or annoyance
  - "cosmetic" — visual/polish only

**Text mode** (`text_mode` true in the init JSON, or `--text` in the arguments):
replace the AskUserQuestion with a plain-text numbered list of the four options
and ask the user to type a number. Required for runtimes without AskUserQuestion.

Carry the confirmed value into `--severity`.
</step>

<step name="check_duplicates">
```bash
grep -l -i "[key words from title]" .planning/todos/pending/*.md 2>/dev/null || true
```

If a potential duplicate is found, read it and compare scope. If they overlap,
use AskUserQuestion:
- header: "Duplicate"
- question: "Similar todo exists: [title]. What would you like to do?"
- options:
  - "Skip" — keep the existing todo
  - "Replace" — update the existing one with the new context
  - "Add anyway" — create it as a separate todo
</step>

<step name="create_file">
**Delegate the write to `phase_run query todo.add`:**

```bash
RESULT=$(phase_run query todo.add "${title}" \
  --problem "${problem}" \
  --solution "${solution}" \
  --severity "${severity}" \
  --files "${file_refs[@]}")
```

The runtime handles the date-stamped slug filename, collision suffixes, area
inference and the frontmatter block:

```markdown
---
created: [timestamp]
title: [title]
area: [area]
severity: [blocker|major|minor|cosmetic]
files:
  - [file:lines]
---

## Problem

[enough context for a future session to understand this weeks later]

## Solution

[approach hints or "TBD"]
```

Extract from the result: `file`, `title`, `area`, `severity`, `file_count`.

Pass `--area` only when overriding the inferred value.
</step>

<step name="update_state">
Refresh the STATE.md "Pending Todos" section from the todos on disk:

```bash
phase_run query state.sync-todos
```

The runtime re-reads `.planning/todos/pending/`, renders one capped bullet per
todo and replaces the section body wholesale, so a stale run-on section is
superseded cleanly with no migration step. It reports
`{"updated": false, "reason": "no STATE.md"}` and changes nothing when STATE.md
is absent — a partial read never overwrites a good existing section.
</step>

<step name="git_commit">
```bash
phase_run query commit "docs: capture todo - ${title}" --files "${todo_file}" .planning/STATE.md
```

The runtime respects `commit_docs` and skips gitignored paths automatically.
</step>

<step name="deliver_session">
This workflow owns the whole unit of work, so it delivers the session rather
than leaving it open. Follow the delivery sequence in
@~/.ai/workflows/_session.snippet.md exactly and in order: the empty-session
check, `git push -u`, `pr.open`, `pr.checks`, the merge confirmation, then
`pr.merge`, `pr.sync` and `session.close`.

Every command runs from `SESSION.worktree`.

**Title:** `Capture todo: ${title}`

**Body:** the todo's own problem and solution sections, plus its area and the severity the user confirmed. Keep it short; the todo file is the record, and the pull request only carries it to the base branch.

A `todos` session is shared, so a resumed one may already carry other captures. Name every todo in the range, not only this one — `pr.open` is editing a pull request that describes all of them.


Report the snippet's delivery line before the output below. A `failing` check
verdict, a declined merge or a preserved session are all reported as they stand
and none of them is worked around — a preserved session is unmerged work.
</step>

<step name="confirm">
```
Todo saved: {file}

  {title}
  Area: {area}
  Severity: {severity}
  Files: {file_count} referenced

---

Would you like to:

1. Continue with current work
2. Add another todo
3. View all todos (`/capture --list`)
```
</step>

</process>

<anti_patterns>
- Don't write the todo file by hand — `todo.add` owns the filename, frontmatter and collision handling
- Don't auto-assign severity without confirming it
- Don't hand-edit the STATE.md Pending Todos section — use `state.sync-todos`
- Don't act on the todo now; capture it and return to the current work
- Don't finish with the session still open — an undelivered session is
  work on a branch nobody merged
- Don't merge past a `failing` or `pending` check verdict, and don't
  `--force` a preserved session away
</anti_patterns>

<success_criteria>
- [ ] Todo file created with valid frontmatter
- [ ] Problem section has enough context to be actionable weeks later
- [ ] Severity confirmed by the user, not silently assigned
- [ ] Duplicates checked and resolved
- [ ] Area consistent with existing todos
- [ ] STATE.md Pending Todos refreshed from disk
- [ ] Todo and state committed
- [ ] Session delivered: pull request opened, its check verdict judged,
      the merge confirmed, and the session closed or its preservation
      reported
</success_criteria>
