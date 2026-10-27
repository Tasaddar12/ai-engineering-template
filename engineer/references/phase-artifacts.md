# Phase artifacts and owners

Read [the canonical registry](../templates/README.md) and complete template before writing. These are record contracts, not independent implementation authority.

| Artifact | Producer | Consumers | Required purpose |
|----------|----------|-----------|------------------|
| NN-CONTEXT.md | discuss coordinator | researcher/planner/executor | Decisions, discussion gate, actual implementation instruction |
| NN-DISCUSSION-LOG.md | discuss coordinator | dispute/audit reconstruction | Incremental options, answers and recommendation evidence |
| NN-RESEARCH.md | phase-researcher | planner/checker | Current-source and primary documentation evidence |
| NN-MM-PLAN.md | planner | executor/checker/verifier | Full tasks, ownership, acceptance, docs, checks argv and issues |
| NN-MM-SUMMARY.md | executor | coordinator/verifier | Actual commits, evidence, delivered coverage, Remaining and threats |
| NN-VALIDATION.md | planner / assigned auditor | checker/verifier | Real validation architecture and 2-in-3 sampling |
| NN-VERIFICATION.md | coordinator from read-only evidence | ship/progress | Joined frozen-revision verdict and v4 covered digest |
| NN-UAT.md | coordinator with actual human | audit/verify/gap planning | Runnable actions, actual responses, final human acceptance |
| NN-SECURITY.md | coordinator from auditor | verify/ship | Threat mitigation evidence and open risks |
| NN-UI-SPEC.md | ui-researcher / coordinator | ui-checker/executor | Approved visual and interaction contract |
| REVIEW.md / NN-REVIEWS.md | code-reviewer | fixer/coordinator | Stable findings, authority, evidence and disposition |
| .continue-here.md | coordinator | continuation | Exact completed/remaining scope and revision |

The runtime owns structured phase numbering, roadmap/state/project decisions, requirements traceability, todo/quick/milestone structures and archive operations. Read [planning-record integrity](template-contract.md#planning-record-integrity). An optional ADR preserves rationale linked from PROJECT Key Decisions, never a second decision owner.

A quick task uses its own `.planning/quick/NNN-slug/NNN-VERIFICATION.md` with `quick: NNN`, not a fabricated phase ID. Keep required metadata and source identity consistent across producer and consumer.

## Complete artifact examples and evidence boundaries

**Bug repair:** preserve the concrete symptom and reproduction, affected requirement/acceptance, before-fix observation and the focused regression assertion in the assigned PLAN. SUMMARY records the actual repair commits, executed RED/GREEN evidence (or explicitly deferred evidence), documentation disposition and remaining causes. VERIFICATION independently checks the integrated trigger → implementation → observable result and its error/empty behavior; a repair commit alone is not proof the symptom disappeared.

**Documentation-only change:** the PLAN names exact document paths, authoritative source interfaces, claim obligations and intended readers. The doc-writer commits the assigned documents and ordinary required SUMMARY; the independent doc-verifier returns its full claim JSON without executing document commands. No product implementation or human-UAT success is invented for a prose change. An explicit maintenance assignment can forbid SUMMARY artifacts, but that exception is scoped to that assignment.

**Research without implementation:** phase-researcher commits only its assigned RESEARCH artifact with current dependency versions, primary sources, observed checks and limits, unresolved choices and named blocked consumers. It does not write source, a product-delivery SUMMARY, STATE or new approval. The planner consumes that artifact only after confirmed producer stop/integration. A research finding can recommend an option only with actual relevant validation or an explicit unvalidated label under the user's check ordering.
