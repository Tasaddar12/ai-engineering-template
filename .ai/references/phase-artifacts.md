# Phase artifacts

A stable directory `.ai/phases/NN-slug/` grows as its phase progresses. Numbered
component instruction/result pairs live here; they have no separate backlog or
lifecycle. Use [templates](../templates/README.md) for their shapes.

| Artifact | Created when | Consumed by |
|---|---|---|
| `NN-CONTEXT.md` | Request/discussion | Everyone working on relevant phase scope |
| `NN-DISCUSSION-LOG.md` | Conversation history is worth retaining | Human reference; decisions come from CONTEXT |
| `NN-RESEARCH.md` | Investigation is needed | Preparer, checker and affected workers |
| `NN-VALIDATION.md` | Checks need a shared strategy | Preparer, checker and verifier |
| `NN-CC-IMPLEMENT.md` | A component is ready to specify | Its fresh coder or documentor |
| `NN-CC-SUMMARY.md` | A worker completes or blocks | Coordinator, dependents and verifier |
| `NN-VERIFICATION.md` | Integrated behavior is independently assessed | Coordinator and publication checks |
| `NN-UAT.md` | User acceptance is required/useful | Acceptance session and publication checks |
| `.continue-here.md` | Work pauses with useful continuation context | Returning coordinator |

CONTEXT carries `phase`, `approval`, phase `depends_on` and `uat` in
frontmatter. Its body owns Goal, Acceptance, Decisions, Authorization, Open
questions and Deferred. Acceptance IDs such as A1 stay stable. Approval must
record the actual human instruction; `approved` text alone is not authority.

IMPLEMENT metadata supplies `kind`, component `depends_on`, `files`,
`resources`, `acceptance`, `documentation` and executable `checks`.
The body supplies Objective, Read first, Implementation, Verification and
Documentation. Dependencies use NN-CC IDs within the phase. Directory ownership
prefixes end in `/`; document obligations name exact paths.

A small bug phase may have only CONTEXT, one IMPLEMENT/SUMMARY pair and
VERIFICATION. Add reproduction and regression proof. A documentation-only phase
uses `kind: documentation`; research-only work can end with findings without
claiming implemented or delivered product behavior. Optional files are omitted
when they would repeat another owner.
