# PR 171 YAML Bootstrap Follow-up

Base: `5ad2f56f75be94185fea3edc5d3b232291934571`

## Changes

- Changed code-fixer's early worktree opt-out read to locate and import the bundled `lib.text.yaml_load` parser before the launcher preamble, preserving the default-enabled fallback for unavailable or malformed config. Its isolated fixture uses `-I -S` and controlled temp project/runtime roots.
- Corrected remaining config filename references in new-project and related docs; clarified git-integration discovery behavior. Updated health workflow guidance to match active YAML validation while preserving retained upstream JSON diagnostic codes as inactive metadata. Removed unsupported persisted `planning.sub_repos` instructions; documented `.gitmodules` discovery, explicit `--subrepo` targeting, and immediate-child runtime scanning.

## Checks

- Bundled parser fixture passed for explicit `false`, explicit `true`, missing config/default, and malformed YAML.
- 441 focused tests ran successfully (`OK`, 1 expected failure), including agent-source, markdown-Python, table, sectionizer, and retained health-diagnostic metadata checks.
- Final focused rerun after health-doc corrections: 70 tests, `OK` (1 expected failure).
- `git diff --check` passed.

## Deviations

- None.

## Remaining

- The coordinator-owned structured finding for an inaccessible config.yaml is pending integration; missing and malformed config already produce structured diagnostics.
