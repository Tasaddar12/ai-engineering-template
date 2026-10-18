# PR 97 contribution-language editorial pass

**Outcome:** Clarified the Codex startup boundary and the action for unknown native-entry outcomes without changing the supported startup or native-entry protocol.

## Revision and scope

- Parent source revision: `ea67b47326e655fb273b7247f7d42bc46d4f8278`
- PR97 worktree start: `c2c727ec100d6311577df18a5f25dc660418c0d2`
- Reviewed original PR97 delta: `47593a3d..cb002502`
- Edited: [`.ai/references/same-agent-worktree.md`](../../.ai/references/same-agent-worktree.md)
- Reviewed unchanged: `AGENTS.md`, `.ai/RULES.md`, `.ai/hooks/README.md`, `.ai/references/worktree-sessions.md`, `.ai/runtime/README.md`, and the `discuss-phase`, `execute-phase`, `plan-phase`, `quick`, `ship` and `verify-work` workflows.

## Changes

- State that this template integration cannot move an active Codex conversation or agent; direct new-run users to the phase and quick startup commands and preserve the product-wide scope boundary.
- Give explicit steps for denial, timeout or missing native-entry results: inspect native state, request journal and Git registration; verify destination defaults if completion is proven, otherwise preserve the request as pending and unverified.
- Tighten the example lead-in and remove continuation-specific execution history.
- Preserve native entry gates, approval requirements, commands, flags, ticket and lifecycle rules, default-context proof, trust/policy constraints and unverified runtime/host boundaries.

## Checks

- Manually reviewed the PR97-only diff and local links in the edited reference.
- `git diff --check` passed.
- Tests and configured project checks: not run, as assigned.

## Deviations and remaining work

- No scope deviations. No unresolved editorial gaps identified in the assigned paths.
