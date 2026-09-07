# Two independent higher-capability review gates

R1 asks whether the task is correctly implemented. R2 asks whether it fits the project and plan. Separate invocations with fresh contexts are mandatory; the same configured high-capability model may serve both. The implementation agent cannot self-approve. R2 receives R1 evidence but independently examines the diff and relevant source.

## Implementation checklist

| ID | Required evidence |
| --- | --- |
| R1-01 | Each task acceptance criterion satisfied |
| R1-02 | Spec requirements and exclusions respected |
| R1-03 | Functional correctness traced through changed code |
| R1-04 | Error paths and resource cleanup behave correctly |
| R1-05 | Boundary and edge cases addressed |
| R1-06 | Tests exercise meaningful behavior and failure cases |
| R1-07 | No unnecessary scope expansion |
| R1-08 | No unrelated file changes |
| R1-09 | Maintainable code and explicit interfaces |
| R1-10 | Basic security and trust-boundary concerns checked |
| R1-11 | Relevant documentation updated accurately |

## Consistency checklist

| ID | Required evidence |
| --- | --- |
| R2-01 | Architecture boundaries respected |
| R2-02 | Accepted ADRs honored |
| R2-03 | Completed sibling handoffs remain compatible |
| R2-04 | Interfaces and imports match contracts |
| R2-05 | API behavior and versioning compatible |
| R2-06 | Database/schema/migration compatibility |
| R2-07 | Naming and repository conventions followed |
| R2-08 | No duplicate implementation |
| R2-09 | No conflicting abstractions |
| R2-10 | Tests assert intended behavior rather than incidental code |
| R2-11 | Documentation matches integrated behavior |
| R2-12 | Plan assumptions remain valid |

Each item is pass/fail/not_applicable with rationale and evidence references. N/A must be reasoned and permitted by policy; missing evidence is fail or inconclusive, never pass. Verdict pass requires all applicable items passed and no unresolved blocking finding. Findings carry severity, category (`defect`, `structural`, `missing_evidence`, `policy`), paths, explanation, expected fix and acceptance linkage.

## Candidate identity and invalidation

The fingerprint hashes task ID + graph revision + exact base/head OIDs + diff digest + spec/plan/ADR/contract/handoff digests + validation evidence digest + checklist version + policy/model profile version. Both review reports must match that same fingerprint and their own role/checklist. Model provenance includes provider, actual returned model ID, configured profile, capability rank and invocation ID. Missing required provenance fails the gate. Do not assume model name lexical order means capability.

Material R1 fixes: new candidate, targeted validation, fresh R1 then R2. Material R2 fixes: invalidate both, validation, fresh R1 then R2. New integration base also requires both reviews. Review reports never mutate; superseded review results remain auditable.

## Plan integration checklist

INT-01 all plan criteria; INT-02 task combination; INT-03 gaps at boundaries; INT-04 interfaces; INT-05 duplicate functionality; INT-06 architecture; INT-07 end-to-end behavior; INT-08 integrated test coverage; INT-09 final documentation. Run on the exact assembled code tree and context. The checkpoint commit containing the review report is excluded from its own fingerprint; code and project documents are included. A state-only delivery commit may reuse the gate only if those inputs are byte-identical and state snapshot validation passes.
