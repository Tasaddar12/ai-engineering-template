# Orchestrator-worktree root pin

Before native Agent dispatch into a runtime-created checkout, read engineer/references/worktree-path-safety.md step 0p, Supplied-root pin. Embed its complete runnable guard inside `<project_root_pin>` in the executor prompt. Substitute `{PINNED_ROOT}` with the exact path returned by `worktree.create`, shell-single-quoting it under that section's composition contract. Never substitute the coordinator's session root for the worker root.

Replace any self-derivation of PROJECT_ROOT in this dispatch's required-reading block with that same quoted literal path. Validate the complete prompt before dispatch: its root, branch, base, plan ID, ownership and handoff all identify the same runtime-created checkout, and no unresolved template marker remains. Do not pass this build-time instruction to the executor instead of the bound runnable guard.

This fragment applies to orchestrator-worktree. Harness-worktree uses the assigned checkout's branch-check guard. Both modes remain isolated; neither permits primary-checkout execution or a project opt-out.
