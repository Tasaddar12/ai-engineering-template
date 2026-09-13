---
name: gsd:workspace
description: Manage GSD workspaces — create, list, or remove isolated workspace environments
argument-hint: "[--new | --list | --remove] [name]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Grep
  - AskUserQuestion
---

<objective>
Manage GSD workspaces with a single consolidated command.

Mode routing:
- **--new**: Create an isolated workspace with repo copies and independent .planning/ → new-workspace workflow
- **--list**: List active GSD workspaces and their status → list-workspaces workflow
- **--remove**: Remove a GSD workspace and clean up worktrees → remove-workspace workflow
</objective>

<routing>

| Flag | Action | Workflow |
|------|--------|----------|
| --new | Create workspace with worktree/clone strategy | new-workspace |
| --list | Scan ~/gsd-workspaces/, show summary table | list-workspaces |
| --remove | Confirm and remove workspace directory | remove-workspace |

</routing>

<execution_context>
@.ai/gsd/workflows/new-workspace.md
@.ai/gsd/workflows/list-workspaces.md
@.ai/gsd/workflows/remove-workspace.md
@.ai/gsd/references/ui-brand.md
</execution_context>

<context>
Arguments: $ARGUMENTS

Parse the first token of $ARGUMENTS:
- If it is `--new`: strip the flag, pass remainder (--name, --repos, --path, --strategy, --branch, --auto flags) to new-workspace workflow
- If it is `--list`: execute list-workspaces workflow (no argument needed)
- If it is `--remove`: strip the flag, pass remainder (workspace-name) to remove-workspace workflow
- Otherwise (no flag): show usage — one of --new, --list, or --remove is required
</context>

<process>
1. Parse the leading flag from $ARGUMENTS.
2. Load and execute the appropriate workflow end-to-end based on the routing table above.
3. Preserve all workflow gates from the target workflow (validation, approvals, commits, routing).
</process>


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

The complete upstream body above is retained from GSD-Core at
`c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977`; only recorded reference substitutions
and explicit local conflict corrections have been made. See
`.ai/gsd/PROVENANCE.json` for exact source hashes and changes.

Read `.ai/gsd/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/gsd-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The upstream `config.json`, `/gsd:*` commands, tool
names, hooks, and Node CLI examples describe GSD's system; this import does not
install or activate that system. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
