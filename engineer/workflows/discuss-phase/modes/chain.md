Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

# Chain mode: discuss interactively, then plan

Load this mode from `discuss-phase.md` when `--chain` is present or when the
workflow's configured `auto_advance` preference requests the chain.

## Discussion behavior

Keep the standard interactive discussion intact. Ask the user about selected
gray areas, record their decisions and scope boundaries, and confirm before
writing the phase context. `--chain` does not answer questions on the user's
behalf and does not grant implementation permission. `--all` only selects all
gray areas; by itself it does not start the chain.

## Advance after context is written

1. After writing context, clear `workflow._auto_chain_active` before dispatch.
   This prevents plan-phase from treating the discuss-to-plan handoff as
   permission to continue into execute-phase. Preserve the user's persistent
   `workflow.auto_advance` setting.
   ```bash
   engineer_run query config-set workflow._auto_chain_active false
   ```
2. Show that discussion is complete and planning is starting.
3. Auto-advance to `plan-phase` for the same phase, passing its context path
   without `--auto` or `--chain`. The plan workflow may stop for missing
   information or a checkpoint; if it does, report that state and leave the
   user with the appropriate planning continuation.
   ```text
   /plan-phase ${PHASE} ${ENGINEER_WS}
   ```
4. When planning returns, report planning completion and the next explicit
   command. Do not dispatch `execute-phase` from discuss-phase chain mode.
   Implementation remains gated by the user's separate authorization.

If no chain trigger is active, finish with the normal manual next steps.
