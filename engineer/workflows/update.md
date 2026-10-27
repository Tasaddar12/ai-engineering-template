<!-- workflow: update; roles: executor, code-reviewer -->
<purpose>
Review a workflow update pinned to an immutable upstream Git revision while preserving project intent and local customizations. Apply only a byte-guarded plan whose exact digest has been reviewed.
</purpose>
<required_reading>
@AGENTS.md
@~/.claude/engineer/RULES.md
@~/.claude/engineer/truth-map.md
@~/.claude/engineer/references/git-workflow.md
</required_reading>
<process>
<step name="pin_scope">
Identify the source repository, exact immutable commit, target installation directory and host (`claude` or `codex`). Resolve a user-supplied tag or branch to a commit and report the resulting pin. Reuse an already approved pin; do not silently substitute a newer upstream revision. Read the target's installed ownership manifest and current project customizations. Record what the user asked to update and which outcomes must be preserved. A request to inspect an update authorizes preview, not application of an unreviewed plan.
</step>
<step name="preview_update">
Resolve `bin/update.py` from the checked-out source tree. Use its complete supported command:
```bash
python -I bin/update.py --source "${SOURCE_REPO}" --ref "${PIN}" --target "${TARGET_DIR}" --host "${HOST}" --plan "${PLAN_FILE}"
```
This invocation is read-only by default. Pass `--no-hooks` only if that preference was explicitly selected. Preserve the exact plan file and its source pin, target, actions, expected bytes, ownership decisions and conflict list. Do not reconstruct a shorter plan from terminal output. Hash the full reviewed plan with Python's standard library; the digest must cover every byte, including explicit per-path resolutions.
</step>
<step name="resolve_conflicts">
For each conflict, determine the intended outcome from current project decisions and the pinned change. Dispatch `executor` with inline model/effort and mandatory worktree isolation to prepare exact per-path resolutions. Give the original file, upstream file, local customization and source evidence; preserve complete methods and examples. Do not permit generic overwrite-all or discard-local rules. Keep source and target guards intact in the plan. Require committed owned changes and the complete resolution diff; wait for the worker to stop before integrating it. A resolution that changes a locked outcome requires an explicit user decision; continue independent resolutions while that one remains blocked.
</step>
<step name="review_plan">
Capture the exact source revision and plan SHA-256. Dispatch a fresh non-author `code-reviewer` with inline model/effort to inspect every planned write/deletion, the complete conflict resolutions, target boundaries, ownership, preserved project behavior, hook changes and byte guards. The reviewer is read-only and reviews the full plan, not a summary of its actions. Join its report. Repair critical findings through a separate isolated executor, then re-review the new exact digest. Never carry approval from one digest to another.
</step>
<step name="apply_reviewed_plan">
Show the concrete reviewed plan and unresolved blockers. Apply only when the user's authorized scope covers those exact changes and the review is acceptable:
```bash
python -I bin/update.py --apply "${PLAN_FILE}" --reviewed-plan-sha256 "${PLAN_SHA256}"
```
The updater re-fetches the pinned source and recomputes source/target byte guards. A drift or unresolved conflict stops the affected apply; do not force it, edit a guard to match, or rerun a new plan under an old digest. Resolve the change in a fresh reviewed plan.
</step>
<step name="verify_named_outcomes">
Read the updater's complete results and identify the exact installed paths changed, preserved and refused. Run only the verification commands already configured for this update and permitted by the user's execution constraints. If testing is deferred, leave those checks pending and make no success claim. Verify the installed layout, command/skill mirrors and host registrations with evidence when execution is authorized. Preserve rollback/ownership artifacts returned by the updater.
</step>
<step name="report">
Report the source pin, host, target, exact plan digest, review revision, applied/preserved/blocked paths, and each named verification result or pending check. Do not hide local conflicts behind an overall success label. Do not merge or publish unrelated project changes.
</step>
</process>
<anti_patterns>
Never update from an unpinned latest revision, overwrite customizations by default, shorten retained methods, apply a modified plan under a previous digest, or treat an unrun check as passing.
</anti_patterns>
