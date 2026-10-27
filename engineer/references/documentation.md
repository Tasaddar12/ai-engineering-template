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
