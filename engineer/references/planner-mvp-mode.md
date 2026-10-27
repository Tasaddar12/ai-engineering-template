# Planner — Tracer-First Decomposition (Vertical Slices)

> Default to a thin real end-to-end `type="tracer"` slice followed by outcome expansions. A tracer exception must be explicit and recorded in the PLAN with its authority and rationale; a mode flag alone does not grant the exception.

## Core Rule

**Decompose by feature slice, not by technical layer.** Every task must move the user-facing capability forward. After each task, a real user can click through more of the feature than they could before.

**Forbidden** under tracer-first:
- "Create the database schema" as a standalone task
- "Build the API layer" as a standalone task
- "Wire up the UI" as a final integration task

**Required** under tracer-first:
- The leading `tracer` task produces a working end-to-end path — production-quality, not a prototype. Stubs are allowed ONLY where they can later be filled without an architectural change; the happy path must be real.
- Each subsequent expansion task either adds a new slice OR refines an existing slice (validation, error states, edge cases).
- When the assignment supplies a user story, retain its actor, action and purpose as the acceptance frame.

## Task Order Pattern

For a feature `F`:

1. **Tracer slice** — the thinnest end-to-end path (UI form → API endpoint → DB read/write), wired through every layer with a real runnable `<verify>`. This task is always `type="tracer"`; production-quality, not a prototype; stubs only where later-fillable without an architectural change. Under `--tdd` it *also* starts red — its first move is a failing end-to-end test for the happy path of `F`.
2. **Real data layer** — replace any stubs from the tracer with real queries.
3. **Validation + error states** — invalid input, network failure, empty states.
4. **Production polish** — loading indicators, edge cases, accessibility checks.

Tasks 2-4 are not always all needed; gate by the phase's acceptance criteria.

## Minimal full-stack capability

When the assignment requests a minimal full-stack capability, select the smallest meaningful user outcome that exercises real persistence, API and interface behavior. Use the project's actual build and deployment conventions. Record the framework, data, auth, directory and run/deployment decisions in CONTEXT, and consequential choices in PROJECT Key Decisions. Do not create a separate skeleton artifact or infer deployment authority.

The bounded plan includes:

- Project scaffold using the existing framework/build/lint conventions.
- One real persistence read/write with its authorized safe fixture.
- One real interface interaction wired through the API to persistence.
- A documented local run command exercising the full stack, or an explicitly authorized dev deployment.
- Framework, data, auth, directory and run/deployment choices in CONTEXT, with consequential decisions in PROJECT Key Decisions.

A documented local command supplies the demonstration when deployment is not authorized. Preserve complete acceptance, documentation, checks argv and issue references.

## Anti-Patterns to Reject

- **Layer cake disguised as slices.** Three "vertical" tasks where Task 1 is "all the schemas", Task 2 is "all the endpoints", Task 3 is "all the UI" — that is horizontal planning with new labels. Reject.
- **Skeleton bloat.** Walking Skeleton is the *thinnest* working stack, not "Phase 1 of a normal app." Honor the configured cap and thin coherent outcome; task count alone does not prove scope.
- **Unauthorized splitting.** Scope splitting belongs to the coordinator. Return a bounded outcome/dependency proposal; do not silently split or defer authorized scope.

## Acceptance Test for Your Plan

Before emitting the plan, ask: **after Task N completes, can a real user *do* something they could not do after Task N-1?** If the answer is "no, but the foundation is laid", you have a horizontal task disguised as a slice. Restructure.
