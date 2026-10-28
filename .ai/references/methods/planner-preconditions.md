# Planner Preconditions — `<precondition>` Element

> Local planning guidance for explicit prerequisites. The worker asserts these
> facts; the Python scheduler does not parse a precondition expression language.

## The contract triad

Every task in a PLAN.md participates in a three-sided contract:

| Contract side | PLAN element | When it binds |
|---|---|---|
| **Precondition** | `<precondition>` (optional element on `<task>`) | Before the task begins. What must already be true for the task to run safely. |
| **Postcondition** | `<verify>` + `<done>` + `<acceptance_criteria>` | After the task ends. What the task guarantees on return. |
| **Invariant** | `must_haves.truths` (plan frontmatter) | Across the whole plan/phase. What always holds. |

The PLAN already models postconditions and invariants well. `<precondition>` closes
the missing side: it states, in runnable/checkable terms, what must be true
*before* a task begins — so an autonomous executor stops the instant an
assumption is false, instead of building ten atomic commits on top of a
migration that never ran.

This is the front-of-task companion to the tracer-bullet proposal:
tracers prove the *architecture* end-to-end before expansion; preconditions prove
each expansion task's *assumptions* before it runs. Together they close both ends
of the "outrunning your headlights" failure mode.

## When to emit `<precondition>`

Emit `<precondition>` ONLY when a task relies on state the plan's own `depends_on`
ordering does not already guarantee. Three cases cover every legitimate use; if
the prerequisite is local task ordering, describe that ordering; between plans
use `depends_on` instead of a redundant precondition.

### Case 1 — External service setup (`user_setup`)

The task depends on an external service the developer must set up (account
creation, secret retrieval, dashboard configuration, billing activation). The
`user_setup` frontmatter field already enumerates these steps; `<precondition>`
on the consuming task ties a specific setup step to a specific task so the
executor halts if the setup was skipped.

```xml
<task type="auto">
  <name>Send welcome email via SendGrid</name>
  <precondition>SENDGRID_API_KEY is set (user_setup step 1 complete)</precondition>
  <files>src/email/welcome.ts</files>
  <action>...</action>
  <verify>...</verify>
  <done>Welcome email dispatched for a test user</done>
</task>
```

### Case 2 — Prior-phase artifact dependency

The task consumes an artifact a prior phase promised (a generated schema, a
migration's dist output, a contract file). Record cross-phase dependencies in phase CONTEXT through the coordinator. A
`<precondition>` adds the concrete artifact assertion; it does not replace that dependency.

```xml
<task type="auto">
  <name>Generate TypeScript client from schema</name>
  <precondition>dist/schema.json from Phase 02 exists and is non-empty</precondition>
  <files>src/client/generated.ts</files>
  <action>...</action>
  <verify>...</verify>
  <done>Client generated and compiles</done>
</task>
```

### Case 3 — Environment variable / runtime configuration

The task shells out to a tool, hits an API, or runs a script that requires an
environment variable or runtime config that exists *now* (not at plan time).

```xml
<task type="auto">
  <name>Add /reveal endpoint handler</name>
  <precondition>server bootstraps and responds to GET /health (from the tracer slice)</precondition>
  <files>server/reveal.ts</files>
  <action>...</action>
  <verify>curl /reveal?path=... opens the OS file manager</verify>
  <done>Endpoint committed and manually verified</done>
</task>
```

## Format

`<precondition>` is a single line of prose inside the `<task>` element, placed right after `<name>` and before `<files>`. It is **prose, not a structured block** — concrete enough that the executor agent can run a read-only check (file existence, env var presence, idempotent `GET /health`-style ping), prose enough not to require a parser extension. The executor MUST verify with read-only checks only: no writes, no network POSTs, no secret emission. If a side-effecting check seems required, the executor halts and surfaces a checkpoint rather than running it.

```xml
<task type="auto">
  <name>...</name>
  <precondition>...</precondition>
  <files>...</files>
  <action>...</action>
  <verify>...</verify>
  <done>...</done>
</task>
```

## What NOT to put in a `<precondition>`

- **Vague readiness checks.** "The system is ready" is not checkable. Name the
  concrete signal: a `curl` response, a file path, an env var name.
- **Intra-plan ordering.** "Task 1 has completed" — that is ordinary task ordering;
  `depends_on` connects distinct plans. Reserve `<precondition>` for state the plan's wave/dependency graph
  cannot express.
- **Implementation choices.** "We have chosen library X" — that belongs in the
  `<action>` body or a `## Decisions` row, not a runtime fact.
- **Things the task itself creates.** A precondition names a fact the task
  *assumes*; if the task produces it, it is a postcondition (`<done>`).

## Executor behavior (assertion contract)

The executor agent reads `<precondition>` before any other task work:

| State | Executor behavior |
|---|---|
| **Absent** | No visible change — execute the task exactly as today. Back-compat for every existing plan. |
| **Met** | No visible change — proceed with the task. The precondition is logged in the SUMMARY only if it was non-trivial to verify. |
| **Unmet** | STOP dependent work and return a blocked SUMMARY naming the unmet fact and evidence. Preserve completed authorized slices. Unmet preconditions are NEVER auto-approved — a missing prerequisite is not a verification step a human can rubber-stamp, it is a fact the executor cannot establish on its own. |

## Plan-structure validation

`<precondition>` is explanatory task content. Keep required task fields and local
frontmatter from [the runtime contract](../../runtime/TEMPLATE-CONTRACT.md).
The worker checks the prerequisite; do not claim an automatic parser evaluates it.

## Method boundaries

This method does not add:

- **Structured precondition DSL** (e.g. `<precondition kind="env" var="X"/>`).
  Prose-first keeps complexity flat; structured validation can land in a later
  PR if prose proves insufficient.
- **Automatic precondition emission for every task.** The three cases above are
  a hard ceiling (Zawinski's Law guard). Most tasks do not need a precondition.
- **Cross-task preconditions.** A precondition binds one task to one fact. Use
  `depends_on` or a parent plan's `must_haves` for multi-task contracts.

## See also

- *The Pragmatic Programmer*, Topic 23 — "Design by Contract" (Hunt & Thomas).
- [runtime contract](../../runtime/TEMPLATE-CONTRACT.md) — supported execution fields.
- [Thin end-to-end slices](planner-mvp-mode.md) — architectural evidence before expansion.
- [coder](../../agents/coder.md) → `<execution_flow>` → precondition check step — the
  assertion surface that consumes what this reference defines.
