<!-- workflow: native orchestrator and declared agents -->
<purpose>
Create a pull request from completed phase/milestone work, generate a rich PR body from planning artifacts, optionally run code review, and prepare for merge. Closes the plan → execute → verify → ship loop.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<available_agent_types>
Valid Engineer subagent types (use exact names — do not fall back to 'general-purpose'):
</available_agent_types>

<process>

<step name="initialize">
Parse arguments and load project state:

```bash
IFS= read -rd '' ENGINEER_ARGS <<'ENGINEER_ARGS_END' || true
$ARGUMENTS
ENGINEER_ARGS_END
ENGINEER_ARGS=${ENGINEER_ARGS%$'\n'}
_engineer_identity_ok() {
  [ -f "$1" ] || return 1
  [ "$(sh "$1" query runtime-identity --pick packageName --raw 2>/dev/null)" = "engineer-runtime" ]
}
_engineer_select() {
  for _engineer_candidate do
    if _engineer_identity_ok "$_engineer_candidate"; then
      ENGINEER_RUN="$_engineer_candidate"
      return 0
    fi
  done
  return 1
}
if [ -n "${ENGINEER_RUN:-}" ]; then
  _engineer_identity_ok "$ENGINEER_RUN" || {
    printf '%s\n' "ERROR: ENGINEER_RUN does not identify engineer-runtime: $ENGINEER_RUN" >&2
    exit 1
  }
else
  _engineer_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
  _engineer_runtime_root=${RUNTIME_DIR:-$_engineer_root}
  _engineer_path_candidate=$(command -v engineer_run 2>/dev/null || true)
  _engineer_select \
    "$_engineer_root/engineer/bin/engineer_run" \
    "$_engineer_runtime_root/engineer/bin/engineer_run" \
    "$_engineer_root/.claude/engineer/bin/engineer_run" \
    "$_engineer_root/.codex/engineer/bin/engineer_run" \
    "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/engineer/bin/engineer_run" \
    "${CODEX_HOME:-$HOME/.codex}/engineer/bin/engineer_run" \
    "$_engineer_path_candidate" || {
    printf '%s\n' 'ERROR: No engineer-runtime launcher was found. Install the Claude or Codex workflow runtime or set ENGINEER_RUN.' >&2
    exit 1
  }
fi
export ENGINEER_RUN
engineer_run() {
  sh "$ENGINEER_RUN" "$@"
}
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  _engineer_path_escaped=$(printf '%s' "${ENGINEER_RUN%/*}" | sed 's/[\\`"$]/\\&/g')
  printf 'export PATH="%s:$PATH"\n' "$_engineer_path_escaped" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true
fi
RESPONSE_LANGUAGE=$(engineer_run query config-get response_language --raw --default "" 2>/dev/null || echo "")
PHASE_ARG=$(echo "$ENGINEER_ARGS" | xargs)
INIT=$(engineer_run query init.phase-op  "${PHASE_ARG}")
```

**If `response_language` is set:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated.

Parse from init JSON: `phase_found`, `phase_dir`, `phase_number`, `phase_name`, `padded_phase`, `commit_docs`.

Also load config for branching strategy:
```bash
CONFIG=$(engineer_run query state.load)
```

Extract: `branching_strategy`, `branch_name`.

Detect base branch for PRs and merges:
```bash
BASE_BRANCH=$(engineer_run query git.base-branch)
```
</step>

<step name="preflight_checks">
Verify the work is ready to ship:

1. **Verification passed?**
   ```bash
   # The gate decides on ONE read. --pick takes a single field, so the two
   # human-facing fields are read only on the blocking path below — never on the
   # passing path — rather than issuing three queries up front.
   # Stderr is kept; a failed read stops shipping — it is never "no status".
   STATUS=$(engineer_run query verification.status "${PHASE_DIR}" --pick status) || { echo "verification.status refused this phase's report — see the error above. Fix it before shipping." >&2; exit 1; }
   ```
   Only `passed` may ship. If `$STATUS` is `passed`, verification is complete — continue to the next preflight check; do not read any further verification field. A non-zero exit above is a hard error (a report `status` outside `passed | gaps_found | human_needed`): present the error and stop.

   Any other value (including `gaps_found`, `human_needed`, `stale`, `missing`, and `phase_dir_not_found`) blocks with `PHASE_VERIFICATION_INCOMPLETE`. Only then, read the two message fields:
   ```bash
   NEXT_ACTION=$(engineer_run query verification.status "${PHASE_DIR}" --pick next_action) || exit 1
   NEXT_COMMAND=$(engineer_run query verification.status "${PHASE_DIR}" --pick next_command) || exit 1
   ```
   Present `$NEXT_ACTION` to the user and, when `$NEXT_COMMAND` is non-empty, show it as the command to run next. These two are message text only — the block/allow decision has already been made from `$STATUS`, so a concurrent write between the reads cannot change the gate's verdict. The query already covers every status in its closed set, so no per-status arm is needed.

2. **Clean working tree?**
   ```bash
   git status --short
   ```
   If uncommitted changes exist: ask user to commit or stash first.

3. **On correct branch?**
   ```bash
   CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || true)
   IS_PROTECTED=$(engineer_run query git.base-branch --is-protected "$CURRENT_BRANCH") || IS_PROTECTED=""
   if [ "$IS_PROTECTED" = true ]; then
     echo "⚠ Current branch '$CURRENT_BRANCH' is a protected branch; shipping should happen from a feature branch." >&2
   elif [ -z "$IS_PROTECTED" ]; then
     echo "⚠ Could not determine whether '$CURRENT_BRANCH' is protected — the query failed. Continuing." >&2
   fi
   ```
   If `IS_PROTECTED` is `true`: warn — should be on a feature branch.
   If branching_strategy is `none`: offer to create a branch now.

4. **Remote configured?**
   ```bash
   git remote -v | head -2
   ```
   Detect `origin` remote. If no remote: error — can't create PR.

5. **`gh` CLI available?**
   ```bash
   which gh && gh auth status 2>&1
   ```
   If `gh` not found or not authenticated: provide setup instructions and exit.

</step>

<step name="push_branch">
Push the current branch to remote:

```bash
git push origin ${CURRENT_BRANCH} 2>&1
```

If push fails (e.g., no upstream): set upstream:
```bash
git push --set-upstream origin ${CURRENT_BRANCH} 2>&1
```

Report: "Pushed `{branch}` to origin ({commit_count} commits ahead of ${BASE_BRANCH})"
</step>

<step name="generate_pr_body">
Use the canonical Git workflow and existing PR template. Fill its required sections from the planning artifacts and preserve the TDD audit evidence below.

**1. Title:**
```
Phase {phase_number}: {phase_name}
```
Or for milestone: `Milestone {version}: {name}`

**2. Summary section:**
Read ROADMAP.md for phase goal. Read VERIFICATION.md for verification status.

```markdown
## Summary

**Phase {N}: {Name}**
**Goal:** {goal from ROADMAP.md}
**Status:** Verified ✓

{One paragraph synthesized from SUMMARY.md files — what was built}
```

**3. Changes section:**
For each SUMMARY.md in the phase directory:
```markdown
## Changes

### Plan {plan_id}: {plan_name}
{one_liner from SUMMARY.md frontmatter}

**Key files:**
{key-files.created and key-files.modified from SUMMARY.md frontmatter}
```

**4. Requirements section:**
```markdown
## Requirements Addressed

{REQ-IDs from plan frontmatter, linked to REQUIREMENTS.md descriptions}
```

**5. Testing section:**
```markdown
## Verification

- [x] Automated verification: {pass/fail from VERIFICATION.md}
- {human verification items from VERIFICATION.md, if any}
```

**6. Decisions section:**
```markdown
## Key Decisions

{Decisions from STATE.md accumulated context relevant to this phase}
```


**8. TDD Audit section:**

Reconstruct the per-commit TDD gate trail before squash-merge discards it. Walk the PR branch's own commits (merges excluded) and read each commit's `gate-status:` trailer with Git's native trailer machinery — never a raw `%B` grep, which would also match the string written in prose:

```bash
# Anchor on the merge-base so a stale local ${BASE_BRANCH} ref cannot over-count.
RANGE_BASE=$(git merge-base "${BASE_BRANCH}" HEAD)
git log "${RANGE_BASE}..HEAD" --no-merges --reverse \
  --format='%H%x1f%s%x1f%(trailers:key=gate-status,valueonly,separator=%x2c)%x1e'
```

Records are separated by `\x1e`; the fields inside each are `\x1f`-separated — `<sha>`, `<subject>`, `<gate-status value>`.

Pair commits by their conventional-commit type (the `type:` prefix of the subject):

- A `test:` commit is the RED row. Pair it with the next following **implementation** commit — a `feat:` or `fix:` — as its **Impl commit** (the GREEN step), skipping over any intervening `refactor:`, `docs:`, or `chore:` commits so they are never mistaken for the GREEN step.
- A `refactor:`, `docs:`, or `chore:` commit that is not consumed as an Impl pairing is a standalone row with Impl commit `—`.
- A `feat:`/`fix:` commit with no preceding unpaired `test:` is a standalone row.

Surface each commit's `gate-status:` value, normalized to exactly one of `skill`, `fallback`, `exempt`, or `missing` — never the raw trailer text. A commit whose trailer is absent, whose value is none of the first three, or which carries more than one `gate-status:` trailer (ambiguous) is counted as **missing** and still listed. This section is informational; it never blocks the ship.

**Self-suppress when every commit is missing:** the execute pipeline only writes `gate-status:` trailers when TDD mode is active. If every commit in the scan normalizes to `missing`, skip this section and the aggregate trailer (step 9) entirely — a 100%-missing table is pure noise. Only emit when at least one commit carries a real value (`skill`, `fallback`, or `exempt`).

Harden every table cell against injection, not just subjects: escape `|` as `\|` and strip `\r`/`\n` from both commit subjects and the rendered `gate-status` value. Prefer NUL (`-z` / `%x00`) record separation, and reject any record whose fields contain the `\x1f`/`\x1e` delimiters, so an adversarial commit message cannot corrupt record or field boundaries.

```markdown
## TDD Audit

| Test commit | Impl commit | gate-status |
|---|---|---|
| `a1b2c3d` test: failing parser test | `e4f5g6h` feat: implement parser | skill |
| `i7j8k9l` test: failing export test | `m0n1o2p` feat: implement export | fallback |
| `q3r4s5t` refactor: extract helper | — | exempt |

Aggregate: 2 skill, 1 fallback, 1 exempt — 0 missing.
```

This `## TDD Audit` section follows the canonical PR sections and precedes the aggregate trailer.

**9. Aggregate gate-status trailer (final line)** (only when step 8 was emitted — i.e., at least one real `gate-status` value exists):

After every other section emit the audit aggregate as a single Git trailer on the **final line** of the PR body, preceded by a blank line so it parses as a valid trailer:

```
gate-status: skill=2, fallback=1, exempt=1, missing=0
```

Use the exact key order `skill=`, `fallback=`, `exempt=`, `missing=` so downstream tooling parses it stably. Keeping it last means a GitHub squash-merge that defaults its commit message to the PR description carries the aggregate into `${BASE_BRANCH}`, preserving the audit footprint in `git log` after the PR branch is deleted. (Best-effort: it depends on the repo's squash-message default; the in-body `## TDD Audit` section is the source of truth regardless.)
</step>

<step name="create_pr">
Create the PR using the generated body. Write the body to a temp file first so the canonical PR body do not hit shell argument limits:

```bash
# BSD/macOS mktemp only randomizes XXXXXX when it is the final path component, so make a
# suffixless temp then append the extension — portable across BSD + GNU.
PR_BODY_FILE=$(mktemp "${TMPDIR:-/tmp}/engineer-pr-body-XXXXXX") && mv "$PR_BODY_FILE" "${PR_BODY_FILE}.md" && PR_BODY_FILE="${PR_BODY_FILE}.md" || exit 1
trap 'rm -f "${PR_BODY_FILE:-}"' EXIT
printf '%s\n' "${PR_BODY}" > "${PR_BODY_FILE}"

gh pr create \
  --title "Phase ${PHASE_NUMBER}: ${PHASE_NAME}" \
  --body-file "${PR_BODY_FILE}" \
  --base "${BASE_BRANCH}"
```

If `--draft` flag was passed: add `--draft`.

Report: "PR #{number} created: {url}"
</step>

<step name="optional_review">


---

**Manual review options:**

Ask if user wants to trigger a code review:

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex) where `AskUserQuestion` is not available.

```
AskUserQuestion:
  question: "PR created. Run a code review before merge?"
  options:
    - label: "Skip review"
      description: "PR is ready — merge when CI passes"
    - label: "Self-review"
      description: "I'll review the diff in the PR myself"
    - label: "Request review"
      description: "Request review from a teammate"
```

**If "Request review":**
```bash
gh pr edit ${PR_NUMBER} --add-reviewer "${REVIEWER}"
```

**If "Self-review":**
Report the PR URL and suggest: "Review the diff at {url}/files"
</step>

<step name="track_shipping">
Update STATE.md to reflect the shipping action. Write the activity line only, with its description; do not write `Status`. At ship time the Current Position block already describes the next phase, and `Status` feeds the frontmatter `status` field, so a free-text value such as "Phase N shipped" does not belong there.

```bash
engineer_run query state.update "Last Activity" "$(date +%Y-%m-%d) -- Phase ${PHASE_NUMBER} shipped as PR #${PR_NUMBER}"
```

If `commit_docs` is true, commit the ship-note AND push it onto the PR branch so
it reaches the default branch when the PR merges. Without this push the ship-note
commit stays local-only and is silently discarded when the branch is deleted on
merge. The `[ci skip]` trailer suppresses the redundant pipeline the push
would otherwise trigger (GitHub honors `[ci skip]` / `[skip ci]`):

```bash
engineer_run query commit "docs(${padded_phase}): ship phase ${PHASE_NUMBER} — PR #${PR_NUMBER} [ci skip]" --files .planning/STATE.md
SHIP_NOTE_SHA=$(git rev-parse HEAD)
git push origin ${CURRENT_BRANCH} 2>&1 || echo "⚠ track_shipping: ship-note push failed — it is local-only; rerun: git push origin ${CURRENT_BRANCH}"

# Preserve the skip-token optimization for repositories without a required-check
# wedge; only synthesize a second CI-triggering commit when GitHub reports one.
# Poll mergeStateStatus with backoff to avoid racing GitHub's async state computation.
# Note: Skip tokens recognized by GitHub Actions are [skip ci], [ci skip], [no ci], [skip actions], [actions skip], and skip-checks:true.
# The recovery commit message MUST NOT contain any of these tokens.
# Recovery keys on the head only (BLOCKED, zero checks, skip token), never the review state.

STATUS="UNKNOWN"
CHECKS=0
for i in {1..5}; do
  PR_STATE=$(gh pr view ${PR_NUMBER} --json headRefOid,mergeStateStatus,statusCheckRollup -q '{head: .headRefOid, status: .mergeStateStatus, checks: ((.statusCheckRollup // []) | length)}' 2>/dev/null || echo '{"head":"","status":"UNKNOWN","checks":0}')
  HEAD_OID=$(echo "$PR_STATE" | jq -r .head)
  if [ "$HEAD_OID" = "$SHIP_NOTE_SHA" ]; then
    STATUS=$(echo "$PR_STATE" | jq -r .status)
    CHECKS=$(echo "$PR_STATE" | jq -r .checks)
  fi
  if [ "$HEAD_OID" = "$SHIP_NOTE_SHA" ] && [ "$STATUS" != "UNKNOWN" ]; then
    break
  fi
  sleep 3
done

if [ "$STATUS" = "BLOCKED" ] && [ "$CHECKS" = "0" ] && git log -1 --format=%B "$SHIP_NOTE_SHA" | grep -q '\[ci skip\]'; then
  echo "⚠ PR is BLOCKED with zero checks. The [ci skip] trailer wedged the PR due to required checks."
  echo "Pushing an empty commit to trigger the required pipelines..."
  # engineer_run query commit requires a file list; use git directly for this intentionally empty commit.
  git commit --allow-empty -m "chore: trigger CI (recover from ship-note skip-token)"
  git push origin ${CURRENT_BRANCH} 2>&1 || echo "⚠ track_shipping: recovery push failed — rerun: git push origin ${CURRENT_BRANCH}"
elif [ "$STATUS" = "UNKNOWN" ]; then
  echo "⚠ track_shipping: PR mergeStateStatus is UNKNOWN after polling; PR may require manual check re-trigger."
fi
```
</step>


<step name="report">
```
---

## ✓ Phase {X}: {Name} — Shipped

PR: #{number} ({url})
Branch: {branch} → ${BASE_BRANCH}
Commits: {count}
Verification: ✓ Passed
Requirements: {N} REQ-IDs addressed

Next steps:
- Review/approve PR
- Merge when CI passes
- /complete-milestone (if last phase in milestone)
- /progress (to see what's next)

---
```
</step>

</process>

<offer_next>
After shipping:

- /complete-milestone — if all phases in milestone are done
- /progress — see overall project state
- /execute-phase {next} — continue to next phase
</offer_next>

<success_criteria>
- [ ] Preflight checks passed (verification, clean tree, branch, remote, gh)
- [ ] Branch pushed to remote
- [ ] PR created with rich auto-generated body
- [ ] STATE.md updated with shipping status
- [ ] User knows PR number and next steps
</success_criteria>
