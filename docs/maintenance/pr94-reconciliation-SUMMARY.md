---
status: complete
acceptance:
  - standalone-cleanup-on-main
  - complete-cleanup-evidence-closure
  - complete-cleanup-test-port
documentation:
  - .ai/commands/cleanup.md
  - .agents/skills/cleanup/SKILL.md
  - .ai/workflows/cleanup.md
  - .ai/references/cleanup.md
  - .ai/hooks/README.md
  - .ai/commands/README.md
base: 393ea2d0a63e07e22d7f146f7cf7a34a189451e1
source: e304a514938a1509de7c4d28b7b6c5dcc4378878
branch: codex/pr94-reconcile-main
---

# PR 94 standalone cleanup reconciliation

## Changes

- Extract the cleanup library and dedicated CLI onto the pinned main base.
  Preserve preview/apply JSON and exit status contracts. Load only the adjacent
  installed `runtime/lib/cleanup.py`; expose no stdin hook path or registration.
- Retain the complete helper closure: protected branch policy, cleanup decision
  type/refusal, canonical paths, bounded subprocess evidence, repository/worktree
  identity, ownership manifests, GitHub/GitLab pagination and exact provider
  identity/terminal state, Git ancestry, cleanup snapshots, safe backup evidence,
  approval validation, exclusive lock, one-use receipts, expected-OID no-deref
  ref deletion and final operation/preserved readback. Keep previews read only.
- Port all 24 original `CleanupTests` cases and their full fixtures. Preserve
  provider matrices, unique unintegrated commits, ignored/untracked/locked work,
  exact/stale approval, receipts, partial failure, backup digests and aliases,
  detached/unrecorded backups, source/installed CLI, per-item provider/ownership/
  ref drift, symbolic and dangling refs, mutation-time aliases/moved OIDs,
  direct-ref controls, nested backups/two owners/five operations and new unowned
  sibling drift. Remove only the obsolete guard fallback; rename import/CLI paths.
  Add CLI assertions that a missing mode rejects stdin JSON without hook output.
- Add both-host installer coverage for CLI/library/command/skill/workflow/reference
  packaging, absence of global guard files/registration and retention of advisory
  PreToolUse registration. Preserve Codex's `.agents/skills` discovery location.
- Add current-use cleanup command/skill/workflow/reference and catalog guidance.

## Checks

- Compare actual Git root with `git -C` against the exact pinned root; confirm
  starting branch, clean tree and base before writing. Repeat the root/branch/base
  check before commit and inspect owned staged paths/content.
- Parse and compile the four changed Python files as AST without importing or
  executing repository code. All parse and compile successfully.
- Compare extracted source AST with the pinned source: 23 helpers/classes are
  unchanged; the decision type and its call are renamed, and refusal text/default
  operation describe cleanup only. A static loaded-identifier scan finds no
  unresolved helper names. Trace provider, ownership and ancestry dependencies.
- Compare old/new test case names and order: all 24 retained. All fixture/test
  method ASTs match except the library path, removed guard fallback, CLI paths
  and added CLI assertions for the absence of a stdin mode.
- Inspect local Markdown link targets, command/skill identity, source/diff and
  whitespace. No rejected guard import or global shell-policy dependency appears
  in the new library, CLI or cleanup tests.
- Tests, configured checks, project workflows, real cleanup, provider calls and
  native probes: **not run**, as instructed. CI configuration is unchanged.

## Deviations

- No installer implementation change is needed: existing tracked-file packaging
  copies the new assets and relocates command/skill/workflow paths for both hosts.
- Exclude global destructive guard files, shell parser/evaluator, global hook
  registration, guard-only tests, parent RULES/worktree changes, planning records,
  native/provider publication code and prior maintenance history.
- Keep extraction source behavior; this static review does not establish passing
  runtime behavior or trusted live host execution.

## Remaining

- Independent source and documentation review by the coordinator. Review the six
  guide/catalog paths listed in `documentation`, especially installed namespace
  resolution, approval provenance and the evidence contract.
- Coordinator owns PR head replacement/retargeting and any publication. No push,
  publish, merge, rebase, branch switch, worktree deletion or cleanup is performed
  by this worker. Resolve this slice's commit from this file's Git history; the
  completion handoff records its exact SHA.
