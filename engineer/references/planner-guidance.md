# Planner Guidance: Philosophy, Task Calibration, and Output Formats

## Coordinated user and agent workflow

The user owns intent, scope and consequential choices. The coordinator routes bounded assignments; workers implement or inspect their exact ownership. Plans record required interfaces, evidence and stop conditions. Account for read/change/check cost through `estimate_scope`, not invented time or token guarantees.

## Plans Are Prompts

PLAN.md IS the prompt (not a document that becomes one). Contains:
- Objective (what and why)
- Context (@file references)
- Tasks (with verification criteria)
- Success criteria (measurable)

## Quality Degradation Curve

| Context Usage | Quality | Claude's State |
|---------------|---------|----------------|
| 0-30% | PEAK | Thorough, comprehensive |
| 30-50% | GOOD | Confident, solid work |
| 50-70% | DEGRADING | Efficiency mode begins |
| 70%+ | POOR | Rushed, minimal |

**Rule:** honor the configured task cap and size by coherent outcomes and actual dependencies. Context estimates are advisory.

## Ship Fast

Plan -> Execute -> Ship -> Learn -> Repeat

**Anti-enterprise patterns (delete if seen):** team structures, RACI matrices, sprint ceremonies, time estimates in human units, complexity/difficulty as scope justification, documentation for documentation's sake.

---

## Task Types

| Type | Use For | Autonomy |
|------|---------|----------|
| `auto` | Authorized independently executable work | Within recorded authority |
| `tracer` | Thin real end-to-end slice | Honors human-check gates |
| `checkpoint:human-verify` | Required human judgment | Wait for actual human answer |
| `checkpoint:decision` | Choice outside delegated discretion | Wait, unless recorded delegation covers declared auto_select |
| `checkpoint:human-action` | Required secure/manual action | Wait only dependent work |

Prepare reviewable work first. Ability to invoke an API does not itself authorize publication, deployment or a human decision.

## Task Sizing

Size each task by one independently verifiable outcome. Read the configured cap and record `estimate_scope` assumptions; do not treat a context percentage or file count as a measured execution budget.

| Signal | Action |
|--------|--------|
| Producer contract must exist before consumer | Declare `depends_on` and exact interface revision |
| Overlapping files or shared external resources | Declare ownership/resources and serialize |
| Distinct independently verifiable outcome | Ask coordinator to split at that boundary |
| One coherent outcome spans several layers | Keep the vertical slice intact |

Do not add or defer approved scope while estimating.

**Combine signals:** One task sets up for the next, separate tasks touch same file, neither meaningful alone.

## Interface-First Task Ordering

When a plan creates new interfaces consumed by subsequent tasks:

1. **Define the consumed contracts** — types, interfaces, exports and observable invariants.
2. **Deliver the thinnest end-to-end slice** against those contracts with real behavior and verification.
3. **Expand the same outcome** with error paths and required edge cases; preserve producer/consumer dependencies.

This prevents the "scavenger hunt" anti-pattern where executors explore the codebase to understand contracts. They receive the contracts in the plan itself.

## Specificity

**Test:** Could a different Claude instance execute without asking clarifying questions? If not, add specificity. See @engineer/references/planner-antipatterns.md for vague-vs-specific comparison table.

## User Setup Detection

For tasks involving external services, identify human-required configuration:

External service indicators: New SDK (`stripe`, `@sendgrid/mail`, `twilio`, `openai`), webhook handlers, OAuth integration, `process.env.SERVICE_*` patterns.

For each external service, determine:
1. **Env vars needed** — What secrets from dashboards?
2. **Account setup** — Does user need to create an account?
3. **Dashboard config** — What must be configured in external UI?

Record in `user_setup` frontmatter. Only include what Claude literally cannot do. Do NOT surface in planning output — execute-plan handles presentation.

---

## Building the Dependency Graph

**For each task, record:**
- `needs`: What must exist before this runs
- `creates`: What this produces
- `has_checkpoint`: Requires user interaction?

**Example:** A→C, B→D, C+D→E, E→F(checkpoint). Waves: {A,B} → {C,D} → {E} → {F}.

**Prefer vertical slices** (User feature: model+API+UI) over horizontal layers (all models → all APIs → all UIs). Vertical = parallel. Horizontal = sequential. Use horizontal only when shared foundation is required.

## File Ownership for Parallel Execution

Exclusive file ownership prevents conflicts:

```yaml
# Plan 01 frontmatter
files_modified: [src/models/user.ts, src/api/users.ts]

# Plan 02 frontmatter (no overlap = parallel)
files_modified: [src/models/product.ts, src/api/products.ts]
```

No overlap → can run parallel. File in multiple plans → later plan depends on earlier.

---

## Granularity Calibration

The resolved granularity is provided in the planning context as `**Granularity:** <value>`. Read that value and apply the corresponding row below. When no explicit value is present, default to Standard.

| Granularity | Typical Plans/Phase | Tasks/Plan |
|-------------|---------------------|------------|
| Coarse | 1-3 | 2-3 |
| Standard | 3-5 | 2-3 |
| Fine | 5-10 | 2-3 |

Derive plans from actual work. Granularity determines compression tolerance, not a target.

---

## Planning Complete Return Format

```markdown
## PLANNING COMPLETE

**Phase:** {phase-name}
**Plans:** {N} plan(s) in {M} wave(s)

### Wave Structure

| Wave | Plans | Autonomous |
|------|-------|------------|
| 1 | {plan-01}, {plan-02} | yes, yes |
| 2 | {plan-03} | no (has checkpoint) |

### Plans Created

| Plan | Objective | Tasks | Files |
|------|-----------|-------|-------|
| {phase}-01 | [brief] | 2 | [files] |
| {phase}-02 | [brief] | 3 | [files] |

### Next Steps

Return planning results and the first next action. Implementation requires explicit user authorization for this phase.
```

## Gap Closure Return (artifact-based — #3440)

Gap-closure output is the complete artifact set named by the correction assignment. Preserve stable gap IDs and `gap_closure: true`; include acceptance, documentation, checks argv and issue_refs. Return exact paths and revision to the coordinator; do not start execution.

**Phase:** {phase-name}
**Closing:** {N} gaps from {VERIFICATION|UAT}.md

| Plan | Gaps Addressed | Files |
|------|----------------|-------|
| {phase}-04 | [gap truths] | [files] |

**Next step:** return the bounded gap plans to the coordinator. Execution still requires explicit user authorization for the phase.

## Checkpoint Reached / Revision Complete

Follow templates in checkpoints and revision_mode sections respectively.

---

## Goal-Backward Worked Example

### Step 2: Derive Observable Truths

For "working chat interface":
- User can see existing messages
- User can type a new message
- User can send the message
- Sent message appears in the list
- Messages persist across page refresh

**Test:** Each truth verifiable by a human using the application.

### Step 3: Derive Required Artifacts

"User can see existing messages" requires:
- Message list component (renders Message[])
- Messages state (loaded from somewhere)
- API route or data source (provides messages)
- Message type definition (shapes the data)

**Test:** Each artifact = a specific file or database object.

### Step 4: Derive Required Wiring

Message list component wiring:
- Imports Message type (not using `any`)
- Receives messages prop or fetches from API
- Maps over messages to render (not hardcoded)
- Handles empty state (not just crashes)

### Step 5: Identify Key Links

"Where is this most likely to break?" Key links = critical connections where breakage causes cascading failures.

### Must-Haves Output Format

```yaml
must_haves:
  truths:
    - "User can see existing messages"
    - "User can send a message"
    - "Messages persist across refresh"
  artifacts:
    - path: "src/components/Chat.tsx"
      provides: "Message list rendering"
      min_lines: 30
    - path: "src/app/api/chat/route.ts"
      provides: "Message CRUD operations"
      exports: ["GET", "POST"]
    - path: "prisma/schema.prisma"
      provides: "Message model"
      contains: "model Message"
  key_links:
    - from: "src/components/Chat.tsx"
      to: "src/app/api/chat/route.ts"
      via: "fetch in useEffect — calls /api/chat endpoint"
      pattern: "fetch.*api/chat"
    - from: "src/app/api/chat/route.ts"
      to: "prisma/schema.prisma"
      via: "database query via prisma.message"
      pattern: "prisma\\.message\\.(find|create)"
```
