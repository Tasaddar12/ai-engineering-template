# Worker handoff

The coordinator dispatches one bounded component with Markdown instructions.
Human-authored inputs use small YAML frontmatter, not external schema documents.

## Assignment

Read the file named by `PHASE_ASSIGNMENT`. Environment also supplies:

| Variable | Meaning |
|---|---|
| `PHASE_COMPONENT` | Assigned component ID |
| `PHASE_KIND` | Worker responsibility |
| `PHASE_WORKTREE` | Exact assigned checkout |
| `PHASE_RESULT` | Required result destination |

The assignment identifies the phase and input revision, relevant decisions,
component instructions, owned paths, checks and dependency results. Read the
mandatory core plus relevant sources. Ask the coordinator for missing scope;
do not borrow another checkout or reconstruct instructions from unrelated history.

## Component result

Coder/documentor workers write and commit the supplied SUMMARY path. Its
frontmatter reports `status: complete|blocked`, covered `acceptance` IDs and
covered `documentation` paths. Its body records Changes, Checks, Deviations and
Remaining, including actual command results and source areas.

A completed result must be supported by real work and evidence. Required
documentation can be verified unchanged with a reason; listing a path alone is
not proof. A blocked result preserves findings and safe partial work without
claiming successful integration. Only the coordinator integrates commits.

The verifier writes a report at an external result path and leaves the checkout
unchanged. Its `revision` must identify the assigned HEAD. The coordinator stores
that report after auditing the tree. There is no worker-authored status registry.

## Revision and recovery

Runtime checkpoints preserve the assignment inputs and observed state. If the
worker exits or the host interrupts, inspect commits and the result before retrying.
A committed result may be recoverable without another worker. Uncommitted or
out-of-scope output requires reconciliation, not automatic acceptance.
