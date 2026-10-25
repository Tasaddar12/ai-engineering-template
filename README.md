# AI Engineer

A fresh foundation for an AI engineering workflow for Codex and Claude, based on
the core prompt and context engineering material from Open GSD.

This first pass replaces the previous repository layout, imports selected full
prompt bodies, and reserves the deployment entry points. The installer,
migration, updater, workflow runtime, and host adapters are not implemented yet.
No tests have been run for this rebuild.

| Path | Purpose |
| --- | --- |
| `bin/installer.py` | Scaffold for fresh Codex or Claude installation. |
| `bin/migrate.py` | Scaffold for migrating an existing deployment to the new layout. |
| `bin/update.py` | Scaffold for updating a deployment from the latest upstream AI Engineer workflow. |
| `ai-engineer/` | Installable workflow base: workflows, templates, references, contexts, and future workflow runtime scripts in `bin/`. |
| `skills/` | Skill prompt definitions intended for installation. |
| `agents/` | Agent prompt definitions intended for installation. |
| `commands/` | Command prompt definitions intended for installation. |
| `hooks/` | Reserved for installable hooks; none imported. |
| `src/` | Reserved for validation, setup, and repository tooling that is not installed into adopting projects. |
| `scripts/` | Reserved for repository development and maintenance automation. |
| `tests/` | Reserved for workflow tests; none imported or run. |
| `docs/` | This project's reference material, scope notes, and import provenance. |

The selected core covers project intake, codebase mapping, phase management,
discussion, planning, execution, verification, quick tasks, task capture,
debugging, session continuity, and milestones. GSD scripts, product docs, hooks,
tests, and optional capability packs are excluded.

The imported Markdown retains upstream names, paths, and runtime instructions.
It is not a ready-to-run Codex or Claude installation. See
[foundation scope](docs/foundation-scope.md) for the remaining adaptation work
and [import provenance](docs/upstream-import.json) for the exact source files.

Imported content is provided under the [Open GSD MIT license](LICENSE).
