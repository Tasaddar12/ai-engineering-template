# AI Engineer source repository

This repository is being rebuilt as a minimal prompt and context engineering
foundation. The imported workflow material is source content for future installs;
it is not the maintenance procedure or authority for this repository.

Read README.md and docs/foundation-scope.md before changing the foundation.
Keep installable prompts in ai-engineer/, skills/, agents/, and commands/.
Reserve hooks/ for installable hooks, src/ for repository tooling, scripts/ for
repository automation, tests/ for workflow tests, and docs/ for this project's guides.

The initial import preserves complete upstream prompt bodies. Keep provenance in
docs/upstream-import.json and retain the upstream MIT license. Do not import GSD
executables, product documentation, tests, or optional capability packs as part
of the foundation.

bin/installer.py, bin/migrate.py, and bin/update.py are scaffolds. Their behavior,
the workflow runtime under ai-engineer/bin/, and Codex/Claude adapters still need
planning and implementation. Do not describe these as working installations.

The user has explicitly deferred testing for this initial rebuild. Do not run
tests, validation suites, or install/migration/update trial runs until authorized.
