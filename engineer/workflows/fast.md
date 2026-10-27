@engineer/references/response-language-directive.md

<purpose>
Execute a trivial task inline without subagent overhead. No PLAN.md, no Task spawning,
no research, no plan checking. Just: understand → do → commit → log.

For tasks like: fix a typo, update a config value, add a missing import, rename a
variable, commit uncommitted work, add a .gitignore entry, bump a version number.

Use /quick for anything that needs multi-step planning or research.
</purpose>

<process>

<step name="parse_task">
Parse `$ARGUMENTS` for the task description.

If empty, ask:
```
What's the quick fix? (one sentence)
```

Store as `$TASK`.
</step>

<step name="scope_check">
Before editing, name one bounded outcome, at most three exact file paths, explicit deletions (none by default), shared resources, and a concrete observable done criterion. A typo, config value, missing import or ignore entry can qualify; new dependencies, architecture changes and research do not. The explicit human /fast request authorizes only that outcome. Another workflow must not invoke fast as a phase implementation shortcut.

If scope exceeds this lane, automatically continue the already authorized outcome through the complete /quick workflow, or the authorized phase discussion/planning procedure when phase-sized. Preserve the user's implementation scope; phase implementation still requires an explicit instruction for that phase. Do not ask for a routine proceed menu. A locked decision or actual human acceptance requirement blocks only dependent work. If scope grows after edits, preserve the session and changes and continue the bounded quick procedure there, without resetting or staging unrelated work.
</step>

<step name="open_session">
Read and execute engineer/workflows/_runtime-launcher.snippet.sh. Inspect session.status; reuse only this task's matching real isolated quick session. Otherwise run `engineer_run query session.open quick "${TASK_LABEL}"`. Quote and enter its returned worktree and capture SESSION_BRANCH, SESSION_WORKTREE and base. Verify the actual root/branch equals that session and differs from the primary/shared checkout. A failed isolation operation stops implementation; never edit inline in the primary checkout. Run `engineer_run query quick.create "${TASK}"` inside the session, retaining QUICK_ID and the returned directory/path. No phase is invented.
</step>

<step name="execute_inline">
Do the work directly:

1. Read the relevant file(s)
2. Make the change(s)
3. Verify the concrete done criterion with applicable existing checks only when execution is permitted. Honor explicit deferred-check instructions; record pending evidence and withhold any verdict requiring it.

**No PLAN.md.** Just do it.
</step>

<step name="commit">
Inspect the exact changed paths against the bounded scope and explicit deletion list. Preserve unrelated dirt. Commit only those paths with `engineer_run query commit "fix: ${CONCISE_OUTCOME}" --files "${OWNED_FILE_1}" "${OWNED_FILE_2}"` (omit unused placeholders). Use fix/feat/docs/chore/refactor as appropriate. Read the actual commit hash; a failed commit remains blocked, never reported complete. Never stage the whole tree.
</step>

<step name="log_to_state">
After the concrete done criterion is met, run `engineer_run query quick.update "${QUICK_ID}" --status complete --commit "${SOURCE_COMMIT}"`, then state.record-session with the actual stopped-at result and quick record path. Commit the exact QUICK directory and changed STATE path through `engineer_run query commit`. The runtime owns these records; do not append or migrate tables by hand. User-deferred checks remain pending and never become a verification pass.
</step>

<step name="deliver_session">
When delivery is authorized, push the exact session branch without force. Build and validate the full canonical PR template under engineer/references/git-workflow.md, then `engineer_run query pr.open "${SESSION_BRANCH}" --title "${TITLE}" --body-file "${BODY_FILE}"` and read back the provider result. Open a draft on the first push and refresh it after each meaningful slice. Observe `pr.checks "${SESSION_BRANCH}" --timeout N` with a bounded timeout; pending/failed checks remain pending/failed. A timeout never proves completion.

Fast creates no PLAN or SUMMARY and dispatches no agents. This alone supplies no independent verification. Leave the draft open unless actual independent quick evidence already exists: resolve the report with `verification.resolve-file --quick ID`, read `verification.status --quick ID`, and require current `verification.fingerprint --quick ID` and `verification.current --quick ID`. Its canonical report must include quick, status, covered_files, fingerprint, revision, issue_refs and v4 covered_digest. Use the real quick.threat-* APIs and canonical planned checklist/human-UAT rules for any findings. Never substitute a fake phase or self-authored passed report. Only current passing evidence can support `pr.ready BRANCH --quick ID`; merge additionally requires the user's explicit merge instruction and `pr.merge BRANCH --quick ID --confirm`.

After provider-confirmed merge, pr.sync reads remote state; session.close BRANCH must run from another clean checkout whose HEAD contains the session head. Preserve dirty, active, unintegrated or blocked worktrees. No forced cleanup.
</step>

<step name="done">
Report completion:

```
✅ Done: {what was changed}
   Commit: {short hash}
   Files: {list of changed files}
```

Report the PR state and pending checks or blockers accurately. No unrelated next-task menu.
</step>

</process>

<guardrails>
- NEVER spawn a Task/subagent — this runs inline
- NEVER create PLAN.md or SUMMARY.md files
- NEVER run research or plan-checking
- If scope grows beyond three edits, preserve work and continue the authorized outcome through /quick.
- If research is needed, preserve the session and route to the complete /quick method.
</guardrails>

<success_criteria>
- [ ] Task completed in current context (no subagents)
- [ ] Atomic git commit with conventional message
- [ ] Runtime quick record and session evidence updated; exact artifacts committed
- [ ] Edited only in the real isolated quick session; authorized draft PR tracked
- [ ] Concrete done criterion and actual validation/delivery state reported; timing is an estimate, never a bypass
</success_criteria>
