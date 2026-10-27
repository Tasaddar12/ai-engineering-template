# Current behavior specification template

Use this complete template for `.planning/specs/SPEC-NNN-capability.md` after inspecting implementation and actual evidence. It describes what currently works, at which revision and under which conditions.

The phase [`spec.md`](spec.md) describes desired behavior before implementation. A locked requirement, design or planned check is not proof that behavior already exists. Keep both records when a transition needs a target and an observed baseline.

**Producer:** executor documenting an assigned nearby contract, or doc-writer working from integrated source and actual checks.

| Consumer | Uses this record to |
|---|---|
| Onboarding coordinator | Establish implemented behavior without inventing product intent |
| Researcher | Compare proposed transitions with actual interfaces and limits |
| Planner / plan-checker | Identify preservation obligations, regression directions and approved changes |
| Executor | Detect unintended behavior changes |
| Verifier | Trace claims through source wiring and observable evidence |
| Guide author | Explain real usage and limitations |

## File Template

```markdown
# SPEC-[NNN]: [Capability]

**Verified revision:** [Exact source revision covered by the evidence]
**Last reconciled:** [YYYY-MM-DD]
**Owning source:** [Implementation paths and public interface]
**Related phase:** [Actual phase CONTEXT, if applicable]

## Capability and scope

[Identify the caller, trigger and observable outcome. State the covered deployment, version and configuration.]

**Included:**
- [Specific observed capability]

**Excluded:**
- [Adjacent behavior with a different owner; not an unapproved reduction in acceptance]

## Behavior

| Trigger / input | Preconditions | Observable result | Evidence ID |
|---|---|---|---|
| [Concrete action and input] | [Required state/configuration] | [Output or side effect] | [E1] |

[Explain ordering, persistence and cross-component interactions where they affect correct use. Link detailed usage to its guide.]

## Interfaces and data

| Interface / artifact | Producer | Consumer | Contract and authoritative location |
|---|---|---|---|
| [API, command, event or file] | [Actual writer/caller] | [Actual reader/handler] | [Fields, format and owning path] |

[Record units, identities, compatibility, serialization and path rules. Link large schemas instead of maintaining another copy.]

## Acceptance examples

- **Given** [specific initial state], **when** [action], **then** [observable result]. [E1]
- **Given** [invalid or boundary input], **when** [action], **then** [defined failure and preservation behavior]. [E2]

## Invariants and boundaries

- [Property preserved across covered operations]
- [Side effect that must not occur, with evidence]
- [Compatibility or resource boundary callers must respect]

## Errors, interruptions and recovery

| Condition | Caller-visible result | Preserved / changed state | Supported recovery | Evidence ID |
|---|---|---|---|---|
| [Invalid input, timeout, interruption or unavailable dependency] | [Actual error/status] | [Concrete state] | [Action or explicit limitation] | [E2] |

[Explain inapplicable categories. Do not imply automatic recovery when inspection, reconciliation or an actual decision is required.]

## Evidence

| ID | Claim | Implementation and consumer | Actual check / result | Revision and environment |
|---|---|---|---|---|
| E1 | [Observed behavior] | [Source symbols and actual wiring] | [Exact executed command or observation] | [SHA and relevant configuration] |
| E2 | [Failure or boundary behavior] | [Failure path and caller] | [Actual regression and outcome] | [SHA and limits] |

**Evidence limits:** [Untested platforms, mocked providers, inaccessible services, manual-only judgments and missing proof. Distinguish observations from source-only inference.]

## Known gaps and authorized transitions

| Item | Current observed state | Required / proposed target | Owning phase or finding |
|---|---|---|---|
| [Gap or transition] | [Actual evidence today] | [Valid acceptance or explicitly proposed behavior] | [Exact authority and canonical tracker] |

[Use None identified within the checked scope only when accurate. A documented defect still violates valid acceptance; this record cannot authorize weakening it.]

## Related records

- Product outcome: [Actual requirement IDs]
- Target and decisions: [Phase SPEC and CONTEXT]
- Rationale: [Key Decisions entry and optional ADR]
- Usage and operations: [Owning guide]
- Integrated proof: [Actual SUMMARY and VERIFICATION]
```

## How to fill it

1. Identify actual callers, entry points, configuration and data flow. Inspect implementation and checks at the stated revision.
2. Read valid requirements and accepted decisions before resolving disagreement. Existing code is behavior evidence, not authority to weaken an obligation.
3. Write observable triggers and results. Include a representative success, meaningful boundary and applicable interruption/failure cases.
4. Trace producers to consumers. An existing parser or handler does not prove the public command uses it.
5. Record only checks actually executed, with environment, result and limits. Unavailable commands remain unverified.
6. Correct the responsible side: repair false documentation with evidence; repair code that violates valid acceptance. Keep proposed behavior in its phase until verified.
7. Use stable evidence IDs instead of repeating logs. Retain detailed logs in actual check/phase evidence locations and link them.
8. Update this contract with the behavior-changing slice and identify changed claims, its exact path and unresolved obligations in the normal execution record.

## Good and bad examples

### Observable behavior

**Good:** "Given a phase whose plans outnumber its complete summaries, routing resumes it before later work and names the missing plan IDs. It does not redispatch a plan with a complete committed summary. E3 exercises a half-executed repository fixture."

**Why it works:** Trigger, conditions, effects and recovery boundaries are independently checkable.

**Bad:** "Recovery is robust and handles interruptions."

**Why it fails:** Readers cannot determine the guarantee or how to disprove it.

### Evidence strength

**Good:** "The ownership regression uses a real Git repository and commits an undeclared file; integration rejects it. The provider is simulated, so this does not prove live hosting permissions."

**Why it works:** It names the exercised boundary and evidence limit.

**Bad:** "All production workflows are validated," supported only by file existence or an agent's successful exit.

**Why it fails:** Structural evidence does not establish connected behavior.

### Required behavior versus a defect

**Good:** "Accepted requirements reject expired tokens. The inspected handler accepts the reproduced expired token; gap AUTH-4 is owned by phase 03. The contract retains rejection and records verification unresolved."

**Why it works:** Observed state and valid intended behavior stay distinct.

**Bad:** Change acceptance to permit expired tokens solely because a bug does so.

**Why it fails:** The document would conceal a required repair.

### Data location

**Good:** "Tracked decisions and summaries live under `.planning/phases/`. Local process checkpoints use runtime-returned locations under the Git common directory's `engineer/` state and do not travel with a clone."

**Why it works:** It identifies persistence and lifecycle as well as filenames.

**Bad:** "Everything is in the planning directory."

**Why it fails:** Recovery would miss process evidence and confuse it with tracked history.

## Completion and downstream handoff

- One coherent capability and its covered conditions are explicit.
- Material present-tense claims have inspected implementation and consumer evidence.
- Checks name actual revision, outcome and limits.
- Negative guarantees and failure/recovery paths have meaningful evidence.
- Observed behavior, valid unmet acceptance and future proposals remain distinct.
- Rationale and usage remain linked owners rather than copied history.
- The execution record identifies changed claims and required documentation evidence still unresolved.

## Lifecycle

Create a current specification when it preserves useful investigation or a required interface. Reconcile it when behavior, configuration or evidence changes. Preserve ordinary history in Git and phase records, significant rationale in optional ADRs linked to Key Decisions. Changed behavior invalidates affected proof until rechecked; copying an old verification date does not refresh evidence.
