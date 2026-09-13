Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

# --all mode — auto-select ALL gray areas, discuss interactively

> **Lazy-loaded.** Read this file from `.ai/library/workflows/discuss-phase.md` when
> `--all` is present in `$ARGUMENTS`. Behavior overlays the default mode.

## Effect

- In `present_gray_areas`: auto-select ALL gray areas without asking the user
  (skips the AskUserQuestion area-selection step).
- Discussion for each area proceeds **fully interactively** — the user drives
  every question for every area (use the default-mode `discuss_areas` flow).
- Does NOT auto-advance to plan-phase afterward — use `--chain` or `--auto`
  if you want auto-advance.
- Log: `[--all] Auto-selected all gray areas: [list area names].`

## Why this mode exists

This is the "discuss everything" shortcut: skip the selection friction, keep
full interactive control over each individual question.

## Combination rules

- `--all --auto`: `--auto` wins for the discussion phase too (Claude picks
  recommended answers); `--all`'s contribution is just area auto-selection.
- `--all --chain`: areas auto-selected, discussion interactive, then
  auto-advance to plan/execute (chain semantics).
- `--all --batch` / `--all --text` / `--all --analyze`: layered overlays
  apply during discussion as documented in their respective files.


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
