# Semantic validation beyond JSON Schema

Schema validation checks types and shape. A second deterministic layer must enforce:

1. IDs unique; all references exist, use compatible schema versions, and resolve within project roots. Full Git OIDs are observed, not fabricated.
2. Task dependencies equal graph dependencies; graph contains exactly live plan tasks, no cycles/self-edges or missing prerequisites; every acceptance ID is covered.
3. Unordered tasks have disjoint write/resource claims, including case-normalized ancestor paths. Concurrent reads of written contracts require dependencies.
4. Approved graph digest matches task records. A graph change invalidates isolation approval and rechecks affected candidates.
5. Transitions obey guards and expected generation. Operation IDs deduplicate effects; lease generation rejects stale output.
6. All required validation commands have successful, current evidence and satisfy their success_rule. Test discovery must report a nonzero test count; exit zero with no tests cannot satisfy a suite. A command exit code is null only when not observed to exit; timeouts and cancelled/unknown executions never pass.
7. Review pass has every expected checklist key exactly once, evidence and reasons; no blocking finding; expected role/model/independent invocation and identical candidate fingerprint. R2 must reference the applicable R1 report.
8. Completed implies observed merge and current integration/CI gates. Accepted task alone is not completed. Superseded requires valid successor lineage with no cycles.
9. Recovery preserves all original acceptance criteria and authority; graph rewrite cannot reset budgets, reuse IDs or mutate completed tasks.
10. Paths and commands meet security policy; model bindings satisfy declared ordering/capabilities; output provenance matches request.
11. Installation file hashes and ownership agree; migrations cannot rewrite project-owned artifacts without an explicit project change.
12. Archive manifests retain every referenced required evidence object. Host-local mappings are excluded from tracked portable records.

The phase-one validator implements only the foundation subset (schema shape, references, DAG, scope, coverage, examples and links). Runtime transition, effect reconciliation and gate implementations belong to PLAN-001.
