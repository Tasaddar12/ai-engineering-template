# PR 94 cleanup documentation reconciliation

## Changes

- Bound the cleanup lock guarantee in the contract and operator sequence: it
  coordinates this CLI, while external Git, filesystem, or provider-state
  changes can race evidence reads. Require reports to reflect observed outcomes
  and readback.

## Coverage

- Verified unchanged: standalone CLI entry and installed namespace resolution;
  preview evidence and eligibility; ordered snapshot operations and bindings;
  exact human approval and envelope fields; exclusive lock and one-use receipts;
  fixed non-force worktree removal and compare-delete direct-ref operation;
  backups and preserved targets; `complete`/`partial`/`refused` outcomes and
  final readback; command/skill route and hook/catalog descriptions.
- Local Markdown links were checked. Command and approval-envelope examples
  were compared with the CLI and runtime implementation.

## Checks

- Manually compared the cleanup contract and workflow claims with
  `.ai/hooks/cleanup.py` and `.ai/runtime/lib/cleanup.py` at
  `6b18365fbcfb9002d23e11934a2ce7c0d3322c30`.
- Checked repository root, branch, HEAD and clean status before edits; checked
  the assigned base ancestry before commit. Inspected the owned diff and local
  links after editing.
- Tests, configured checks, cleanup execution, provider calls, and native host
  execution: not run, as assigned.

## Remaining

- Coordinator-owned integration and independent documentation review.
