<!-- workflow
step: ship
agent-roles: orchestrator, code-reviewer
produces: pushed branch, pull request
consumes: VERIFICATION.md, SUMMARY.md, ROADMAP.md, STATE.md
-->

<purpose>
Publish verified work as a pull request. Confirms the phase actually passed
verification, checks the tree and remote are in a fit state, composes a PR body
from the phase's own records, and opens or updates the PR.

Shipping publishes. It does not merge, and it does not decide that unverified
work is good enough.
</purpose>

<required_reading>
@~/.ai/references/universal-anti-patterns.md
</required_reading>

<available_agent_types>
Valid subagent types (use these exact names — never fall back to a generic agent):
- code-reviewer — reviews the changes being published
</available_agent_types>

<model_selection>
Models are injected inline at dispatch, never read from an agent's frontmatter.
Resolve each agent's model from the runtime and pass it on the `Agent(...)` call:

```bash
phase_run query resolve-model <agent> --raw
```

A result of `inherit` means the project set no override — **omit the `model`
argument entirely** in that case and let the host choose. Pass `model` only when
resolution returned a concrete model name. The `models` map in each init bundle
carries the same resolved values for every agent that workflow dispatches.
</model_selection>

<process>

<step name="initialize">
Parse `$ARGUMENTS`: an optional phase number, plus:
- `--draft` — open the PR as a draft
- `--review` — run a code review over the full diff before opening the PR
- `--no-push` — compose and show the PR body without pushing or opening anything

```bash
_root="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
for _c in "$_root"/.{ai,claude,codex}/runtime/phase.py "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/runtime/phase.py "${CODEX_HOME:-$HOME/.codex}"/runtime/phase.py; do
  [ -f "$_c" ] && PHASE_RUNTIME="$_c" && break
done
[ -n "${PHASE_RUNTIME:-}" ] || { echo "ERROR: phase runtime not found; run the installer." >&2; exit 1; }
phase_run() { "$(command -v python3 || command -v python)" "$PHASE_RUNTIME" "$@"; }
INIT=$(phase_run query init.ship "${PHASE}")
```

Extract: `phase_found`, `phase_number`, `padded_phase`, `phase_name`, `phase_dir`,
`goal`, `artifacts`, `verification`, `checks`, `checks_configured`, `git`
(`base_branch`, `current_branch`, `is_protected`, `has_remote`), `commit_docs`,
`response_language`.

**If `response_language` is set:** all user-facing output MUST be presented in
`{response_language}`; technical terms, code, file paths and commit/PR text stay
in English.

Display: `► SHIP PHASE {phase_number}: {phase_name}`
</step>

<step name="preflight_checks">
Verify the work is ready to publish. Every check below blocks; none is advisory.

1. **Verification passed.**

   ```bash
   phase_run query verification.status "${phase_number}"
   ```

   Only `status: passed` may ship. Any other value — `gaps_found`,
   `human_needed`, or no report at all — blocks:

   ```
   Cannot ship Phase {N}: verification is {status or "missing"}.

   Run `/verify-work {N}` and resolve its findings first.
   ```

   Exit. Do not offer a bypass: an unverified PR is exactly what this gate exists
   to prevent.

   Also compare the report's `revision` to the current HEAD. If the code moved
   since verification, the report is stale — say so and require re-verification.

2. **Clean working tree.**

   ```bash
   git status --short
   ```

   If there are uncommitted changes, ask the user to commit or stash them first.
   Shipping over a dirty tree publishes something nobody reviewed.

3. **Not on a protected branch.**

   If `git.is_protected` is true, the current branch is the base branch. Offer to
   create a feature branch from here:

   ```bash
   git switch -c "phase/${padded_phase}-${phase_slug}"
   ```

4. **Remote configured.**

   If `git.has_remote` is false:

   ```
   No `origin` remote configured — there is nowhere to open a pull request.
   ```

   Exit.

5. **`gh` available and authenticated.**

   ```bash
   gh auth status
   ```

   If `gh` is missing or unauthenticated, report the setup steps and exit.

6. **Configured checks pass.**

   ```bash
   phase_run query verification.run-checks
   ```

   A failing check blocks. Report the command and its output tail.
</step>

<step name="optional_review">
**Only when `--review` was passed.**

```
Agent(
  prompt="
Review everything Phase {phase_number} is about to publish.

**Diff:** {base_branch}...HEAD
**Phase goal:** {goal}

Review the changed source for correctness bugs, security issues and anything a
reviewer on the PR would rightly object to. Judge the code as it stands.

Return:
## REVIEW
Findings: <numbered, each with file:line and severity (critical|warning)>
",
  subagent_type="code-reviewer",
  ${models['code-reviewer'] === 'inherit' ? '' : `model="${models['code-reviewer']}",`}
  description="Pre-ship review of phase {phase_number}"
)
```

Critical findings block the PR. Fix them, re-verify, and start again — do not
publish with a known critical finding and a note about it.
</step>

<step name="push_branch">
**Skip when `--no-push` was passed.**

```bash
git push -u origin "$(git branch --show-current)"
```

If the push is rejected because the remote moved, report it and stop. Do not
force-push: the remote branch may hold work you cannot see.
</step>

<step name="generate_pr_body">
Compose the PR body from the phase's own records — its summaries and verification
report — rather than from the diff. A reader wants to know what shipped and what
was confirmed, not a file list.

```markdown
## Phase {N}: {phase_name}

{goal}

### What shipped

{For each {padded_phase}-{MM}-SUMMARY.md: one line naming the plan and what it
delivered.}

### Requirements covered

{Each REQ id claimed by the phase, and where it is satisfied.}

### Verification

Status: {verification.status} (revision {verification.revision})

{The Acceptance section from VERIFICATION.md: what was confirmed, and how.}

{If checks are configured:}
Checks: {each command and its result}

{If the report recorded accepted gaps:}
### Known gaps

{Each one, with why it was accepted rather than closed.}
```

Show the composed body to the user before opening the PR.
</step>

<step name="create_pr">
**Skip when `--no-push` was passed.**

```bash
gh pr create \
  --base "${git.base_branch}" \
  --title "Phase ${phase_number}: ${phase_name}" \
  --body-file "${body_path}" \
  ${draft:+--draft}
```

If a PR already exists for this branch, update it instead:

```bash
gh pr edit --title "..." --body-file "${body_path}"
```

Opening a PR can start CI. It does not mean the checks have finished, and it
never means the PR is ready to merge. Report the URL and the check state as
observed, not as assumed:

```bash
gh pr view --json url,state,statusCheckRollup
```
</step>

<step name="track_shipping">
Record the publication against the phase:

```bash
phase_run query state.record-session \
  --stopped-at "Phase ${phase_number} shipped: ${pr_url}" \
  --status "Shipped"
phase_run query state.add-decision "Phase ${phase_number} published as ${pr_url}"
phase_run query commit "docs(state): record phase ${phase_number} publication" \
  --files .planning/STATE.md
```
</step>

<step name="report">
```
Phase {phase_number} shipped.

PR: {url} ({draft ? "draft" : "ready for review"})
Base: {base_branch}
Verification: passed (revision {revision})
Checks: {observed state, or "none configured"}

---

## What's Next

- Watch the PR's checks; opening it may have started them
- `/progress` — where the project stands
- `/next` — continue with the next phase while this one is in review

Merging is not this workflow's job, and no command here moves the base branch.

---
```
</step>

</process>

<anti_patterns>
- Don't ship work whose verification is not `passed` — there is no bypass
- Don't ship against a stale verification report; code that moved needs re-verifying
- Don't force-push a branch that already exists on the remote
- Don't merge the PR or move the base branch
- Don't report CI as passing because the PR opened; report what `gh` observed
- Don't compose the PR body from the diff when the phase's own records say it better
- Don't ship over an uncommitted working tree
</anti_patterns>

<success_criteria>
- [ ] Verification confirmed `passed` and current for the revision being shipped
- [ ] Working tree clean, branch not the protected base, remote and `gh` available
- [ ] Configured checks run and passing
- [ ] Review run and critical findings resolved when `--review` was passed
- [ ] Branch pushed and the PR opened or updated
- [ ] PR body composed from the phase's summaries and verification report
- [ ] Check state reported as observed, never assumed
- [ ] Publication recorded in STATE.md and committed
</success_criteria>
