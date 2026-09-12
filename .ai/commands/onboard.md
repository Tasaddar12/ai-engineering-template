# Onboard

Read [RULES](../RULES.md). Inspect first; write in an
[assigned worktree](worktree.md) only when adoption or changes are authorized.

## Fresh adoption

1. Inspect the source layout, languages, entry points, tests, configuration,
   recent history and existing guides. Do not invent a product from this template.
2. Establish PROJECT from the user's stated purpose, success, boundaries and
   confirmed decisions. Resolve genuinely missing intent with the user; record
   existing explicit authorization without asking again.
3. Configure actual required checks and available worker commands in config.yaml.
   Run the checks and report their real baseline. Missing routes/checks are
   configuration gaps, not permission to claim readiness.
4. Inventory existing documents and compare relevant claims to code. Preserve
   useful guides. Propose specific retirement/move actions only where needed,
   within the user's authorized scope. Do not bulk-convert transcripts into
   requirements or invent historical ADR rationale.
5. Record desired outcomes in REQUIREMENTS and order coherent capabilities as
   phases in ROADMAP. Detail only the next useful scope. Known defects, unknown
   failures and documentation corrections use the same phase process.
6. Use phase CONTEXT for incoming information, exact acceptance, choices and
   unresolved questions. Create codebase maps only where they save later work.
   Draft current SPECs only from inspected implementation evidence.
7. Confirm AGENTS points to the active rules, commands and roles. Commit authorized
   setup, then report what is ready and what still needs a decision or setup.

## Returning session

Read PROJECT, STATE, ROADMAP and the selected phase's context/evidence. Run
[phase-status](phase-status.md), inspect relevant code and continue the user's
authorized work. Do not restructure the project merely because onboarding was
invoked. Report drift with evidence in its affected phase.
