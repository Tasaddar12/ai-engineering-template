<!-- workflow: check-todos; produces: selected pending-item routing -->
<purpose>
List pending work with its actual severity and issue state, publish or link the selected item's canonical issue before routing it, and preserve pending status until demonstrated resolution.
</purpose>
<required_reading>
@~/.claude/engineer/RULES.md
@~/.claude/engineer/references/git-workflow.md
@~/.claude/engineer/templates/issue.md
</required_reading>
<process>
<step name="init_context">
Read and execute engineer/workflows/_runtime-launcher.snippet.sh. Run `engineer_run query init.todos`. Read actual records/count, commit_docs, text_mode and roadmap_exists. If empty, report "No pending captured work" and point to `/capture <description>`; do not fabricate a placeholder record.
</step>
<step name="parse_filter">
Treat an optional area/name filter as data. Compare it with actual record fields; do not pass an unquoted filter into a shell query. No match is an empty filtered list, not permission to create a new item.
</step>
<step name="list_todos">
Show each matching stable ID/file, title, area, severity, phase assignment, current pending state and provider-confirmed issue link/state when available. Retain the concrete problem and acceptance when displaying a selected item. Do not turn a linked closed issue into a completed local record without the resolution guards.
</step>
<step name="handle_selection">
Capture the exact selected TODO_FILE and TODO_NAME. Ask for selection when no item was explicitly named; preserve text-mode rendering without simulating a reply. Cancel leaves every item unchanged. Selection does not itself authorize implementation or an external scope change.
</step>
<step name="load_context">
Read the complete selected record, referenced source evidence and canonical linked issue state. Preserve its acceptance, severity, exclusions and history. Do not infer that a proposed solution was implemented or that a closed issue alone demonstrates the local acceptance.
</step>
<step name="check_roadmap">
When a roadmap exists, run roadmap.analyze and identify the next one or two actually open phases. Run `engineer_run query todo.match-phase "${PHASE_NUMBER}"` for those phases and inspect explicit matches. Do not invent a phases-list pseudo-loop or silently assign the selected item to a merely similar phase. Show the exact matching goal/acceptance and the intended fold before routing.
</step>
<step name="publish_selected_issue">
Publish or link only the selected record. Read the complete canonical issue template, author the exact public title/body and review canonical matching issues. Choose the exact canonical variant Bug, Enhancement, Decision required, Security risk, or UAT and preserve its complete template. Preview with todo.issue-preview FILE --variant VARIANT --title TITLE --body-file FILE and exactly one `--existing-issue URL_OR_NUMBER` or `--no-match`. Review every returned public field and source snapshot. Publish with todo.issue-publish and the same arguments, explicit --variant and reviewed disposition plus the content-bound --preview-token. Existing linked edits use todo.issue-update. Re-read provider identity, URL, title/body and state; inspect unknown outcomes before retrying and never duplicate an uncertain create.

On publication failure, stop before any action routing for this item, preserve its pending record and blocked-publication reason, run state.sync-todos and commit only its exact file plus changed STATE. Linking a reviewed closed match does not reopen/close it or complete the pending record.
</step>
<step name="offer_actions">
Offer concrete choices for the selected item: Fold into the named matching phase; Make it a quick task; Make it a phase; Leave pending. Each choice shows its exact scope and keeps the original todo pending. A fold must appear under the phase CONTEXT's exact Folded Todos filenames; a quick task gets its own runtime record; a phase is created only through phase.add/insert. Do not mark selection or routing as resolution.
</step>
<step name="execute_action">
Carry out the chosen record/routing operation within actual authorization. Implementing a phase still requires explicit instruction for that phase. A separately authorized quick outcome runs the complete quick workflow with isolation and its own validation. If existing work already resolves this item, verify concrete local acceptance and canonical issue CLOSED readback first, including accepted-human evidence when it is UAT. Only then use `engineer_run query todo.complete "${TODO_FILE}"`; the runtime rechecks source digest and issue evidence. A failed guard leaves the item pending with its actual reason. Never move a file directly to a completed folder.
</step>
<step name="update_state">
Run state.sync-todos from actual records. Commit the exact returned created/changed/archive paths and STATE through engineer_run query commit, including removed paths with --files-removed when the runtime archived a record. Do not remove records from the index merely to hide a pending count.
</step>
<step name="report">
Report the selected identity, provider-confirmed issue, chosen action, new phase/quick record if any, pending/completed result and exact resolution/blocker evidence. Preserve independent pending work and do not start an unselected task.
</step>
</process>
<anti_patterns>
Never publish unselected records, infer implementation authority from selection, complete an item from routing alone, skip duplicate disposition/readback, or hand-render state counts.
</anti_patterns>
<success_criteria>
The selected record's full context and severity are preserved, its canonical issue is verified or publication is explicitly blocked, routing stayed within authority, and completion reflects demonstrated resolution and guarded provider/local evidence.
</success_criteria>
