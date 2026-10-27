<!-- workflow: next; coordinator routing only -->
<purpose>
Determine the next logical authorized workflow from actual project evidence, announce it and carry it through. Progress reports; this command acts within authority.
</purpose>
<response_language>
Read `engineer_run query config-get response_language --raw` through the sourced launcher. Apply the configured language to every user-facing prose surface: narration between tool calls, status updates, progress notes, findings, route explanations, headings and the final result. Preserve literal code, paths, identifiers, parser keys and canonical markers. Missing configuration uses the established conversation language; do not invent a language alias in an init bundle.
</response_language>
<process>
<step name="detect_state">
Read and execute engineer/workflows/_runtime-launcher.snippet.sh. Run `engineer_run query init.progress`. Require an actual roadmap and project records; if missing, report onboarding or phase creation as the concrete route rather than inventing project state. Read current phase records and pending continuation evidence, using actual runtime fields or explicit read-only queries rather than a separate state.json file.
</step>
<step name="safety_gates">
A stored checkpoint, error state, failed verification, uncommitted planning records or unresolved STATE blocker requires inspection before unrelated advancement. Check `git status --porcelain .planning` and report actual uncommitted record paths rather than silently committing or discarding them. Existing record health is inspected through /progress; do not invent a health command. A supplied `--force` overrides only the specific gate the user explicitly named; never infer it from urgency or a generic proceed.

Phase implementation still requires an explicit instruction for that phase recorded in CONTEXT. Discussion, planning, a passed design review and readiness do not supply it. If the next action is execute-phase and authority is absent, present that exact phase and stop without dispatching implementation. Do not use routing to expand an already authorized phase into another one.
</step>
<step name="find_incomplete_phase">
Prefer the earliest actually started unfinished phase over starting new work. Use a computed init incomplete_phase only when available and consistent; otherwise compare ordered roadmap phases with phase-plan-index records. Name blocked predecessors and preserve partially completed work. New work suggested by a finding stays a concrete scoped decision rather than a hand-written backlog phase.
</step>
<step name="select_route">
For the chosen phase run `engineer_run query init.phase-op "${PHASE_NUMBER}"`, checking phase_found first. Use actual context_path, plan_records, summaries and verification status:

| Evidence | Route |
|---|---|
| No discussion context | discuss-phase |
| Discussion exists, no checked plans | plan-phase |
| Unfinished checked plans | execute-phase, gated on explicit implementation authority |
| Implemented, verification absent/stale/nonpassed | verify-work |
| Passed/current verification, delivery pending | ship |
| Every current milestone phase complete and delivered | complete-milestone |

Do not route to removed modes, convergence loops, speculative future phases or unsupported commands. A blocker that cannot be resolved within scope is reported as the action needed, not bypassed with another route.
</step>
<step name="show_and_execute">
Announce the phase, observed state, selected workflow and evidence-backed reason. With `--dry-run`, report only and stop. Otherwise read the selected workflow in full and execute it end to end within existing authorization: discuss, plan, verify or milestone closeout may proceed when their own gates allow; execute-phase stops unless that exact phase has explicit implementation authority; ship preserves publication and explicit merge limits. Resume within the same session lineage and honor the selected workflow's completion boundary. Do not ask for routine handoff confirmation already authorized.
</step>
</process>
<anti_patterns>
Do not self-implement a routed plan, hide blockers, alter records to fit a preferred route, override authority, or automatically enter another phase after the selected workflow finishes.
</anti_patterns>
<success_criteria>
The route matches actual records and artifacts, safety and implementation-authority gates held, and the authorized workflow completed or reported its exact blocker. Dry run made no changes.
</success_criteria>
