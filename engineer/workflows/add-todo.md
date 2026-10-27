<!-- workflow: add-todo; produces: pending todo and canonical issue link -->
<purpose>
Capture the user's idea, task or issue as a complete structured pending record, then publish or link its canonical issue through a reviewed content-bound preview. This workflow records requested work; it does not implement it.
</purpose>
<required_reading>
@~/.claude/engineer/RULES.md
@~/.claude/engineer/references/git-workflow.md
@~/.claude/engineer/templates/issue.md
</required_reading>
<process>
<step name="init_context">
Read and execute engineer/workflows/_runtime-launcher.snippet.sh. Run `engineer_run query init.todos`. Read actual pending records/count, text_mode, response_language and project/roadmap existence. The runtime todo.add owns record allocation and directories; do not pre-create folders or hand-write frontmatter.
</step>
<step name="extract_content">
Read the user's actual description and relevant conversation. Separate title, concrete problem, desired outcome, proposed solution, affected files, scope and acceptance. Retain details and examples the user supplied; do not replace them with a vague title or shortened restatement. If evidence is missing, identify it as unknown rather than inventing a stack trace or promised behavior.

Examples: `/capture Fix expired sessions returning an HTML page` records the observed response and desired API behavior; `/capture Add export of the selected date range` records what the export must contain and exclusions; `/capture --list api` routes to the listing workflow, not a new record. Ask only for a missing detail that actually prevents an accurate record.
</step>
<step name="infer_area">
Choose the existing project's area convention from actual pending records and source ownership. Typical areas are api, auth, ui, data, tests, infra and docs, but use project vocabulary when established. Keep a cross-cutting issue explicit rather than hiding affected components. A source path is evidence to inspect, not authority to modify it.
</step>
<step name="infer_severity">
Use minor for a bounded inconvenience, major for a material workflow/behavior defect, and blocker for work that prevents a required outcome. Preserve explicit user severity. When evidence does not distinguish two levels, present the concrete impact and ask a short severity question rather than exaggerating urgency. In text mode, render real numbered options and wait for the answer; do not fabricate a choice.
</step>
<step name="check_duplicates">
Read pending records and canonical linked issue evidence before adding a duplicate. If an existing record represents the same work, show its exact identity and preserve its existing scope, status and history. Do not create a second pending record solely because its title differs. A related but distinct acceptance outcome needs its own explicit distinction.
</step>
<step name="create_file">
Run `engineer_run query todo.add "${TITLE}" --area "${AREA}" --severity "${SEVERITY}" --problem "${PROBLEM}" --solution "${SOLUTION}" --description "${DESCRIPTION}"`, adding exact known --files paths and an explicitly applicable --phase only when supported by actual scope. Pass each value as a single argument; never interpolate user prose into executable shell code. Read the returned exact file/path, title and stable todo metadata. Stop on failure or an unusable returned path; do not substitute a guessed filename or a manually generated slug.
</step>
<step name="publish_issue">
Read the full canonical issue File Template and populate its required sections, concrete acceptance, evidence, scope/exclusions and validation details. Preserve all required structure and markers. Public content must not expose secrets or invent observations. Search canonical provider issues and existing record links for the same work; explicitly review either one existing issue or a genuine no-match disposition.

Preview with `engineer_run query todo.issue-preview "${TODO_FILE}" --variant "${ISSUE_VARIANT}" --title "${PUBLIC_TITLE}" --body-file "${PUBLIC_BODY_FILE}"`, adding exactly one reviewed `--existing-issue "${ISSUE_URL_OR_NUMBER}"` or `--no-match`. Review the complete returned public title/body, source identity and snapshot. Select the exact canonical variant Bug, Enhancement, Decision required, Security risk, or UAT from the actual finding. Run `engineer_run query issue.validate --variant "${ISSUE_VARIANT}" --body-file "${PUBLIC_BODY_FILE}"` when validation execution is permitted; preview independently validates and binds that same variant. Never change the variant between preview and publish. Retain the content-bound preview token, disposition and exact body file.

Publish with todo.issue-publish and the same source/--variant/title/body/labels/disposition plus `--preview-token "${PREVIEW_TOKEN}"`. Existing linked updates use todo.issue-update under its existing-link contract. The token binds the reviewed public content and duplicate disposition; any edit requires a fresh preview. Read back the canonical issue URL, repository, title/body and state before linking the local record. An already closed reviewed match may be linked for reconciliation; the local todo remains pending and this workflow does not reopen or close the issue.

On a failed or uncertain provider result, inspect canonical provider state before any retry. Never send a second create to recover an unknown first create. Keep the local record and exact blocked-publication reason. A captured local idea is still worth committing even when publication is blocked; do not fabricate a URL or discard the user's details.
</step>
<step name="update_state">
Run `engineer_run query state.sync-todos`. It derives pending counts from runtime records. Never re-render STATE's pending section by hand.
</step>
<step name="git_commit">
Commit the exact returned TODO_FILE and changed STATE path with `engineer_run query commit "docs(capture): record ${TODO_TITLE}" --files "${TODO_FILE}" .planning/STATE.md`. Include the actual blocked-publication status when present; do not stage unrelated project work or claim an issue was published from an unverified return.
</step>
<step name="confirm">
Report the complete record path, title, area, severity and concrete scope. Give a provider-confirmed issue URL or the exact blocked-publication reason. State that the record is pending and no implementation ran. Use `/capture --list` as the single inspection route.
</step>
</process>
<anti_patterns>
Do not implement captured work, invent evidence, shorten the user's supplied details, duplicate a canonical issue, bypass preview/readback, or hand-edit runtime pending counts.
</anti_patterns>
<success_criteria>
The user's actual scope is preserved in a runtime-created pending record, duplicate review and public preview are explicit, publication has verified evidence or an honest blocker, state is synchronized, and exact record changes are committed.
</success_criteria>
