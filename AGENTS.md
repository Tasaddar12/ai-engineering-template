# Operating index

Today's architecture is defined in `ARCHITECTURE.md` and `.ai/decisions/ADR-006.md`.
Read `.ai/STATE.yaml`, the selected plan/feature, and only their relevant references.
Historical files under `.ai/archive/` and `.ai/plans/superseded/` are evidence, never active instructions.

- Use Python 3.11+ and the `ai_engineering` package. Tasks plan work; feature batches own agents and `.worktrees/` checkouts.
- Follow `.ai/constraints.yaml`, `.ai/models.yaml`, `.ai/project/commands.yaml`, and the selected `.ai/agents/` role definition. All command execution in the product goes through the central runner.
- The coordinator alone updates workflow state. Agents edit declared scope and return templated handoffs.
- Inspect source first, test meaningful behavior, and check your diff before handoff. Record actual commands, failures, skips, assumptions, and deviations.
- Use one independent Critical Change Reviewer on the complete feature diff. Verdicts are `PASS` or `CHANGES_REQUIRED`; repairs return to the same implementer. Never self-approve.
- Structural failures go through recovery and decomposition. Preserve rejected and superseded artifacts.
- Local reversible work and local commits are authorized. External writes, credentials, paid use, destructive operations, and scope expansion require configured authority.

Start with `python -m ai_engineering status`. See `docs/workflows.md` for lifecycle rules and `.ai/plans/active/PLAN-002.md` for Python boundaries. During this reset, follow PLAN-002 and its approved decomposition; do not resume PLAN-001.

## Hard requirement: planning location

ALL plans and plan-specific contracts MUST live under `.ai/` as a `PLAN-NNN` Markdown document with explicit task and feature references. Tasks and features MUST also live under `.ai/`. Never place a plan, plan-specific contract, task list or feature graph in `docs/` or any other product-documentation folder. Reusable architecture/workflow documentation may live in `docs/`; it must link to plans instead of containing their implementation planning. This is a hard constraint, not a preference.

## Mandatory change lifecycle

Every repository edit follows **worktree -> changes -> meaningful validation and one independent complete-diff review -> merge -> delete the merged worktree and its branch**. This includes plans, tasks, features, documentation, configuration and changes to these operating instructions. Start in a dedicated managed worktree before editing; do not edit the primary checkout and treat the worktree as a future implementation detail. Keep each authoring/implementation session on its assigned branch.

Use the current explicitly selected development base; normal configured delivery uses a PR to main. Do not silently change the integration base or merge unrelated work. When no remote exists and local delivery is explicitly authorized, record the reviewed local merge honestly rather than inventing a PR. Verify the exact merged revision, stopped ownership and clean managed path, then remove its worktree and exact local/remote branch. This cleanup is required and authorized by the standing user instruction; concrete obstacles require repair or evidenced hard-block metadata, not an extra routine permission request.

Planning and its Git delivery never authorize implementation of the plan. Pure discussion/read-only inspection needs no worktree. The coordinator may record administrative intents, command/review evidence and state observations from its control context; this exception cannot be used for direct product/document edits or self-review.
