# PR 171 Bundle Field Follow-up

Base: `5ad2f56f75be94185fea3edc5d3b232291934571`

## Changes

- Corrected the three `init.new-project` output references to `sub_repos`, matching the field emitted by `engineer/bin/lib/bundles.py`.

## Checks

- Confirmed the runtime packet field at `engineer/bin/lib/bundles.py:87-90`.
- `git diff --check` passed.

## Deviations

- None.

## Remaining

- None.