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

Extract `file`, `title`, `area`, `severity`, `file_count` and `todoId` from the result. Keep the exact returned relative path as `todo_file`; set `todo_name` to its basename for TODO runtime verbs.

Pass `--area` only when overriding the inferred value.
</step>

<step name="publish_issue">
This `/capture` invocation authorizes publishing this newly captured TODO in the
current repository. Do not ask for another publication permission. Publish only
this TODO; duplicate `Skip` ends capture without publishing another record.

If the conversation names a related PR in this repository, include
`--related-pr "${related_pr}"` in the preview call. Preview the selected pending
TODO:

```bash
PREVIEW=$(phase_run query todo.issue-preview "${todo_name}")
```

Read `previewToken`, `privateLocal`, `candidates` and `relatedPRs` from the JSON;
use `previewToken` as `preview_token`. Treat `privateLocal` as private review input.
Compare `candidates` (open and closed issues) and `relatedPRs` with the TODO's
scope, including linked PR context. Runtime returns candidates; it does not
perform semantic deduplication for you. Reuse a matching issue only when its
current context is actionable. For a closed match, compare its closure evidence
with this TODO's full scope; closed status alone never proves the TODO resolved.
Keep a mismatch pending. Reopen only with separate authorization or choose the
appropriate issue/scope. Reuse links the issue without editing or closing it. If reviewed safe details are needed, add them explicitly with `gh issue edit` or
`gh issue comment`, then preview again; block if the issue still cannot carry the
needed context.

Use the existing issue template to prepare a separately reviewed public title
and body. Reuse the local title only after checking that it is safe to publish.
Never copy private TODO metadata or sensitive context into the public body. If no
safe, actionable public text is available, block publication and keep the local
TODO pending. Put the body in a separate non-empty file, never the TODO file.
Choose exactly one reviewed decision:

```bash
--existing-issue "${issue_url}"
--no-match
```

Pass that decision with the current preview token, public title and body file:

```bash
PUBLISH=$(phase_run query todo.issue-publish "${todo_name}" \
  --preview-token "${preview_token}" \
  --title "${public_title}" \
  --body-file "${public_body_file}" \
  --existing-issue "${issue_url}")
```

For an explicit no-match, use `--no-match` instead of the final
`--existing-issue` option.

Use `--no-match` instead of `--existing-issue` only after reviewing every
candidate. An exact existing TODO marker is reused. A successful result must
return `linked: true` and a verified `issueURL`; extract it for reporting. The
TODO stays pending.

On authentication, lookup, create, readback or recovery failure, report that
publication is blocked, preserve and commit the full pending TODO, and do not
claim an issue URL. If a create may have succeeded, never create again: preview
again and retry only with the identical reviewed title/body so the runtime can
recover one verified exact marker. Zero, multiple, unreadable or mismatched
matches require human resolution; changed intent cannot be retried.
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

Use the exact `file` returned by `todo.add`, including publication metadata or
verified linkage. Commit the local TODO and STATE even when remote publication is
blocked. The runtime respects `commit_docs` and skips gitignored paths.
</step>

<step name="confirm">
```
Todo saved and still pending: {file}
Verified GitHub issue: {issueURL}

  {title}
  Area: {area}
  Severity: {severity}
  Files: {file_count} referenced

If publication was blocked, say so, give no issue URL, and confirm that the full
TODO remains pending and committed.

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
- Don't act on the todo now; capture it, publish its reviewed issue link, and return to the current work
- Don't publish the private TODO body or claim linkage without a verified `issueURL`
</anti_patterns>

<success_criteria>
- [ ] Todo file created with valid frontmatter and a stable `todoId`
- [ ] Problem section has enough context to be actionable weeks later
- [ ] Severity confirmed by the user, not silently assigned
- [ ] Duplicates checked and resolved
- [ ] Area consistent with existing todos
- [ ] STATE.md Pending Todos refreshed from disk
- [ ] Verified issue linkage recorded, or blocked publication truthfully reported with full TODO preserved
- [ ] TODO remains pending after capture and exact TODO path plus STATE committed
</success_criteria>
