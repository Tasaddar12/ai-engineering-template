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

Read required skill paths from IMPLEMENT's Read first section in the assigned
checkout. Commit those repository skills with the prepared inputs; fresh workers
use that revision's copy. Select additional matching skills only when useful,
without injecting every skill body. See [skill use](../../docs/AGENT-SKILLS.md)
for native discovery and hosts that need explicit paths.

## Component result

Coder/documentor workers write and commit the supplied SUMMARY path. Its
frontmatter reports `status: complete|blocked`, covered `acceptance` IDs and
covered `documentation` paths. Its body records Changes, Checks, Deviations and
Remaining, including actual command results and source areas.

A completed result must be supported by real work and evidence. Required
documentation can be verified unchanged with a reason; listing a path alone is
not proof. A blocked result preserves findings and safe partial work without
claiming successful integration. Only the coordinator integrates commits.

The verifier returns a complete report for the host adapter to save at the external
result path. A custom adapter may write it directly. The checkout stays unchanged,
and `revision` identifies the assigned HEAD. The coordinator stores the report
after auditing the tree. There is no worker-authored status registry.

## Revision and recovery

Runtime checkpoints preserve the assignment inputs and observed state. If the
worker exits or the host interrupts, inspect commits and the result before retrying.
A committed result may be recoverable without another worker. Uncommitted or
out-of-scope output requires reconciliation, not automatic acceptance.

Verifier attempts retain their process identity, source revision, result path and
worktree. Reuse requires a stopped process and valid current evidence. Follow
phase-verify with --workers-stopped when inspection establishes that a fresh
verification attempt is needed; component resume does not restart a reviewer.
