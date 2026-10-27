<!-- workflow: insert-phase; produces: ROADMAP.md, STATE.md -->
<purpose>
Insert urgent work after an existing phase while preserving the numbering and content of existing phases. The runtime allocates the inserted identifier and records its dependencies.
</purpose>
<required_reading>
@engineer/RULES.md
@engineer/references/template-contract.md
</required_reading>
<process>
<step name="parse_arguments">
Parse `/phase --insert <after-phase> "<description>" [--goal <text>] [--requirements <ids>]`. Require the anchor phase and a short description. Accept the runtime's supported phase identifiers, including decimal and letter-suffix forms; do not impose an integer-only regular expression. Do not insert before the first phase. Use ordinary `/phase` for planned work at the milestone's end.
</step>
<step name="init_context">
Read and execute `engineer/workflows/_runtime-launcher.snippet.sh`, then run `engineer_run query init.phase-op "${after_phase}"`. Stop on a missing roadmap or `phase_found: false`. Read the anchor's title, goal and dependencies, and the following phases before proposing the insertion's effect.
</step>
<step name="insert_phase">
Run `engineer_run query phase.insert "${after_phase}" "${description}" --goal "${goal}"`, adding supplied requirement IDs without inventing new ones. Consume the returned `phase_number`, `padded`, `name`, `directory`, and dependency changes only after success. The runtime owns identifier selection, directory creation, the inserted marker, checklist and Progress rows. Preserve existing phase descriptions and numbering.
</step>
<step name="update_project_state">
Run `engineer_run query state.add-roadmap-evolution "Phase ${phase_number} inserted after ${after_phase} (URGENT): ${description}"`. Never patch STATE position fields to make the new phase appear current.
</step>
<step name="commit">
Run `engineer_run query commit "docs(roadmap): insert phase ${phase_number}" --files .planning/ROADMAP.md .planning/STATE.md .planning/REQUIREMENTS.md "${directory}"` with the actual changed paths.
</step>
<step name="completion">
Report the inserted number, title, goal, directory, and anchor phase. Explain any dependency impact on the next phase using the runtime's returned record. Creating this record does not authorize planning or implementation. End with `Discuss phase {phase_number} with /discuss-phase {phase_number}.`
</step>
</process>
<anti_patterns>
Do not renumber existing phases, change the anchor's content, edit roadmap structures directly, or create plans here. Preserve existing completed work and report incompatible dependency changes instead of rewriting them.
</anti_patterns>
<success_criteria>
The runtime inserted the phase, state records its actual identifier, dependency implications were reviewed, and the changed records are committed.
</success_criteria>
