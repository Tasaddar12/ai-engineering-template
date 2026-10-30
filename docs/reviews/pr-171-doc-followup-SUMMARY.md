# PR 171 Documentation Follow-up

Base: `5ad2f56f75be94185fea3edc5d3b232291934571`

## Changes

- Changed the phase researcher input example to use `.planning/tmp/research-plan-input.json` and explicitly create the repository-local directory, matching the runtime's repository-confined safe-path behavior.

## Checks

- Confirmed the create and `research-plan --input` examples use the same repository-local path.
- `git diff --check` passed.

## Deviations

- None.

## Remaining

- The runtime regression for this documented input path is coordinator-owned.
