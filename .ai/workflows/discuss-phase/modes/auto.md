Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

# --auto mode — fully autonomous discuss-phase

> **Lazy-loaded.** Read this file from `workflows/discuss-phase.md` when
> `--auto` is present in `$ARGUMENTS`. After the discussion completes, the
> parent's `auto_advance` step also reads `modes/chain.md` to drive the
> auto-advance to plan-phase.

## Effect across steps

- **`check_existing`**: if CONTEXT.md exists, auto-select "Update it" — load
  existing context and continue to `analyze_phase` (matches the parent step's
  documented `--auto` branch). If no context exists, continue without
  prompting. For interrupted checkpoints, auto-select "Resume". For existing
  plans, auto-select "Continue and replan after". Log every decision so the
  user can audit.
- **`cross_reference_todos`**: fold all todos with relevance score >= 0.4
  automatically. Log the selection.
- **`present_gray_areas`**: auto-select ALL gray areas. Log:
  `[--auto] Selected all gray areas: [list area names].`
- **`discuss_areas`**: for each discussion question, choose the recommended
  option (first option, or the one explicitly marked "recommended") **without
  using AskUserQuestion**. Skip interactive prompts entirely. Log each
  auto-selected choice inline so the user can review decisions in the
  context file:
  ```
  [auto] [Area] — Q: "[question text]" → Selected: "[chosen option]" (recommended default)
  ```
- After all areas are auto-resolved, skip the "Explore more gray areas"
  prompt and proceed directly to `write_context`.
- After `write_context`, **auto-advance** to plan-phase via `modes/chain.md`.

## Auto-mode pass cap

In `--auto` mode, complete the discuss step in a single pass. After writing
CONTEXT.md once, continue to `write_context` and `auto_advance`. Do not reread
CONTEXT.md or run another pass.

If you have already written and committed CONTEXT.md, the discuss step is
complete. Move on.

## Combination rules

  auto mode (no user prompts to render).
  trail; selection still uses the recommended option.
  answering — incompatible with autonomous selection).
