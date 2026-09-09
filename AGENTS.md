# Operating index

Read `ARCHITECTURE.md`, `.ai/STATE.yaml`, the selected artifact, the focused constraints and the relevant workflow. PLAN-003 is completed and delivered; its record is `.ai/plans/completed/PLAN-003.md`. No implementation is active. Tests and validation remain deferred until the user requests that pass.

Use Python 3.11+ with authored modules directly under `src` and the installed `ai_engineering` namespace. Reusable assets live in root `agents`, `templates`, `workflows`, `constraints` and `framework.yaml`; installed `.ai` copies are derived from them. Every product subprocess goes through the central runner.

All plans and plan-specific contracts must be PLAN-NNN Markdown documents under `.ai`, with explicit task and feature references. Tasks and features also live under `.ai`. Keep managed worktree/branch ownership fixed. The coordinator owns state, commits, delivery and exact merged-worktree cleanup. Do not restore deleted project history or obsolete configuration.

Implementation subagents use GPT-5.6 Sol with xhigh reasoning. Reviewers, when requested, may use GPT-6 Astra with xhigh reasoning. Local reversible changes and commits are authorized; honor the current user request and configured authority for external operations. Keep credentials outside versioned content.
