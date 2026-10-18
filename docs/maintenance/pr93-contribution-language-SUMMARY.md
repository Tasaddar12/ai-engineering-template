# PR 93 contribution-language editorial pass

**Outcome:** Clarified current-record validation scope and native checker inputs without changing the required metadata schema or warn-only behavior.

## Revision and scope

- Parent source revision: `c9d7ae8c357574faaef6fc201ff19908fff501dc`
- PR93 worktree start: `fdfa3efad15b851bf5361090d836aab02ff3e8bf`
- Reviewed original PR93 delta: `d8f2c8bd0c4dca0f82a7fc8a95e4f0abb8bcd2b6..47593a3d`
- Edited: [`.ai/runtime/README.md`](../../.ai/runtime/README.md) and [`.ai/runtime/TEMPLATE-CONTRACT.md`](../../.ai/runtime/TEMPLATE-CONTRACT.md)
- Reviewed unchanged: [`.ai/hooks/README.md`](../../.ai/hooks/README.md), [`.ai/templates/context.md`](../../.ai/templates/context.md), [`.ai/templates/phase-prompt.md`](../../.ai/templates/phase-prompt.md) and [`.ai/templates/summary.md`](../../.ai/templates/summary.md)

## Changes

- State the active-record commit gate and excluded unchanged/archive/maintenance/source-template inputs directly; keep instructional skeletons as source guidance.
- State warn-only `planning.validate` use and the explicit `--strict` condition without changing its behavior.
- List the checker’s accepted command payload locations and argv-list input directly, preserving the named payload fields.
- Preserve authored planning and history records, required schema fields, issue declaration mappings, status values, refusal conditions and evidence requirements.

## Checks

- Manually reviewed the original PR93 diff, current changed paragraphs and the native checker payload reader.
- Checked the edited contract anchor and maintenance-summary local links; `git diff --check` passed.
- Tests and configured project checks: not run, as assigned.

## Deviations and remaining work

- No scope deviations. No unresolved documentation gaps identified in the assigned paths.
