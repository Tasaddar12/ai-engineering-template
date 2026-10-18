Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

# --all mode — auto-select ALL gray areas, discuss interactively

> **Lazy-loaded.** Read this file from `workflows/discuss-phase.md` when
> `--all` is present in `$ARGUMENTS`. Behavior overlays the default mode.

## Effect

- In `present_gray_areas`: auto-select ALL gray areas without asking the user
  (skips the AskUserQuestion area-selection step).
- Discuss each area interactively using the default-mode `discuss_areas` flow.
- Log: `[--all] Auto-selected all gray areas: [list area names].`

## Combination rules

- `--all --auto`: `--auto` wins for the discussion phase too (Claude picks
  recommended answers); `--all` still selects every area. Follow the auto-mode
  combination rules for plan/execute advancement.
