---
tier: contract
authority: agent
id: SPEC-001
scope: Available document interfaces and behavior of the scaffold.
links: [ADR-001, ADR-002, AMD-001]
verification_refs: [PLAN-002]
title: Project contracts
---
> Contract: amend with evidence inside the approved scope.

# Project contracts

## Requirement

This repository provides a Markdown/YAML operating scaffold for recording
current behavior, planning changes and coordinating approved engineering
work. Its instructions and report templates are manually usable documents.

[Config](../config.yaml) owns paths and identifiers.
[Truth map](../truth-map.md) assigns facts to one owner.
[Rules](../RULES.md) routes readers to policies, workflows and evidence gates.

## Acceptance criteria

- Given a new session, AGENTS.md directs the reader to current context,
  authority, fact ownership and the assigned role.
- Given a record, its tier and authority describe allowed mutability.
  Legacy journal content receives its log tier from its path.
- Given a PLAN or FIX, its directory supplies lifecycle stage.
- Given proposed behavior, a PLAN holds exact contract wording until its
  implementation makes that wording true in a SPEC.
- Given a confirmed defect, a FIX records symptom, root cause or uncertainty,
  repair scope and before/after proof. Intake retains unconfirmed findings.
- Given a role, its description, read/write scope, steps, exclusions and
  report format define a bounded assignment.
- Given a command, it points to a workflow owning the procedure. Aliases
  share that owner rather than duplicating its steps.
- Given completed work, verification compares observed behavior with current
  contracts and reconciles the plan's promised record changes.
- Given concurrent work, a run board owns dependency waves, contention
  tracks, reservations and assignments; track evidence records review rounds.
- Given delivery, gates distinguish publication, acceptance, merge and
  exact cleanup using observed evidence.

## Invariants

Current specs contain present behavior; planned behavior and historical
rationale have separate owners. Human intent lives in state/PROJECT.md even
though that file shares a directory with mutable STATE.

Source documents, lifecycle conventions and flat templates are the product.
Each record kind has a template, ID convention and lifecycle or evidence owner.
Indexes link available [roles](../agents/README.md),
[commands](../commands/README.md) and [workflows](../workflows/README.md).

Record history is append-only where its tier requires it. An inspection
report states unavailable or unrun checks instead of inventing results.

## Explicitly out of scope

These files do not launch agents, install prompts, enforce a sandbox,
run Git hooks or supply application behavior. Optional execution facilities
must be selected and authorized by the consuming project.

## Verification

Current evidence is linked through verification_refs and the selected plan.
Document checks inspect tiers, template fields, paths, links, unique IDs,
lifecycle ownership and command/role handoffs. Executing the documented
engineering workflows requires a concrete target project and its checks.
