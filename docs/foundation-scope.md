# Foundation scope

The first rebuild is a prompt-only source import. It replaces the former .ai/,
.agents/, .planning/, documentation, tests, and CI setup with the new source
layout. It does not initialize an adopting project's identity or planning records.

## Imported core

The source snapshot is Open GSD version 1.18.0 at Git revision
754e886bffaf2947648177d6371cd8705f42ab9b. Selected Markdown is copied byte for
byte, including its full context, examples, and procedural instructions.
docs/upstream-import.json maps every imported source path to its destination
and records its source SHA-256 digest. LICENSE preserves the original MIT notice.

The selection covers onboarding and document intake; codebase mapping; phase
add/insert/edit/remove; discussion, planning, execution and verification; quick
work, task capture and todos; debugging; progress, pause and resume; milestone
planning, audit, closure and summaries. Supporting agent prompts, workflow
fragments, templates, references and contexts live beside those entry points.

The commands/gsd/ and skills/gsd-*/ names are retained to make the initial import
traceable. Their final installed names and host bindings remain to be planned.

## Reserved implementation

The three root bin/*.py entry points deliberately exit with an unimplemented
message. They do not install files, migrate a deployment, fetch upstream, or
write project state. ai-engineer/bin/ is reserved for future installed workflow
runtime scripts. src/ and scripts/ are reserved for tooling used in this source
repository. hooks/ and tests/ have no imported implementation.

The intended responsibilities are fresh Codex/Claude installation via
bin/installer.py, existing-deployment migration via bin/migrate.py, and updates
from the latest upstream AI Engineer workflow via bin/update.py. Target layout,
CLI options, ownership tracking, preservation of project data, rollback, host
adapters, and upstream update policy need planning before implementation.

## Upstream bindings still present

The imported prompts contain Claude include paths such as ~/.claude/gsd-core/,
GSD command and agent names, Bash snippets, Agent/AskUserQuestion tool calls,
and gsd_run/gsd-tools runtime verbs. The new ai-engineer/ path is only the
repository destination; references inside copied files have not been rewritten.
Those bindings must be adapted to the new runtime and each supported host before
installation can work. Some conditional references point to optional material
outside the minimal import. Keeping a prompt body does not enable those features.

No source executable or GSD runtime was copied. Embedded code examples and shell
instructions inside prompt Markdown are preserved context, not ported scripts.
GSD's product documentation, optional capability packs, host plugins, editor
extensions, package metadata, CI, tests, and hook implementations are excluded.

## Current evidence

File selection, copying, repository inventory, and Git diff inspection are the
only review activities in this pass. No tests, linters, validation suites,
installation trials, migration trials, or updater trials have been run. Runnable
behavior and cross-host compatibility remain unverified and unimplemented.
