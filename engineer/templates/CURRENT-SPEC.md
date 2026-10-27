# Specification: [Bounded outcome]

---
spec: SPEC-[identifier]
status: draft
phase: [phase identifier or unassigned]
issue_refs: []
---

**Owner:** [coordinator / user]
**Approved by / at:** [actual decision or pending]
**Source:** [user request and evidence]

## Problem and intended outcome

[State what the user needs to accomplish and the observable result.]

## Scope

### Included

[Concrete delivered behaviors and interfaces.]

### Excluded

[Explicit boundaries; research cannot add exclusions or defer approved scope.]

## Users and entry points

| User / actor | Entry point | Preconditions | Outcome |
|--------------|-------------|---------------|---------|
| [actor] | [URL / command / API] | [fixture / authorization] | [observable behavior] |

## Requirements

| ID | Requirement | Acceptance evidence | Source |
|----|-------------|---------------------|--------|
| [REQ-01] | [testable obligation] | [behavioral check] | [request / decision] |

## Interfaces and data

[Exact input/output types, enum values, error shapes, persistence and migration rules. Cite existing interfaces rather than inventing replacements.]

## User flows

### Successful flow

1. [Concrete trigger and input].
2. [System action and observable state change].
3. [Completion evidence].

### Failure and recovery

[Bad input, unauthorized actor, unavailable dependency, timeout, cancellation and retry behavior. State what remains durable and what must never be retried blindly.]

## Edge Coverage

| Requirement | Edge | Acceptance predicate | Status | Verification |
|-------------|------|----------------------|--------|--------------|
| [REQ-01] | [boundary / empty / duplicate / concurrent / interrupted] | [observable invariant] | [resolved / unresolved] | [explicit / backstop] |

Keep unclassified edges unresolved. A backstop predicate without explicit evidence routes to human-needed; never infer a pass from prose.

## Prohibitions

| ID | Requirement | Prohibition | Status | Verification |
|----|-------------|-------------|--------|--------------|
| [P-01] | [REQ-01] | [specific must-NOT outcome] | unverified | [wired evidence or missing] |

Use the full [prohibition protocol](../references/prohibition-probe.md). Preserve flagged unverified items without inventing check descriptors.

## Security and trust boundaries

| Threat ID | Input / boundary | Abuse case | Mitigation | Evidence | Canonical issue |
|-----------|------------------|------------|------------|----------|-----------------|
| [T-{phase}-NN] | [boundary] | [abuse] | [control] | [behavioral check] | [URL / Pending reason] |

## Documentation and operations

[Required guides, runbooks, configuration, deployment authorization, rollback and monitoring.]

## Acceptance protocol

[Exact actions, fixtures, expected outcomes and required human judgment. Link the UAT protocol; human acceptance cannot be inferred from automated checks.]

## Open questions

| ID | Missing decision | Dependent scope | Owner / next action |
|----|------------------|-----------------|---------------------|
| [Q-01] | [decision] | [blocked scope only] | [owner] |

## Change control

Record approved scope changes in the owning CONTEXT / PROJECT Key Decisions and runtime-owned roadmap or requirements fields. Preserve specification history. A draft, approved design or complete specification does not authorize implementation.
