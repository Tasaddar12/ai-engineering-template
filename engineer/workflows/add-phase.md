<!-- workflow: add-phase; produces: ROADMAP.md, STATE.md -->
<purpose>
Add a titled phase at the end of the current milestone. Let the runtime allocate its number, create its directory, and maintain every roadmap section and traceability field. Creating a phase never authorizes implementation.
</purpose>
<required_reading>
@engineer/RULES.md
@engineer/truth-map.md
@engineer/references/template-contract.md
</required_reading>
<process>
<step name="parse_arguments">
Read the description from the user's arguments. Parse optional `--goal <text>` and `--requirements <ids>` separately; do not include flags in the title. Require a nonempty short description. Ask for the missing description before any write.

Usage: `/phase "Add authentication" --goal "Users can sign in" --requirements AUTH-01,AUTH-02`.
Use the description as the goal only when no separate goal was supplied. Preserve requirement identifiers exactly; do not invent acceptance criteria from the title.
</step>
<step name="init_context">
Read and execute `engineer/workflows/_runtime-launcher.snippet.sh` in the current shell, then run:
```bash
engineer_run query init.phase-op 0
```
Read `roadmap_exists` and `response_language`. If no roadmap exists, report the missing record and direct the user to onboarding. Apply the configured language to user-facing prose; preserve commands, paths and identifiers.
</step>
<step name="add_phase">
Run `engineer_run query phase.add "${description}" --goal "${goal}"`, adding `--requirements` only when supplied. Check the command's exit status before consuming the result. The runtime owns the next number, slug, directory, roadmap heading, checklist, dependency fields, Progress row, and requirement traceability. Extract `phase_number`, `padded`, `name`, `goal`, `slug`, and `directory` from the returned JSON with `--pick` on the producing query where practical. Do not repeat the mutation to obtain another field; retain its JSON output for a standard-library Python read.

If a warning says the title is goal-shaped, show it and propose a shorter title through `/phase --edit`; never silently rewrite approved wording.
</step>
<step name="update_project_state">
Run `engineer_run query state.add-roadmap-evolution "Phase ${phase_number} added: ${description}"`. A duplicate result means the existing record already covers the change; do not append it by hand.
</step>
<step name="commit">
Run `engineer_run query commit "docs(roadmap): add phase ${padded}" --files .planning/ROADMAP.md .planning/STATE.md .planning/REQUIREMENTS.md "${directory}"`. Include only returned changed record paths and the new directory. Report a failed commit without pretending the addition was rolled back.
</step>
<step name="completion">
Report the allocated phase number, title, goal, requirement IDs, directory, and record paths. State that it is not planned or implemented. End with one line: `Discuss phase {phase_number} with /discuss-phase {phase_number}.`
</step>
</process>
<anti_patterns>
Do not number phases, create directories, or edit roadmap sections by hand. Do not create plans during phase addition. Do not start implementation or bypass discussion. Do not omit an explicitly supplied goal or requirement link.
</anti_patterns>
<success_criteria>
The runtime addition succeeded, its returned phase and directory exist, the roadmap and evolution record reflect the same number, and the meaningful slice is committed. Any warning or blocker appears in the report.
</success_criteria>
