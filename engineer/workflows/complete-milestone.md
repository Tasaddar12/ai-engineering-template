<purpose>

Mark a shipped version (v1.0, v1.1, v2.0) as complete. Creates historical record in MILESTONES.md, reorganizes ROADMAP.md with milestone groupings.

</purpose>

<required_reading>

1. engineer/templates/milestone.md
2. engineer/templates/milestone.md
3. `.planning/ROADMAP.md`
4. `.planning/REQUIREMENTS.md`
5. `.planning/PROJECT.md`

</required_reading>

<archival_behavior>

When a milestone completes:

1. Extract full milestone details to `.planning/milestones/v[X.Y]-ROADMAP.md`
2. Archive requirements to `.planning/milestones/v[X.Y]-REQUIREMENTS.md`
3. Update ROADMAP.md — overwrite in place with milestone grouping (preserve Backlog section)
4. Safety commit archive files + updated ROADMAP.md, then `git rm REQUIREMENTS.md` (fresh for next milestone)
6. Offer to create next milestone inline
7. Archive UI artifacts (`*-UI-SPEC.md`, `*-UI-REVIEW.md`) alongside other phase documents
8. Clean up `.planning/ui-reviews/` screenshot files (binary assets, never archived)

**Context Efficiency:** Archives keep ROADMAP.md constant-size and REQUIREMENTS.md milestone-scoped.

**ROADMAP archive** uses `engineer/templates/milestone.md` — includes milestone header (status, phases, date), full phase details, milestone summary (decisions, issues, tech debt).

**REQUIREMENTS archive** contains all requirements marked complete with outcomes, traceability table with final status, notes on changed requirements.

</archival_behavior>

<process>


<step name="pre_close_artifact_audit">
Before proceeding with milestone close, run the comprehensive open artifact audit.

```bash
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
engineer_run query audit-open
```

**If `response_language` is set:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated.

If the output contains open items (any section with count > 0):

Display the full audit report to the user.

Then ask:
```
These items are open. Choose an action:
[R] Resolve — stop and fix items, then re-run /complete-milestone
[A] Acknowledge all — document as deferred and proceed with close
[C] Cancel — exit without closing
```

**If user chooses [A] (Acknowledge):** re-fetch `audit-open --json`, then acknowledge EVERY open item (across all categories — debug_sessions, threads, seeds, todos, quick_tasks, uat_gaps, verification_gaps, context_questions, deferred_items) through the `audit-open acknowledge` CLI writer, which is what actually suppresses each item starting at the next scan (the STATE.md `## Deferred Items` table is a disclosure record only). Any failed acknowledge call HALTS the close before proceeding — a refusal must never be silently discarded. After a clean pass, append one row per acknowledged item to STATE.md's `## Deferred Items` table (sanitized via `sanitizeForDisplay()`, never raw content), set `closeout_type=override_closeout`, and record a `Known verification overrides: {N} newly acknowledged, {M} carried forward` line in MILESTONES.md. Acknowledging is verdict-preserving and self-invalidating — it never rewrites the artifact's own status (except `deferred_items`), and the suppression lapses automatically the moment the artifact's state changes again (a reopened session, an edited gap, a re-triggered seed), resurfacing at the next audit.

If output shows all clear (no open items): set `closeout_type=verified_closeout` — but if any items are `acknowledged.total` from a PRIOR close, note that carried-forward suppression explicitly rather than implying everything was fixed this time.

<!-- engineer:protected -->
SECURITY: Audit JSON output is structured data from the `audit-open` query handler (same JSON contract as legacy `engineer_run query audit-open`) — validated and sanitized at source. The `audit-open acknowledge` writer is the only path that sets the `audit_acknowledged` suppression marker — it snapshots each artifact's current state itself from the identifiers passed on the command line, so this workflow never hand-authors the marker. When writing the STATE.md disclosure table, item identifiers, statuses, and deferred-item text are sanitized via `sanitizeForDisplay()` before inclusion. Never inject raw user-supplied content into STATE.md without sanitization.

</step>

<step name="verify_readiness">

**Use `init.manager` for canonical readiness check:**

```bash
IFS= read -rd '' ENGINEER_ARGS <<'ENGINEER_ARGS_END' || true
$ARGUMENTS
ENGINEER_ARGS_END
ENGINEER_ARGS=${ENGINEER_ARGS%$'\n'}
INIT_MANAGER=$(engineer_run query init.manager )
```

This returns all phases with implementation and verification projection. Use this to verify:
- Which phases belong to this milestone?
- `all_phases_verified`: all milestone phases have `phase_complete === true` and `verification_status === 'passed'`.
- `progress_percent` should be 100%.

Compute readiness from `INIT_MANAGER`, not from roadmap counts:

```bash
ALL_PHASES_VERIFIED=$(printf '%s' "$INIT_MANAGER" | jq -r '[
  .phases[] | select((.number | tostring | test("^999(\\.|$)") | not))
  | (.phase_complete == true and .verification_status == "passed")
] | all')
```

If not all_phases_verified, verified_closeout must not proceed. Set `closeout_type=override_closeout`, show each phase whose `phase_complete !== true` or `verification_status !== 'passed'`, and require an explicit user choice:
1. **Proceed anyway** — record verification overrides in MILESTONES.md/STATE.md
2. **Run verification first** — `/verify-work {phase}` or `/execute-phase {phase}`
3. **Abort** — return to development

Only set `closeout_type=verified_closeout` when `ALL_PHASES_VERIFIED` is `true`.

**Requirements completion check (REQUIRED before presenting):**

Parse REQUIREMENTS.md traceability table:
- Count total v1 requirements vs checked-off (`[x]`) requirements
- Identify any non-Complete rows in the traceability table

Present:

```
Milestone: [Name, e.g., "v1.0"]

Includes:
- Phase 1: Foundation (2/2 plans complete)
- Phase 2: Authentication (2/2 plans complete)
- Phase 3: Core Features (3/3 plans complete)
- Phase 4: Polish (1/1 plan complete)

Total: {phase_count} phases, {total_plans} plans
Verification: {all_phases_verified ? "all phases verified" : "override needed"}
Closeout type: {closeout_type}
Requirements: {N}/{M} v1 requirements checked off
```

**If requirements incomplete** (N < M):

```
⚠ Unchecked Requirements:

- [ ] {REQ-ID}: {description} (Phase {X})
- [ ] {REQ-ID}: {description} (Phase {Y})
```

MUST present 3 options:
1. **Proceed anyway** — mark milestone complete with known gaps
2. **Run audit first** — `/audit-milestone` to assess gap severity
3. **Abort** — return to development

If user selects "Proceed anyway": set `closeout_type=override_closeout`; note incomplete requirements in MILESTONES.md under `### Known Gaps` with REQ-IDs and descriptions.

<config-check>

```bash
cat .planning/config.json 2>/dev/null || true
```

</config-check>

<if mode="yolo">

```
⚡ Auto-approved: Milestone scope verification
[Show breakdown summary without prompting]
Proceeding to stats gathering...
```

Proceed to gather_stats.

</if>

<if mode="interactive" AND="gates.confirm_milestone_scope!= false">

```
Ready to mark this milestone as shipped?
(yes / wait / adjust scope)
```

Wait for confirmation.
- "adjust scope": Ask which phases to include.
- "wait": Stop, user returns when ready.

</if>

</step>

<step name="gather_stats">

Calculate milestone statistics:

```bash
git log --oneline --grep="feat(" | head -20
git diff --stat FIRST_COMMIT..LAST_COMMIT | tail -1
find . -name "*.swift" -o -name "*.ts" -o -name "*.py" | xargs wc -l 2>/dev/null || true
git log --format="%ai" FIRST_COMMIT | tail -1
git log --format="%ai" LAST_COMMIT | head -1
```

Present:

```
Milestone Stats:
- Phases: [X-Y]
- Plans: [Z] total
- Tasks: [N] total (from phase summaries)
- Files modified: [M]
- Lines of code: [LOC] [language]
- Timeline: [Days] days ([Start] → [End])
- Git range: feat(XX-XX) → feat(YY-YY)
```

</step>

<step name="extract_accomplishments">

Extract one-liners from SUMMARY.md files using summary-extract:

```bash
# Zsh aborts the block on an unmatched for-list glob (nomatch); bash passes it through. nullglob both.
shopt -s nullglob 2>/dev/null; setopt NULL_GLOB 2>/dev/null

# For each phase in milestone, extract one-liner
for summary in .planning/phases/*-*/*-SUMMARY.md; do
  [ -e "$summary" ] || continue
  engineer_run query summary-extract "$summary" --fields one_liner --pick one_liner
done
```

Extract 4-6 key accomplishments. Present:

```
Key accomplishments for this milestone:
1. [Achievement from phase 1]
2. [Achievement from phase 2]
3. [Achievement from phase 3]
4. [Achievement from phase 4]
5. [Achievement from phase 5]
```

</step>

<step name="create_milestone_entry">

**Note:** MILESTONES.md entry is now created automatically by `engineer_run query milestone.complete` in the archive_milestone step. The entry includes version, date, phase/plan/task counts, and accomplishments extracted from SUMMARY.md files.

If additional details are needed (e.g., user-provided "Delivered" summary, git range, LOC stats), add them manually after the CLI creates the base entry.

</step>

<step name="archive_milestone">

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex) where `AskUserQuestion` is not available.

**Quick-task archival (opt-in — NOT symmetrical with phase archival below):** unlike phase archival, quick-task archival is **opt-in, default OFF**. Doing nothing leaves `.planning/quick/` untouched, exactly like today's behavior. Decide this BEFORE calling `milestone complete` below, so the flag can be folded into that single invocation rather than issuing a second, redundant call.

If `.planning/quick/` contains at least one directory, ask:

AskUserQuestion: "Archive completed quick tasks into this milestone too?" with options: "Yes — archive quick tasks into v[X.Y]" | "Skip"

If "Yes": set `ARCHIVE_QUICK_FLAG="--archive-quick"`. If "Skip" (or `.planning/quick/` is empty): set `ARCHIVE_QUICK_FLAG=""`.


**Delegate archival to `engineer_run query milestone.complete`:**

```bash
ARCHIVE=$(engineer_run query milestone.complete "v[X.Y]" --name "[Milestone Name]" --confirm $ARCHIVE_QUICK_FLAG)
```

`--confirm` is required: the archive is irreversible (ROADMAP/REQUIREMENTS archived, phase
directories MOVED, STATE.md rewritten), so `milestone complete` refuses to mutate without it. This
workflow has already gathered the user's explicit intent by this step, so passing the flag here is
correct; `--dry-run` previews the exact move list without mutating if a preview is ever needed first.

The CLI handles:
- Creating `.planning/milestones/` directory
- Archiving ROADMAP.md to `milestones/v[X.Y]-ROADMAP.md`
- Archiving REQUIREMENTS.md to `milestones/v[X.Y]-REQUIREMENTS.md` with archive header
- Moving audit file to milestones if it exists
- Creating/appending MILESTONES.md entry with accomplishments from SUMMARY.md files
- Updating STATE.md (status, last activity)
- When `ARCHIVE_QUICK_FLAG` is `--archive-quick`: moving every directory under `.planning/quick/` into `.planning/milestones/v[X.Y]-quick/`, writing a `README.md` index into that archive directory (generated by scanning the archive directory itself), and archiving the corresponding runtime quick-task records

Extract from result: `version`, `date`, `phases`, `plans`, `tasks`, `accomplishments`, `archived`.

Verify: `✅ Milestone archived to .planning/milestones/`

**Known limit (quick-task archival):** there is no on-disk provenance recording which milestone a given quick task belonged to. Archival buckets **all** remaining `.planning/quick/*` into the completing milestone — a quick task that predates an earlier, unarchived milestone lands in the current bucket regardless.

Verify after `--archive-quick` was passed: `✅ Quick tasks archived to .planning/milestones/v[X.Y]-quick/`

**Phase archival (default-on):** `milestone complete` archives phase directories to `milestones/v[X.Y]-phases/` by default, so the next `/new-milestone` never inherits un-archived dirs. No manual `mkdir`/`mv` or `--archive-phases` flag is needed.

If the user explicitly wants to keep phase directories in place as raw execution history, invoke `milestone complete` with `--no-archive-phases`:

```bash
engineer_run query milestone complete v[X.Y] --no-archive-phases --confirm
```


Verify after a default (archived) completion: `✅ Phase directories archived to .planning/milestones/v[X.Y]-phases/`

After archival, the AI still handles:
- Reorganizing ROADMAP.md with milestone grouping (requires judgment) — overwrite in place after extracting Backlog section, with the write-guard's single-use sentinel armed first (a per-step env var cannot reach a hook — see the reorganize step for the sentinel mechanics)
- Safety commit of archive files + updated ROADMAP.md, then `git rm .planning/REQUIREMENTS.md`
- These are NOT fully delegated because they require AI interpretation of content

</step>

<step name="reorganize_roadmap_and_delete_originals">

After `milestone complete` has archived, reorganize ROADMAP.md with milestone groupings, then commit archives as a safety checkpoint before removing originals.

**Backlog preservation — do this FIRST before rewriting ROADMAP.md:**

Extract the Backlog section from the current ROADMAP.md before making any changes:

```bash
IFS= read -rd '' ENGINEER_ARGS <<'ENGINEER_ARGS_END' || true
$ARGUMENTS
ENGINEER_ARGS_END
ENGINEER_ARGS=${ENGINEER_ARGS%$'\n'}
INIT_REORG=$(engineer_run query init.complete-milestone )
_engineer_field() { value=$(printf '%s' "$1" | engineer_run query json.get --field "$2" --default '""' --raw) || return $?; [ "$value" = null ] && value=""; printf '%s' "$value"; }
ROADMAP_PATH=$(_engineer_field "$INIT_REORG" roadmap_path)
# Extract lines under ## Backlog through end of file (or next ## section)
BACKLOG_SECTION=$(awk '/^## Backlog/{found=1} found{print}' "$ROADMAP_PATH")
```

If `$BACKLOG_SECTION` is empty, there is no Backlog section — skip silently.

**Reorganize ROADMAP.md** — overwrite in place (do NOT delete first) with milestone groupings.

This rewrite is an *intentional* catastrophic shrink: phase detail was just archived to `milestones/v[X.Y]-ROADMAP.md`, and a multi-hundred-line ROADMAP.md collapses to a compact grouped summary. The `engineer-write-guard` PreToolUse hook hard-blocks exactly that shape on curated `.planning/` files — this step is the legitimate milestone reset its escape hatch exists for. A hook inherits the *runtime's* environment, so no per-step env var can reach it; the hatch is a **single-use sentinel file the guard itself consumes**. Arm it, then write:

1. Arm the sentinel (single-use; the guard checks it is fresh — within 15 minutes — and names exactly this file, then consumes it):

```bash
IFS= read -rd '' ENGINEER_ARGS <<'ENGINEER_ARGS_END' || true
$ARGUMENTS
ENGINEER_ARGS_END
ENGINEER_ARGS=${ENGINEER_ARGS%$'\n'}
INIT_REORG=$(engineer_run query init.complete-milestone )
_engineer_field() { value=$(printf '%s' "$1" | engineer_run query json.get --field "$2" --default '""' --raw) || return $?; [ "$value" = null ] && value=""; printf '%s' "$value"; }
ROADMAP_PATH=$(_engineer_field "$INIT_REORG" roadmap_path)
printf '%s\n' "$ROADMAP_PATH" > .planning/.engineer-allow-shrink
echo "Write target: $ROADMAP_PATH"
```

2. Compose the full new ROADMAP.md content (template below) and overwrite the file at **`$ROADMAP_PATH`** (the runtime-resolved write target) with the **Write tool** — the normal path. The guard allows this one shrink and deletes the sentinel. If the Write is blocked anyway, the sentinel was stale or consumed — re-run the `printf` and retry the Write.

Template for the composed content:

```markdown
# Roadmap: [Project Name]

## Milestones

- ✅ **v1.0** — Phases 1-4 (shipped YYYY-MM-DD)
- 🚧 **v1.1 Security** — Phases 5-6 (in progress)

## Phases

<details>
<summary>✅ v1.0 (Phases 1-4) — SHIPPED YYYY-MM-DD</summary>

- [x] Phase 1: Foundation (2/2 plans) — completed YYYY-MM-DD
- [x] Phase 2: Authentication (2/2 plans) — completed YYYY-MM-DD

</details>
```

**Re-append Backlog section after the rewrite** (only if `$BACKLOG_SECTION` was non-empty):

Append the extracted Backlog content verbatim to the end of the newly written ROADMAP.md. This ensures 999.x backlog items are never silently dropped during milestone reorganization.

**Safety commit — commit archive files BEFORE deleting any originals:**

```bash
IFS= read -rd '' ENGINEER_ARGS <<'ENGINEER_ARGS_END' || true
$ARGUMENTS
ENGINEER_ARGS_END
ENGINEER_ARGS=${ENGINEER_ARGS%$'\n'}
INIT_REORG=$(engineer_run query init.complete-milestone )
_engineer_field() { value=$(printf '%s' "$1" | engineer_run query json.get --field "$2" --default '""' --raw) || return $?; [ "$value" = null ] && value=""; printf '%s' "$value"; }
STATE_PATH=$(_engineer_field "$INIT_REORG" state_path)
ROADMAP_PATH=$(_engineer_field "$INIT_REORG" roadmap_path)
ARCHIVE_DIR=$(_engineer_field "$INIT_REORG" archive_dir)
MILESTONES_PATH=$(_engineer_field "$INIT_REORG" milestones_path)
PROJECT_PATH=$(_engineer_field "$INIT_REORG" project_path)
engineer_run query commit "chore: archive v[X.Y] milestone files" --files "${ARCHIVE_DIR}/v[X.Y]-ROADMAP.md" "${ARCHIVE_DIR}/v[X.Y]-REQUIREMENTS.md" "${ARCHIVE_DIR}/v[X.Y]-MILESTONE-AUDIT.md" "$MILESTONES_PATH" ${PROJECT_PATH:+"$PROJECT_PATH"} "$STATE_PATH" "$ROADMAP_PATH"
```

This creates a durable checkpoint in git history. If anything fails after this point, the working tree can be reconstructed from git.


**Remove REQUIREMENTS.md via git rm** (preserves history, stages deletion atomically):

```bash
IFS= read -rd '' ENGINEER_ARGS <<'ENGINEER_ARGS_END' || true
$ARGUMENTS
ENGINEER_ARGS_END
ENGINEER_ARGS=${ENGINEER_ARGS%$'\n'}
INIT_REORG=$(engineer_run query init.complete-milestone )
_engineer_field() { value=$(printf '%s' "$1" | engineer_run query json.get --field "$2" --default '""' --raw) || return $?; [ "$value" = null ] && value=""; printf '%s' "$value"; }
REQUIREMENTS_PATH=$(_engineer_field "$INIT_REORG" requirements_path)
git rm "$REQUIREMENTS_PATH"
```

</step>

<step name="write_retrospective">

**Append to living retrospective:**

Check for existing retrospective:
```bash
ls .planning/RETROSPECTIVE.md 2>/dev/null || true
```

**If exists:** Read the file, append new milestone section before the "## Cross-Milestone Trends" section.

**If doesn't exist:** Create from template at `engineer/templates/retrospective.md`.

**Gather retrospective data:**

1. From SUMMARY.md files: Extract key deliverables, one-liners, tech decisions
2. From VERIFICATION.md files: Extract verification scores, gaps found
3. From UAT.md files: Extract test results, issues found
4. From git log: Count commits, calculate timeline
5. From the milestone work: Reflect on what worked and what didn't

**Write the milestone section:**

```markdown
## Milestone: v{version} — {name}

**Shipped:** {date}
**Phases:** {phase_count} | **Plans:** {plan_count}

### What Was Built
{Extract from SUMMARY.md one-liners}

### What Worked
{Patterns that led to smooth execution}

### What Was Inefficient
{Missed opportunities, rework, bottlenecks}

### Patterns Established
{New conventions discovered during this milestone}

### Key Lessons
{Specific, actionable takeaways}

### Cost Observations
- Model mix: {X}% opus, {Y}% sonnet, {Z}% haiku
- Sessions: {count}
- Notable: {efficiency observation}
```

**Update cross-milestone trends:**

If the "## Cross-Milestone Trends" section exists, update the tables with new data from this milestone.

**Commit:**
```bash
engineer_run query commit "docs: update retrospective for v${VERSION}" --files .planning/RETROSPECTIVE.md
```

</step>

<step name="update_state">

Most STATE.md updates were handled by `milestone complete`, but verify and update remaining fields:

**Project Reference:**

```markdown
## Project Reference

See: .planning/PROJECT.md (updated [today])

**Core value:** [Current core value from PROJECT.md]
**Current focus:** [Next milestone or "Planning next milestone"]
```

**Accumulated Context:**
- Clear decisions summary (full log in PROJECT.md)
- Clear resolved blockers
- Keep open blockers for next milestone

</step>

<step name="handle_branches">

Check the project's `branching_strategy` (from `init.execute-phase`/`init.complete-milestone`). `"none"` skips branch handling. For `"phase"` or `"milestone"`, list the matching branches (by the configured prefix template); no branches found also skips branch handling. Resolve the base branch through the single shared resolver, never a bare `main`/`master` fallback:
```bash
BASE_BRANCH=$(engineer_run query git.base-branch)
```

If branches exist, present them and ask (AskUserQuestion): **Squash merge** (recommended) / **Merge with history** / **Delete without merging** / **Keep branches**. All three merge/delete options iterate every matching branch (phase strategy) or the one milestone branch, checking out `BASE_BRANCH` first and returning to the original branch after; both merge options strip `.planning/` from staging first when `commit_docs` is false. "Keep branches" just reports them as preserved for manual handling.


</step>

<step name="git_commit_milestone">

Commit the REQUIREMENTS.md deletion (archive files and ROADMAP.md were already committed in the safety commit in `reorganize_roadmap_and_delete_originals`).

```bash
git commit -m "chore: remove REQUIREMENTS.md for v[X.Y] milestone"
```

Confirm: "Committed: chore: remove REQUIREMENTS.md for v[X.Y] milestone"


</step>

<step name="offer_next">

```
✅ Milestone v[X.Y] [Name] complete

Shipped:
- [N] phases ([M] plans, [P] tasks)
- [One sentence of what shipped]

Archived:
- milestones/v[X.Y]-ROADMAP.md
- milestones/v[X.Y]-REQUIREMENTS.md

Summary: .planning/MILESTONES.md

---

## ▶ Next Up — [${PROJECT_CODE}] ${PROJECT_TITLE}

**Start Next Milestone** — questioning → research → requirements → roadmap

`/clear` then:

`/new-milestone`

---
```

</step>

</process>

<milestone_naming>

**Version conventions:**
- **v1.0** — Initial release
- **v1.1, v1.2** — Minor updates, new features, fixes
- **v2.0, v3.0** — Major rewrites, breaking changes, new direction

**Names:** Short 1-2 words (v1.0, v1.1 Security, v1.2 Performance, v2.0 Redesign).

</milestone_naming>

<what_qualifies>

**Create milestones for:** Initial release, public releases, major feature sets shipped, before archiving planning.

**Don't create milestones for:** Every phase completion (too granular), work in progress, internal dev iterations (unless truly shipped).

Heuristic: "Is this deployed/usable/shipped?" If yes → milestone. If no → keep working.

</what_qualifies>

<success_criteria>

Milestone completion is successful when:

- [ ] Pre-close artifact audit run and output shown to user
- [ ] Deferred items recorded in STATE.md if user acknowledged
- [ ] Known deferred items count noted in MILESTONES.md entry

- [ ] MILESTONES.md entry created with stats and accomplishments
- [ ] All shipped requirements moved to Validated in PROJECT.md
- [ ] Key Decisions updated with outcomes
- [ ] ROADMAP.md Backlog section extracted before rewrite, re-appended after (skipped if absent)
- [ ] ROADMAP.md reorganized with milestone grouping (overwritten in place, not deleted)
- [ ] Roadmap archive created (milestones/v[X.Y]-ROADMAP.md)
- [ ] Requirements archive created (milestones/v[X.Y]-REQUIREMENTS.md)
- [ ] Safety commit made (archive files + updated ROADMAP.md) BEFORE deleting REQUIREMENTS.md
- [ ] REQUIREMENTS.md removed via `git rm` (fresh for next milestone, history preserved)
- [ ] STATE.md updated with fresh project reference
- [ ] Milestone commit made (includes archive files and deletion)
- [ ] Requirements completion checked against REQUIREMENTS.md traceability table
- [ ] Incomplete requirements surfaced with proceed/audit/abort options
- [ ] Known gaps recorded in MILESTONES.md if user proceeded with incomplete requirements
- [ ] RETROSPECTIVE.md updated with milestone section
- [ ] Cross-milestone trends updated
- [ ] User knows next step (/new-milestone)

</success_criteria>
