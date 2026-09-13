# Current Behavior Specification Template

Template for `.planning/specs/SPEC-NNN-capability.md`.

**Purpose:** Describe verified current behavior at a known deliverable revision.
A future agent should be able to tell what the capability does, where it stops,
and what evidence supports each claim.

**Producer:** A coder documenting an assigned nearby contract or a documentor
working from integrated implementation and actual checks.

**Downstream consumers:**

| Consumer | Uses this record to |
|---|---|
| Onboarding agent | Establish the implemented baseline without inventing product intent |
| Researcher | Compare a proposed change with existing interfaces and constraints |
| Planner and checker | Identify required preservation, regression coverage and approved transitions |
| Coder | Implement against current contracts and detect unintended behavior changes |
| Verifier | Trace a documented claim through implementation and observable evidence |
| Guide author | Explain actual usage and limitations accurately |

**Distinction:** The upstream [`spec.md`](spec.md) produces a phase's desired
`NN-SPEC.md` before implementation. This local template produces an evidenced
current contract after implementation. A locked requirement is not proof that it
already works. Keep both records when the transition needs both.

---

## File Template

```markdown
# SPEC-[NNN]: [Capability]

**Verified revision:** [Exact source revision covered by the evidence]
**Last reconciled:** [YYYY-MM-DD]
**Owning source:** [Main implementation paths or public interface]
**Related phase:** [.planning/phases/NN-name/NN-CONTEXT.md]

## Capability and scope

[One paragraph naming the user or caller, triggering action and observable
outcome. State which deployment/configuration/version this contract covers.]

**Included:**
- [Concrete behavior covered here]

**Excluded:**
- [Adjacent capability or configuration that has a different owner]

## Behavior

| Trigger or input | Preconditions | Observable result | Evidence ID |
|---|---|---|---|
| [Action with concrete input] | [Required state/configuration] | [Specific output or side effect] | [E1] |

[Explain ordering, persistence or cross-component interactions only where they
change what a caller can observe. Link usage examples in the owning guide.]

## Interfaces and data

| Interface or stored artifact | Producer | Consumer | Contract and location |
|---|---|---|---|
| [API, command, event or file] | [Actual writer/caller] | [Actual reader/handler] | [Format, required fields and authoritative path] |

[Record units, identities, compatibility constraints, serialization or path rules
when they affect correct use. Link exact definitions instead of duplicating a
large schema or configuration reference.]

## Acceptance examples

- **Given** [specific starting state], **when** [action], **then** [observable result]. [E1]
- **Given** [boundary or invalid input], **when** [action], **then** [defined failure/preservation behavior]. [E2]

## Invariants and boundaries

- [Property that must remain true across the covered operations]
- [Side effect that must not occur, with evidence]
- [Compatibility or resource boundary callers must respect]

## Errors, interruptions and recovery

| Condition | Caller-visible result | Preserved or changed state | Recovery action | Evidence ID |
|---|---|---|---|---|
| [Invalid input, timeout or interruption] | [Error/status] | [Concrete state] | [Supported action or explicit limitation] | [E2] |

[If a category is inapplicable, say why. Do not imply recovery is automatic when
it requires inspection, reconciliation or a user decision.]

## Evidence

| ID | Claim | Implementation and consumer | Actual check and result | Revision/environment |
|---|---|---|---|---|
| E1 | [Behavior above] | [Source symbols and wiring] | [Exact command/observation and outcome] | [Source revision and relevant settings] |
| E2 | [Failure or boundary behavior] | [Failure path and caller] | [Exact regression or observation and outcome] | [Source revision and relevant settings] |

**Evidence limits:** [Untested platforms, mocked boundaries, unavailable services,
manual-only observations or missing proof. Distinguish an observed pass from an
inference based only on source inspection.]

## Known gaps and authorized transitions

| Item | Current observed state | Required or proposed target | Owning phase/finding |
|---|---|---|---|
| [Gap or transition, if any] | [What the evidence shows today] | [Valid requirement or clearly labeled proposal] | [Exact source of authority and tracking link] |

[Write “None identified within the checked scope” when that is accurate. A gap
against valid acceptance remains a defect; documenting it does not satisfy the
requirement or authorize a weaker contract.]

## Related records

- Product outcome: [.planning/REQUIREMENTS.md and requirement IDs]
- Phase target and decisions: [NN-SPEC.md if used; NN-CONTEXT.md]
- Rationale: [Relevant ADRs, if any]
- User/operator guide: [Responsible guide]
- Integrated proof: [SUMMARY and VERIFICATION]
```

## How to fill it

1. Identify the capability's actual callers, entry points, configuration and data
   flow. Read the implementation and checks at the revision being described.
2. Read valid existing requirements and phase decisions before resolving a
   discrepancy. Code is evidence of behavior, not automatic authority to weaken
   approved acceptance.
3. State claims as observable triggers and results. Include a representative
   success case, meaningful boundary and applicable failure or interruption.
4. Trace connections between producers and consumers. A parser existing in one
   file does not prove the public command invokes it.
5. Record checks actually run, including environment, outcome and limitations.
   If a check was unavailable, say so; do not silently turn an intended command
   into evidence of a pass.
6. Resolve conflicts on the responsible side. Incorrect documentation needs an
   evidenced correction; implementation violating a valid requirement needs a
   repair. Keep proposed behavior in the phase until verified.
7. Assign evidence IDs so repeated claims can reference the same proof. Keep
   detailed logs in the phase or test artifacts rather than pasting entire logs.
8. Update the contract in the same phase as the behavior and include its exact
   path and coverage in the responsible component's SUMMARY.

## Good and bad examples

### Observable behavior

**Good:** “Given a stopped worker with a clean committed SUMMARY, resume audits
its commits and runs the required checks before integration. It does not launch
another worker for that completed output. Evidence E3 covers the recorded source
revision using an interrupted-process fixture.”

**Why it works:** It describes a trigger, conditions, observable effects and a
specific recovery boundary that can be checked independently.

**Bad:** “Recovery is robust and handles interruptions.”

**Why it fails:** Neither a caller nor a verifier can tell what is guaranteed.

### Evidence strength

**Good:** “The ownership regression creates a real Git worktree and commits an
unassigned file; the coordinator rejects integration and preserves the checkout.
The external hosting API is simulated, so this check does not prove live hosting
permissions.”

**Why it works:** It says what was exercised and where the evidence stops.

**Bad:** “All production workflows are validated,” supported only by a file
existence assertion or an agent's successful exit code.

**Why it fails:** Structural evidence cannot establish connected behavior.

### Required behavior versus a defect

**Good:** “The approved requirement rejects expired tokens. The inspected handler
accepts the reproduced expired token; this is gap AUTH-4, owned by phase 03. The
contract retains the rejection requirement and marks verification unresolved.”

**Why it works:** It preserves intent while accurately recording the defect.

**Bad:** Change the contract to “expired tokens are accepted” solely because a
bug currently allows them.

**Why it fails:** The document would disguise a required repair as completion.

### Data location

**Good:** “Tracked phase decisions and summaries live under `.planning/phases/`.
Local process checkpoints live under the Git common directory's `ai/phases/` and
do not travel with a clone.”

**Why it works:** It identifies lifecycle and persistence, not just filenames.

**Bad:** “Everything is in the planning directory.”

**Why it fails:** A recovery agent would miss the actual process evidence.

## Completion and downstream handoff

- The title names one coherent capability and its scope is explicit.
- Every material present-tense claim has inspected implementation evidence.
- Recorded checks name their revision, actual result and relevant limits.
- Failure paths and important negative guarantees have meaningful evidence.
- Current behavior, valid unmet requirements and future proposals are distinct.
- The current contract links to rationale and usage without becoming a history log.
- SUMMARY tells the verifier which claims changed and which required coverage
  remains unresolved. Unresolved required documentation prevents completion.

## Lifecycle

Create a current specification when it saves future investigation or documents a
required interface. Reconcile it when behavior, configuration or evidence changes.
Keep the current contract readable; preserve ordinary history in Git and phase
records. Use an ADR for a significant rationale change. A later implementation
revision invalidates claims whose supporting behavior changed until rechecked;
copying an old verification date does not refresh the evidence.
