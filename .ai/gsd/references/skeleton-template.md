# SKELETON.md Template

> Emitted by `gsd-planner` when `WALKING_SKELETON=true` (Phase 1 + `--mvp` + new project). The Walking Skeleton is the **Phase-1 special case of the tracer** — a whole-application tracer slice — so it records the architectural decisions the rest of the project's later tracer slices build on.

```markdown
# Walking Skeleton — [Project Name]

**Phase:** 1
**Generated:** {ISO date}

## Capability Proven End-to-End

> One sentence: the smallest user-visible capability that exercises the full stack.

Example: "A signed-in user can view their email on a dashboard page served by the deployed app."

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Framework | (e.g., Next.js 15 App Router) | Why this fits the project |
| Data layer | (e.g., Postgres + Drizzle) | Why |
| Auth | (e.g., session cookies + bcrypt) | Why |
| Deployment target | (e.g., Vercel preview) | Why |
| Directory layout | (e.g., feature-folders under src/features/*) | Why |

## Stack Touched in Phase 1

- [ ] Project scaffold (framework, build, lint, test runner)
- [ ] Routing — at least one real route
- [ ] Database — at least one real read AND one real write
- [ ] UI — at least one interactive element wired to the API
- [ ] Deployment — running on dev environment OR documented local full-stack run command

## Out of Scope (Deferred to Later Slices)

> Anything that is *not* in the skeleton. Be explicit — this list prevents future phases from re-litigating Phase 1's minimalism.

- (e.g., password reset, email verification, multi-tenancy)

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without altering its architectural decisions:

- Phase 2: [next user capability]
- Phase 3: [next user capability]
- ...
```


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
