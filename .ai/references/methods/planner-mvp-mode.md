# Planner — Tracer-First Decomposition (Vertical Slices)

Tracer-first is the default planning method. A tracer is a thin production-quality
end-to-end slice, expressed as a supported `type="auto"` task. The syntax change
does not waive the early integration feedback gate. If a non-behavioral assignment
cannot benefit from a tracer, explicitly record the exception and its verification
rationale in the PLAN rather than silently treating the method as optional.

## Core Rule

**Decompose by feature slice, not by technical layer.** Every task must move the user-facing capability forward. After each task, a real user can click through more of the feature than they could before.

**Forbidden** under tracer-first:
- "Create the database schema" as a standalone task
- "Build the API layer" as a standalone task
- "Wire up the UI" as a final integration task

**Required** under tracer-first:
- The leading `tracer` task produces a working end-to-end path — production-quality, not a prototype. Stubs are allowed ONLY where they can later be filled without an architectural change; the happy path must be real.
- Each subsequent expansion task either adds a new slice OR refines an existing slice (validation, error states, edge cases).
- When useful, The phase goal is framed as a user story: "**As a** [user], **I want to** [do X], **so that** [Y]."

## Task Order Pattern

For a feature `F`:

1. **Tracer slice** — the thinnest end-to-end path (UI form → API endpoint → DB read/write), wired through every layer with a real runnable `<verify>`. This task is always `type="auto"`; production-quality, not a prototype; stubs only where later-fillable without an architectural change. When TDD is assigned it *also* starts red — its first move is a failing end-to-end test for the happy path of `F`.
2. **Real data layer** — replace any stubs from the tracer with real queries.
3. **Validation + error states** — invalid input, network failure, empty states.
4. **Production polish** — loading indicators, edge cases, accessibility checks.

Tasks 2-4 are not always all needed; gate by the phase's acceptance criteria.

## Walking Skeleton for a New Application

When the approved phase establishes a new application, the first slice proves the chosen architecture:

- The "feature" is the application itself. Pick the smallest meaningful capability that proves the full stack works (e.g., "user can sign up and see their name on a dashboard").
- For an approved web application with these layers, cover:
  - Project scaffold (framework init, routing, build, lint)
  - One real DB read/write when persistence is in scope
  - One real UI interaction wired to the API when those layers are in scope
  - Deployment to a dev environment (or a documented local-run command that exercises the full stack)
- Record framework, DB, deployment, auth and directory-layout decisions in existing phase context/specification through the coordinator. An assigned architecture document may hold details; no separate skeleton template is required.

These recorded architectural decisions constrain later slices; preserve them unless an authorized decision changes them.

## Anti-Patterns to Reject

- **Layer cake disguised as slices.** Three "vertical" tasks where Task 1 is "all the schemas", Task 2 is "all the endpoints", Task 3 is "all the UI" — that is horizontal planning with new labels. Reject.
- **Skeleton bloat.** Walking Skeleton is the *thinnest* working stack, not "Phase 1 of a normal app." If Skeleton has more than ~5 tasks, you are not skeletonizing.
- **Premature SPIDR splitting.** Changing phase scope belongs to the user and coordinator, not the planner. If the phase scope feels too large, surface it via the verification loop, do not split silently.

## Acceptance Test for Your Plan

Before emitting the plan, ask: **after Task N completes, can a real user *do* something they could not do after Task N-1?** If the answer is "no, but the foundation is laid", you have a horizontal task disguised as a slice. Restructure.
