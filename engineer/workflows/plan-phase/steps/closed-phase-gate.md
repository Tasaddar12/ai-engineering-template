# Closed-phase gate

Run `engineer_run query roadmap.get-phase "${PHASE_NUMBER}"` and read its structured status. If `--gaps` was explicitly passed, use gap-closure mode and preserve original accepted plans. Otherwise, a status of `Complete` blocks replanning unless the user explicitly supplied `--force`.

Report: "Phase {N} is complete. Replanning can invalidate the relationship between plans and shipped code. Use `/phase` for new work, `/phase --insert {N}` for a separately authorized follow-up, or `/plan-phase {N} --gaps` for actual verification gaps."

With explicit `--force`, warn that the closed phase is being replanned and preserve the previous evidence in Git. Confirm that closeout was wrong or that this exact replan was intended before committing altered plans. The override grants no implementation permission. An executed phase with stale or failed verification is not a completed phase; assess its actual owning records rather than inventing a completion status.
