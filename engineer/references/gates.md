# Gates Taxonomy

Canonical gate types used across GSD workflows. Every validation checkpoint maps to one of these four types.

---

## Gate Types

### Pre-flight Gate
**Purpose:** Validate repository, branch, revision, assignment ownership and authorization before entry.
**Behavior:** Block only dependent work on a missing precondition; preserve completed independent slices.
**Recovery:** State the exact missing fact and first corrective action. Read required role and complete templates before writing.
**Examples:** explicit implementation authority, exact deletion ownership, existing inputs and configured checks.

### Revision Gate
**Purpose:** Evaluate output against its approved contract and return evidenced findings.
**Behavior:** Correct until resolved or specifically blocked; there is no fixed review-count exemption.
**Recovery:** Return a bounded correction packet and rerun affected checks. Never repeat an identical failed attempt without a changed hypothesis, input or tool. Preserve reusable passing evidence whose inputs remain unchanged.
**Examples:** PLAN correction, source review, documentation and integration findings.
### Escalation Gate
**Purpose:** Obtain an actual missing decision or capability.
**Behavior:** Prepare the concrete choice, preserve evidence and continue independent work.
**Recovery:** Record the human's answer and covered scope before resuming. A mode flag, retry count or unattended run never grants authorization.
### Abort Gate
**Purpose:** Stop an unsafe or unreliable operation while preserving completed work.
**Behavior:** Stop when checkout ownership is uncertain, a worker may still be writing, or an operation would discard unintegrated work.
**Recovery:** Confirm process stop, re-establish identity and ask the coordinator to assign a safe continuation. A wait timeout alone does not prove worker exit.

## Gate Matrix

| Workflow | Phase | Gate Type | Artifacts Checked | Failure Behavior |
|----------|-------|-----------|-------------------|------------------|
| plan-phase | Entry | Pre-flight | REQUIREMENTS.md, ROADMAP.md | Block with missing-file message |
| plan-phase | Step 12 | Revision | PLAN.md quality | Return bounded correction until resolved or blocked |
| plan-phase | Post-revision | Escalation | Unresolved issues | Surface to developer |
| execute-phase | Entry | Pre-flight | PLAN.md | Block with missing-plan message |
| execute-phase | Completion | Revision | SUMMARY.md completeness | Re-run incomplete tasks |
| verify-work | Entry | Pre-flight | SUMMARY.md | Block with missing-summary |
| verify-work | Evaluation | Escalation | Failed criteria | Surface gaps to developer |
| next | Entry | Abort | Error state, checkpoints | Stop with diagnostic |

---

## Implementing Gates

Use this taxonomy when designing or auditing workflow validation points:

- **Pre-flight** gates belong at workflow entry points. They are cheap, deterministic checks that prevent wasted work. If you can verify a precondition with a file-existence check or a config read, use a pre-flight gate.
- **Revision** gates belong after a producer step where quality varies. Never repeat an identical failed attempt; change the hypothesis or escalate a concrete blocker. A count does not waive unresolved findings.
- **Escalation** gates belong wherever automated resolution is impossible or ambiguous. They are the safety valve between revision loops and abort. Present the developer with clear options and enough context to decide.
- **Abort** gates belong at points where continuing would cause damage, waste significant resources, or produce meaningless output. They should preserve state so work can resume after the root cause is fixed.

**Selection heuristic:** Start with pre-flight. If the check happens after work is produced, it is a revision gate. If the revision loop cannot resolve the issue, escalate. If continuing is dangerous, abort.

## Additional gate routes

| Operation | Gate | Condition / outcome |
|-----------|------|---------------------|
| UAT | Human acceptance | Required actions and actual human acceptance remain pending until observed |
| Publication | Current evidence | Draft first push is tracking; ready/merge require current verification and merge requires user instruction |
| Recovery | Ownership / confirmed stop | Preserve uncertain processes and worktrees; reassign only after confirmed stop |

No review-count cap makes a failing result acceptable. Continue productive correction or report the concrete blocker.
