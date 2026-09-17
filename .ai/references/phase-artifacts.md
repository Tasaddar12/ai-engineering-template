# Phase artifacts

A stable directory `.planning/phases/NN-slug/` grows as its phase progresses. Numbered
component instruction/result pairs live here; they have no separate backlog or
lifecycle. Use [templates](../templates/README.md) for their shapes.

| Artifact | Created when | Consumed by |
|---|---|---|
| `NN-CONTEXT.md` | Request/discussion | Everyone working on relevant phase scope |
| `NN-DISCUSSION-LOG.md` | Every phase discussion; update after each exchange | Human reference; decisions come from CONTEXT |
| `NN-RESEARCH.md` | Investigation is needed | Preparer, checker and affected workers |
| `NN-VALIDATION.md` | Checks need a shared strategy | Preparer, checker and verifier |
| `NN-CC-PLAN.md` | A component is ready to specify | Its fresh coder or documentor |
| `NN-CC-SUMMARY.md` | A worker completes or blocks | Coordinator, dependents and verifier |
| `NN-VERIFICATION.md` | Integrated behavior is independently assessed | Coordinator and publication checks |
| `NN-UAT.md` | User acceptance is required/useful | Acceptance session and publication checks |
| `.continue-here.md` | Work pauses with useful continuation context | Returning coordinator |

Use the full templates for both authoring instructions and output structure.
CONTEXT retains upstream decision categories, canonical references, existing-code
insights and deferred ideas. PLAN retains task-level actions, verification, done
criteria and goal-backward `must_haves`. SUMMARY retains dependency effects,
changes, decisions, issues and evidence.

The [runtime contract](../runtime/TEMPLATE-CONTRACT.md) specifies additive metadata
for authorization, ownership, checks, documentation coverage and exact revision
evidence. Do not substitute the previous shortened records for these full outputs.
Dependencies use NN-CC IDs within a phase; ownership prefixes end in `/` and
required documentation names exact files.

A small bug phase may have only CONTEXT, DISCUSSION-LOG, one PLAN/SUMMARY pair
and VERIFICATION. Add reproduction and regression proof. A documentation-only phase
uses `kind: documentation`; research-only work can end with findings without
claiming implemented or delivered product behavior. Optional files are omitted
when they would repeat another owner.
