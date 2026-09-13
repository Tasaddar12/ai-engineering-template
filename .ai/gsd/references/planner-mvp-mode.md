# Planner — Tracer-First Decomposition (Vertical Slices)

> Loaded by `gsd-planner` for the **default** tracer-first decomposition: every phase LEADS with one thin end-to-end `type="tracer"` slice, then expansion tasks. `--no-tracer` (`TRACER_MODE=false`) restores standard horizontal-layer planning. The MVP enrichment (user-story framing) and Walking Skeleton mode apply *on top* when `MVP_MODE=true` / `WALKING_SKELETON=true`.

## Core Rule

**Decompose by feature slice, not by technical layer.** Every task must move the user-facing capability forward. After each task, a real user can click through more of the feature than they could before.

**Forbidden** under tracer-first:
- "Create the database schema" as a standalone task
- "Build the API layer" as a standalone task
- "Wire up the UI" as a final integration task

**Required** under tracer-first:
- The leading `tracer` task produces a working end-to-end path — production-quality, not a prototype. Stubs are allowed ONLY where they can later be filled without an architectural change; the happy path must be real.
- Each subsequent expansion task either adds a new slice OR refines an existing slice (validation, error states, edge cases).
- *(MVP enrichment, `MVP_MODE=true`)* The phase goal is framed as a user story: "**As a** [user], **I want to** [do X], **so that** [Y]."

## Task Order Pattern

For a feature `F`:

1. **Tracer slice** — the thinnest end-to-end path (UI form → API endpoint → DB read/write), wired through every layer with a real runnable `<verify>`. This task is always `type="tracer"`; production-quality, not a prototype; stubs only where later-fillable without an architectural change. Under `--tdd` it *also* starts red — its first move is a failing end-to-end test for the happy path of `F`.
2. **Real data layer** — replace any stubs from the tracer with real queries.
3. **Validation + error states** — invalid input, network failure, empty states.
4. **Production polish** — loading indicators, edge cases, accessibility checks.

Tasks 2-4 are not always all needed; gate by the phase's acceptance criteria.

## Walking Skeleton Mode (`WALKING_SKELETON=true`)

When the orchestrator sets `WALKING_SKELETON=true` (Phase 1 of a new project under `--mvp`), the plan changes shape:

- The "feature" is the application itself. Pick the smallest meaningful capability that proves the full stack works (e.g., "user can sign up and see their name on a dashboard").
- The plan **must include**:
  - Project scaffold (framework init, routing, build, lint)
  - One real DB read/write
  - One real UI interaction wired to the API
  - Deployment to a dev environment (or a documented local-run command that exercises the full stack)
- The plan **must produce** `SKELETON.md` in the phase directory alongside `PLAN.md`. Use the template at `@.ai/gsd/references/skeleton-template.md`. `SKELETON.md` records the architectural decisions that subsequent phases will build on (chosen framework, DB, deployment target, auth approach, directory layout).

`SKELETON.md` is the architectural backbone for every later vertical slice; treat it as a contract, not a scratchpad.

## Anti-Patterns to Reject

- **Layer cake disguised as slices.** Three "vertical" tasks where Task 1 is "all the schemas", Task 2 is "all the endpoints", Task 3 is "all the UI" — that is horizontal planning with new labels. Reject.
- **Skeleton bloat.** Walking Skeleton is the *thinnest* working stack, not "Phase 1 of a normal app." If Skeleton has more than ~5 tasks, you are not skeletonizing.
- **Premature SPIDR splitting.** SPIDR splitting is the `mvp-phase` command's job (Phase 2 of the PRD), not the planner's. If the phase scope feels too large, surface it via the verification loop, do not split silently.

## Acceptance Test for Your Plan

Before emitting the plan, ask: **after Task N completes, can a real user *do* something they could not do after Task N-1?** If the answer is "no, but the foundation is laid", you have a horizontal task disguised as a slice. Restructure.


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

The complete upstream body above is retained from GSD-Core at
`c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977`; only recorded reference substitutions
and explicit local conflict corrections have been made. See
`.ai/gsd/PROVENANCE.json` for exact source hashes and changes.

Read `.ai/gsd/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/gsd-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The upstream `config.json`, `/gsd:*` commands, tool
names, hooks, and Node CLI examples describe GSD's system; this import does not
install or activate that system. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
