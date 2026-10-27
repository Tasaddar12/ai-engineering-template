# Documentation obligations

Document changed behavior where its readers need it. The assigned PLAN declares `documentation`; the SUMMARY records delivered paths and actual evidence, and the verifier checks accuracy against the integrated revision.

| Change | Required documentation |
|--------|------------------------|
| User command / workflow | Purpose, inputs, branch outcomes, gates and result |
| Runtime interface | Exact argv, field shape, defaults, errors and consumers |
| Public API | Supported inputs/outputs, failures and version constraints |
| Operational behavior | Setup, ownership, bounded recovery and rollback |
| Significant architectural choice | PROJECT Key Decisions entry, with an optional ADR for rationale |
| Artifact contract | Full template, registry and producer/consumer agreement |
| No documentation impact | Explicit reason tied to the actual change |

Read complete templates; retain method bodies and detailed examples. Update owning facts and link consumers to them. Keep examples runnable for the stated shell and actual configuration. Never claim an unimplemented operation, installed tool, registered command or successful check.

## Verification

A doc-verifier compares instructions with source, actual interfaces, artifact fields and acceptance. Return exact path/line, mismatch, authority and required correction. Source-changing doc-writers commit their owned changes; read-only doc-verifiers return evidence without a completion commit.

## Decision ownership and history

PROJECT Key Decisions owns decisions through `state.add-decision`. ADRs explain optional rationale and link to the owning entry. Preserve history in Git and Key Decisions; do not create parallel decision lifecycle tables or silently delete rationale.

## Reporting

Record changed paths, why readers need them, inspected revision, checks actually run and pending evidence. If the user defers checks, preserve that order and label validation pending. Missing documentation evidence remains a gap when required by acceptance.

## Per-obligation disposition

Every declared documentation obligation must reach exactly one disposition before readiness:

| Disposition | Required evidence | Effect |
|---|---|---|
| Updated and verified | Changed owned path, exact source revision, completed writer commit and independent claim result | Obligation satisfied for that revision. |
| Verified unchanged | Existing exact section still describes the changed interface/outcome; cite source and independent comparison | No artificial rewrite required. |
| Not applicable | Concrete reason tied to the actual change and intended reader; cite the obligation/authority | No document change, with an auditable reason. |
| Unresolved | Missing source, stale claim, incomplete writer, inaccessible dependency or required evidence pending | Remains a readiness gap; never counted as documented. |

Dispatch a doc-writer when user-facing behavior, installation/setup, supported commands/flags/defaults/errors, public API or schema, configuration, dependency versions, operational ownership/recovery, security controls, architecture or artifact contracts change and existing guidance no longer represents them. New reusable workflows also require usable examples, branch outcomes and result contracts. A source-only internal refactor with no reader-visible effect can be verified unchanged or not applicable, with a reason. Do not claim a future writer will document delivered work.

The writer receives the integrated source interface it must document, exact owned document paths, complete applicable template, disposition list, source revision and explicit dependency ordering. If another producer has not yet delivered that interface, retain the dependency and wait for it; do not write guessed API facts. Every command example needs parser/manifest provenance. Execute it only when authorized; otherwise mark runtime validation unverified and preserve pending execution separately from a static claim pass.
