# Bounded batch planning

The coordinator assigns one bounded outcome and a complete sibling-plan catalog. This reference does not create tasks, publish or authorize phase implementation.

## Required assignment

Read the exact repository, branch, base revision, owned PLAN output and relevant source contracts. The catalog contains sibling plan IDs and their outcomes. Declare dependencies only when a sibling produces an interface or result this plan consumes; do not invent IDs or dependencies.

## PLAN contract

```yaml
phase: quick-batch
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified: ["src/example.py", "tests/test_example.py"]
files_deleted: []
resources: []
autonomous: true
requirements: []
acceptance: []
documentation: []
checks: []
issue_refs: []
```

Use sibling **plan IDs** in `depends_on`, never a quick record identifier. Keep quick record identity in the coordinator's persisted batch mapping. Include exact files and deletions; an undeclared deletion blocks merge. Shared resource identities serialize otherwise independent plans. Required checks are argv lists, never shell strings.

## Scheduling and ownership

The coordinator computes groups from dependencies, path overlap and resources within host capacity. A wave number is a declared planning label, not an ownership exemption. The coordinator validates current PLAN metadata again before dispatch and merge; if the plan changes, update the persisted batch mapping before continuing.

## Tasks and evidence

Use the full [PLAN template](../templates/phase-prompt.md): each task names exact files, read_first, action, verify and done. State concrete acceptance and documentation obligations, and canonical issue references or Pending reasons. Honor the assigned task cap and split only at coherent outcomes through the coordinator.

## Return

Return the exact PLAN path, input revision, contract summary and unresolved decisions. Do not execute the plan or create unrelated batch records. Existing files are not proof of completion; a resumed assignment requires content and revision reconciliation.
