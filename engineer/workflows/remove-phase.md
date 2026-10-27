<!-- workflow: remove-phase; produces: ROADMAP.md, STATE.md -->
<purpose>
Remove explicitly selected future work through the runtime, after showing the exact phase and receiving the user's confirmation. Preserve evidence of work that has already run.
</purpose>
<required_reading>
@engineer/RULES.md
@engineer/references/template-contract.md
</required_reading>
<process>
<step name="parse_arguments">
Parse `/phase --remove <phase> [--force] [--no-renumber]`. Require one exact target. Record whether the user supplied each flag; never infer `--force` from urgency or a failed attempt.
</step>
<step name="init_context">
Read and execute `engineer/workflows/_runtime-launcher.snippet.sh`. Run `engineer_run query init.phase-op "${target}"`. Stop when the phase is absent. Read `status`, `plans_complete`, `summary_count`, and `state.position.Phase` from the result; read the target's name, goal and directory before presenting deletion.
</step>
<step name="validate_future_phase">
Require a future phase with zero completed plans and zero summaries. Compare identifiers using roadmap order rather than lexical or floating-point comparisons. A current, completed, or partially executed phase requires a separate retirement decision; do not erase its evidence to make removal succeed. `--force` is an explicit override only for the runtime's documented removable-phase status guard; it does not authorize deleting executed evidence.
</step>
<step name="confirm_removal">
Show the target number, name, directory, dependencies, record paths, and the exact renumbering effect. With `--no-renumber`, state that subsequent phase numbers stay unchanged. Ask for an explicit yes to this exact removal; an empty, ambiguous, or unrelated reply cancels it. Existing authorization for this exact target may supply the confirmation; do not ask again solely because the workflow has multiple steps.
</step>
<step name="execute_removal">
Run `engineer_run query phase.remove "${target}"` with only the explicitly supplied supported flags. The runtime owns the guarded directory removal, roadmap references, dependencies, Progress rows, and any renumbering. Consume `removed`, `name`, `directory`, and `renumbered`; report a refusal as a refusal, without shell deletion or manual record repair.
</step>
<step name="commit">
Run `engineer_run query commit "chore(roadmap): remove phase ${target}" --files .planning` after inspecting the changed record paths. The commit message preserves the removed phase identity. Do not stage unrelated project work.
</step>
<step name="completion">
Report the removed phase, deleted directory, actual renumbering and changed records. Mention any dependency that now needs a decision. Use `/progress` only as the single route to inspect the remaining roadmap; do not start further work.
</step>
</process>
<anti_patterns>
Never delete executed phase evidence, bypass a runtime refusal, renumber by hand, or treat a generic approval as confirmation of a different deletion list.
</anti_patterns>
<success_criteria>
The exact removal was confirmed, runtime guards passed, returned effects match the record diff, and only the meaningful removal slice is committed.
</success_criteria>
