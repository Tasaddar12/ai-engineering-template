<!-- workflow: progress; read-only -->
<purpose>
Report actual project progress, recent shipped work, current position, decisions, blockers and record health, then recommend exactly one next action. Do not start the recommended work.
</purpose>
<process>
<step name="initialize">
Read and execute engineer/workflows/_runtime-launcher.snippet.sh. Run `engineer_run query init.progress`. Read actual project/roadmap/state existence, phase records/counts, progress_percent, milestone and state. If the roadmap is absent, report the missing record and recommend onboarding or phase creation according to the actual project state; do not invent a roadmap. Honor response_language for prose only. `--no-resume` suppresses a resume-focused recommendation; it does not authorize mutation.
</step>
<step name="load">
Read PROJECT's current intent, authoritative requirements and the actual phase goals. Use INIT state/roadmap fields for position, Key Decisions and blockers; a stale STATE pointer does not override authoritative roadmap or on-disk plan evidence. Read at most the three newest relevant complete SUMMARYs for recent work, naming actual deliverables and commits rather than deriving achievements from roadmap checkmarks. Read pending items from todo.list and open quick records from `engineer_run query quick.list --status open`; do not assume nonexistent init aliases contain them.
</step>
<step name="record_health">
When inspection execution is permitted, run `engineer_run query planning.validate` and report its actual warnings as Record Health. This is warn-only and read-only; never repair from progress. When the user deferred checks, report that validation is pending rather than running it or claiming health passed.
</step>
<step name="find_live_phase_state">
For the relevant phase run `engineer_run query find-phase "${CURRENT_PHASE}"` and phase-plan-index. Count actual plan and complete SUMMARY records; a partial or blocked summary is not proof of completion. Inspect only partial UAT status as human acceptance evidence when applicable. Run `engineer_run query verification.status "${CURRENT_PHASE}"` and use the canonical status; do not depend on a suggested command field.

Derive incomplete_phase from ordered roadmap phases and actual plan indexes: an earlier phase with started but unfinished plan evidence takes precedence over new work. When an init bundle exposes that same computed field, require it to agree with the source records. Do not run a cross-phase audit or unrelated verification to fill a progress report.
</step>
<step name="report">
Use `engineer_run query progress.bar --raw` for the actual progress bar. Present project and milestone, current phase and goal, recent complete work, plan/summary counts, decisions, blockers, open quick tasks and Record Health. Show `/capture --list` only when pending todos exist. Distinguish implemented, verified, merged and pending-human work; a summary alone does not mean shipped. If source and records disagree, name the exact mismatch and its owner.
</step>
<step name="recommend_one_action">
Use the first applicable evidence-backed route:

| Actual state | One recommendation |
|---|---|
| Project records missing | /new-project |
| Earlier phase started but incomplete | /execute-phase {N}, with the missing implementation-authority condition stated |
| Phase lacks CONTEXT | /discuss-phase {N} |
| Context exists but checked plans are missing | /plan-phase {N} |
| Plans remain unfinished | /execute-phase {N}, only with explicit implementation authority |
| All summaries exist but verification is absent, stale, gaps_found or human_needed | /verify-work {N} |
| Passed/current verification and open session awaits delivery | /ship {N} |
| All milestone phases are verified and delivered | /complete-milestone |
| No remaining scoped work | /new-milestone |

State the reason and stop. Do not include alternative command lists or a command handoff that starts work. An actual blocker may make its concrete human decision the single recommended action instead of a workflow.
</step>
<step name="edge_cases">
A missing project identity is an onboarding condition, not permission to fill it from this template. Empty phases, missing artifacts, stale record pointers and unverified quick tasks must be reported directly. Use runtime-owned record repair only in a separately authorized maintenance workflow. If the selected phase cannot be determined unambiguously, show the competing actual phase records and report the selection needed.
</step>
</process>
<anti_patterns>
Do not start the recommendation, repair records, create todos, infer success from counts, hide pending-human acceptance, or recommend several commands at once.
</anti_patterns>
<success_criteria>
The report reflects current evidence, recent actual work, blockers and record health, and ends with one justified next action without starting it.
</success_criteria>
