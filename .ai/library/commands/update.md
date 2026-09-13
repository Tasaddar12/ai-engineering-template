---
name: workflow:update
description: Update Workflow to latest version with changelog display
argument-hint: "[--sync | --reapply | --next | --rc]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

<objective>
Check for Workflow updates, install if available, and display what changed.

Routes to the update workflow which handles:
- Version detection (local vs global installation)
- npm version checking
- Changelog fetching and display
- User confirmation with clean install warning
- Update execution and cache clearing
- Restart reminder
</objective>

<execution_context>
@.ai/library/workflows/update.md
</execution_context>

<flags>
- **--sync**: Sync managed Workflow skills across runtime roots so multi-runtime users stay aligned after an update. Runs the sync-skills workflow (--from, --to, --dry-run, --apply flags supported).
- **--reapply**: Reapply local modifications after a Workflow update. Uses three-way comparison (pristine baseline, user-modified backup, newly installed version) to merge user customizations back. Runs the reapply-patches workflow.
- **--next** (alias **--rc**): Target the `@next` RC dist-tag instead of `@latest` so you can install or refresh a release candidate (e.g. `1.4.0-rc.1`) through the normal update flow — scope/runtime detection, changelog preview, custom-file backup, and cache clearing all still apply. Omitting it keeps targeting `@latest` (no change). See ADR #660 for the RC channel.
- **(no flag)**: Standard update — check for new version, show changelog, install.
</flags>

<process>
Parse the first token of $ARGUMENTS:
- If it is `--sync`: strip the flag, execute the sync-skills workflow (passing remaining args for --from/--to/--dry-run/--apply).
- If it is `--reapply`: strip the flag, execute the reapply-patches workflow.
- Otherwise (including `--next` / `--rc`): execute the update workflow end-to-end, passing `$ARGUMENTS` through so the workflow's parse_update_channel step can select the release channel.

</process>

<execution_context_extended>
@.ai/library/workflows/sync-skills.md
@.ai/library/workflows/reapply-patches.md
</execution_context_extended>


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

This complete authoring guide retains its source content, examples, and methods.
Only recorded namespace/reference substitutions and explicit local conflict
corrections have been made. Source attribution and exact original hashes are
isolated in `.ai/library/THIRD-PARTY-NOTICES.md` and `PROVENANCE.json`.

Read `.ai/library/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/template-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The retained `config.json`, `/workflow:*` commands, tool
names, hooks, and Node CLI examples describe supporting source capabilities;
this import does not install or activate them. Source catalog pointers in examples
identify provenance, not executable command arguments. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
