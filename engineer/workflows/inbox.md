<purpose>
Triage and review all open GitHub issues and PRs against project contribution templates.
Produces a structured report showing compliance status for each item, flags missing
required fields, identifies label gaps, and optionally takes action (label, comment, close).
</purpose>

<required_reading>
Read the full canonical sources, including their authoring and consumer guidance:
- @~/.claude/engineer/templates/issue.md - select the existing issue's variant
- @~/.claude/engineer/templates/pull-request.md - the shared PR body contract
- @~/.claude/engineer/references/git-workflow.md - publication, evidence and closure rules
- The target repository's `CONTRIBUTING.md` and contribution templates, if present,
  for actual repository-specific requirements. Do not assume missing typed templates,
  approval labels, issue-first rules or changelog machinery exist.
</required_reading>

<process>
```bash
_ENGINEER_SHIM_NAME="engineer_run"; _ENGINEER_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; ENGINEER_TOOLS="${_ENGINEER_RUNTIME_ROOT}/engineer/bin/${_ENGINEER_SHIM_NAME}"; _engineer_at() { for _p; do if [ -f "$_p" ]; then ENGINEER_TOOLS="$_p"; return 0; fi; done; return 1; }; _engineer_id_ok() { case "$("$1" runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"engineer-runtime"'*'}') return 0;; *) return 1;; esac; }; _engineer_homes() { set -- "${CLAUDE_CONFIG_DIR:-$HOME/.claude}" "${CODEX_HOME:-$HOME/.codex}"; for _h; do _engineer_at "$_h/engineer/bin/${_ENGINEER_SHIM_NAME}" && return 0; done; return 1; }; if _engineer_at "${_ENGINEER_RUNTIME_ROOT}/engineer/bin/${_ENGINEER_SHIM_NAME}" "${_ENGINEER_RUNTIME_ROOT}/.claude/engineer/bin/${_ENGINEER_SHIM_NAME}" "${_ENGINEER_RUNTIME_ROOT}/.codex/engineer/bin/${_ENGINEER_SHIM_NAME}"; then engineer_run() { sh "$ENGINEER_TOOLS" "$@"; }; elif _engineer_homes; then engineer_run() { sh "$ENGINEER_TOOLS" "$@"; }; elif unset -f engineer_run; _G="$(command -v engineer_run)"; [ -n "$_G" ] && _engineer_id_ok "$_G"; then ENGINEER_TOOLS="$_G"; engineer_run() { "$ENGINEER_TOOLS" "$@"; }; else echo "ERROR: engineer_run not found at $ENGINEER_TOOLS and no identity-proving engineer_run is on PATH. Run: python -I bin/install.py --source <local-source> --ref <pinned-ref> --target <project-root> --host claude --local" >&2; exit 1; fi; ENGINEER_IDENTITY_STATUS=unverified; _engineer_id_ok engineer_run && ENGINEER_IDENTITY_STATUS=ok; export ENGINEER_IDENTITY_STATUS; [ "$ENGINEER_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$ENGINEER_TOOLS\" did not prove it is engineer-runtime - it is either a different package or an engineer-runtime older than the runtime-identity verb." >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${ENGINEER_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${ENGINEER_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
RESPONSE_LANGUAGE=$(engineer_run query config-get response_language --raw --default "" 2>/dev/null || echo "")
```

**If `response_language` is set:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated.

<step name="preflight">
Verify prerequisites:

1. **`gh` CLI available and authenticated?**
   ```bash
   which gh && gh auth status 2>&1
   ```
   If not available: print setup instructions and exit.

2. **Detect repository:**
   If `--repo` was provided, validate its `owner/repo` value and set `REPO` to
   that literal value. Otherwise set `REPO` from:
   ```bash
   gh repo view --json nameWithOwner -q '.nameWithOwner' 2>/dev/null
   ```
   If no repo detected: error - must be in a git repo with a GitHub remote.
   Pass `--repo "$REPO"` to every subsequent `gh` operation; an explicit target
   must not fall back to the current checkout's repository.

3. **Parse flags:**
   - `--issues` → set REVIEW_ISSUES=true, REVIEW_PRS=false
   - `--prs` → set REVIEW_ISSUES=false, REVIEW_PRS=true
   - `--label` → set AUTO_LABEL=true
   - `--close-incomplete` → set AUTO_CLOSE=true
   - Default (no flags): review both issues and PRs, report only (no auto-actions)
</step>

<step name="fetch_issues">
Skip if REVIEW_ISSUES=false.

Fetch open issues from the selected repository:
```bash
gh issue list --repo "$REPO" --state open --json number,title,labels,body,author,createdAt,updatedAt --limit 100
```

If the limit is reached, fetch the remaining pages before claiming all items
were reviewed, or report the unreviewed scope.

Classify using the issue's original intent, body, labels and prior/archived body
where necessary. Select one variant from the canonical issue template:

| Intent | Variant |
|---|---|
| Existing behavior is wrong or broken | Bug |
| New or improved capability | Enhancement |
| Blocked choice among options | Decision required |
| Security concern needing assessment or remediation | Security risk |
| Human validation of a delivered build | UAT |
| Ambiguous or conflicting evidence | Unknown; manual triage |

Preserve the existing intent; a bug found during UAT remains a Bug. Do not
classify by a title keyword alone or rewrite the body during report-only review.
</step>

<step name="review_issues">
Skip if REVIEW_ISSUES=false.

For each classified issue, compare its actual body with the selected variant's
File Template and full authoring guidance:
- Required headings, order, tables and result fields are present.
- Required fields contain concrete facts rather than unfilled prompts or examples.
- `N/A` has a reason; `Unknown` or `Pending` names the missing evidence/dependency.
- Scope, acceptance and safe evidence are actionable and consistent with intent.
- UAT retains actual or pending Human acceptance; formatting is not human acceptance.
- Security issues preserve risk key, aliases, assessment, owner, lifecycle and
  outcome evidence under the canonical Git workflow.

Report structural completeness separately from factual verification. Missing
access or evidence is a gap, not proof that a claim is false or resolved.
Recommend labels only when the target repository actually uses them.

**Scoring:** Count applicable required fields present vs. total required fields.
Score = (present / total) * 100. Status: COMPLETE (100%), MOSTLY COMPLETE
(75-99%), INCOMPLETE (50-74%), REJECT (<50%). Record the denominator and missing
fields; a complete shape does not establish correctness or closure authority.
</step>

<step name="fetch_prs">
Skip if REVIEW_PRS=false.

Fetch open PRs from the selected repository:
```bash
gh pr list --repo "$REPO" --state open --json number,title,labels,body,author,headRefName,baseRefName,isDraft,createdAt,updatedAt,reviewDecision,statusCheckRollup --limit 100
```

If the limit is reached, fetch remaining pages or report the unreviewed scope.
Use the shared canonical pull request template for every PR; there is no
mandatory feature/enhancement/fix PR template.

Identify all issue links, including neutral links and closing references.
Read linked issues in their actual repositories to check scope and observed
state. A missing Requirements or Issues section is permitted when none apply.
</step>

<step name="review_prs">
Skip if REVIEW_PRS=false.

Review each PR against the shared canonical template:
- [ ] Goal and owned Changes explain the authorized outcome.
- [ ] Verification names the full candidate/tested revisions and exact checks,
      observed results and matching evidence, or truthful Pending dependencies.
- [ ] Known gaps states unfinished acceptance, missing review or checks.
- [ ] Risks or rollback gives inspected risks and a practical rollback.
- [ ] Requirements or Issues is present only when applicable.
- [ ] Stack is present only for an actual dependency, with its required fields.
- [ ] No unfilled prompts or invented evidence remain.
- [ ] Issue links preserve scope and actual unresolved/accepted/deferred/resolved
      status; closing references meet the canonical Git workflow's acceptance
      and closure-authority requirements.
- [ ] Required checks and applicable independent review are current at the actual
      PR head, or explicitly Pending.
- [ ] The title is descriptive and the diff has no unrelated changes.

Apply additional contribution requirements only when verified in the target
repository. Do not require approval labels, typed PR templates, closing links or
changesets merely because this workflow once named them.

**Scoring:** Use applicable required fields as for issues. Report draft state,
CI, review and evidence gaps separately; a score does not establish merge eligibility.
</step>

<step name="check_gates">
Check the canonical Git workflow and any verified target-repository requirements:
1. Distinguish published, verified and merged states. A tracking draft with
   truthful Pending evidence is not a readiness claim.
2. Verify applicable issue links and full-scope acceptance. Missing issue links
   alone are not a violation when no requirement or issue applies.
3. Flag premature closing references, unsupported readiness claims and actual
   unmet repository requirements, naming the source and missing evidence.
4. Keep user merge authorization distinct from completeness, approval and CI.
   Inbox review never merges a PR or grants merge or issue-closure authority.
</step>

<step name="generate_report">
Produce a structured triage report:

```
===================================================================
  Engineer INBOX TRIAGE — {repo} — {date}
===================================================================

SUMMARY
-------
Open issues: {count}    Open PRs: {count}
  Bugs:        {n}        Draft PRs:        {n}
  Enhancements:{n}        Template gaps:    {n}
  Decisions:   {n}        Evidence gaps:    {n}
  Security:    {n}        Requirements:     {n}
  UAT:         {n}        Unverified links: {n}
  Unclassified:{n}

WORKFLOW FINDINGS (review required)
---------------------------------
{For each violation:}
  PR #{number}: {title}
    Problem: {actual unmet requirement and its source, or missing evidence}
    Action:  {bounded corrective next step}

ISSUES NEEDING ATTENTION
------------------------
{For each issue sorted by completeness score, lowest first:}
  #{number} [{type}] {title}
    Score: {percentage}% complete
    Missing: {list of missing required fields}
    Labels: {current labels} → Suggested: {recommended labels}
    Age: {days since created}

PRS NEEDING ATTENTION
---------------------
{For each PR sorted by completeness score, lowest first:}
  #{number} [{type}] {title}
    Score: {percentage}% complete
    Missing: {list of missing checklist items}
    CI: {passing/failing/pending}
    Review: {approved/changes_requested/none}
    Linked issues: {verified URLs and observed states, None applicable, or Pending}
    Age: {days since created}

REVIEW AND VERIFICATION STATUS
------------------------------
{For each PR:}
  #{number} {title} - {draft/current verification/review/check status and gaps}
  Merge authority: {actual authorization or unavailable; no merge performed}

STALE ITEMS (>30 days, no activity)
------------------------------------
{Issues and PRs with no updates in 30+ days}

===================================================================
```

Print the report in the conversation. Do not automatically create a transient
planning file for inbox triage.
</step>

<step name="auto_actions">
Only execute if `--label` or `--close-incomplete` flags were set.

**If --label:**
For each issue/PR where labels are missing or incorrect:
```bash
gh issue edit {number} --repo "$REPO" --add-label "{label}"
```
Or:
```bash
gh pr edit {number} --repo "$REPO" --add-label "{label}"
```

Apply only recommended labels verified as appropriate in the target repository.
Do not create approval or gate labels as a substitute for canonical evidence.

**If --close-incomplete:**
Completeness scores identify candidates for review, not automatic issue closure.
The canonical Git workflow requires demonstrated acceptance and closure authority
before closing an issue. Keep unresolved, accepted and deferred work open.
After the required confirmation and only for an eligible selected issue:
```bash
gh issue close {number} --repo "$REPO" --comment "{reviewed safe acceptance evidence and authorized closure reason}"
```

For a PR selected for closure under the verified repository policy and confirmed
by the user:
```bash
gh pr close {number} --repo "$REPO" --comment "{reviewed safe reason and actual unmet requirement}"
```

Always confirm with the user before closing anything:

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex) where `AskUserQuestion` is not available.

```
AskUserQuestion:
  question: "Found {N} items to close. Review the list above — proceed with closing?"
  options:
    - label: "Close all"
      description: "Close all {N} eligible selected items with reviewed explanations"
    - label: "Let me pick"
      description: "I'll choose which ones to close"
    - label: "Skip"
      description: "Don't close anything — report only"
```
</step>

<step name="report">
```
---

## Inbox Triage Complete

Reviewed: {issue_count} issues, {pr_count} PRs
Workflow findings: {finding_count}
Verification/review gaps: {gap_count}
Needing attention: {attention_count}
Stale (30+ days): {stale_count}

Next steps:
- Review findings against the cited canonical or repository-specific requirement
- Address incomplete submissions under the authorized scope
- Resolve verification/review gaps; leave merge decisions to the user
- Triage unclassified issues

---
```
</step>

</process>

<offer_next>
After triage:

- /code-review - Review source changes for a specific phase
- /ship — Create a PR from completed work
- /progress — See overall project state
- /inbox --label — Re-run with auto-labeling enabled
</offer_next>

<success_criteria>
- [ ] All open issues fetched and classified by type
- [ ] Each issue reviewed against its template requirements
- [ ] All open PRs fetched and classified by type
- [ ] Each PR reviewed against its template checklist
- [ ] Findings cite actual canonical or target-repository requirements
- [ ] Structured report generated with scores and action items
- [ ] Auto-actions executed only when flagged and user-confirmed
</success_criteria>
