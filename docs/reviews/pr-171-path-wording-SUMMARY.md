# PR 171 Submodule Path Wording Follow-up

Base: `5ad2f56f75be94185fea3edc5d3b232291934571`

## Changes

- Clarified that `sub_repos` entries are repository paths relative to the workspace root, consistent with the paths read from `.gitmodules`.

## Checks

- Confirmed the field preserves `.gitmodules` path values in `engineer/bin/lib/bundles.py`.
- `git diff --check` passed.

## Deviations

- None.

## Remaining

- None.