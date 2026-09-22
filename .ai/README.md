# Engineering workflow

Start at [RULES](RULES.md), [PROJECT](../.planning/PROJECT.md) and
[STATE](../.planning/STATE.md), then load the selected
[command](commands/README.md) and [role](agents/README.md). These are the
project's installed engineering tools and guidance. Preserve existing project
context; onboarding fills only what is missing from evidence and user intent.

Run [onboard](commands/onboard.md) for a new or newly adopting project, then
[new-milestone](commands/new-milestone.md) to open each later cycle of work.

## Layering

```
command (commands/) ── the entry point; names a workflow, changes nothing
  └─ workflow (workflows/) ── the procedure: what to load, whom to spawn,
                               what to ask, which runtime verbs to call
       ├─ runtime (runtime/phase.py) ── every planning-record read and write
       └─ agent (agents/) ── a bounded role, spawned with its own context
```

A workflow orchestrates; a runtime verb mutates. Phase numbering, the roadmap,
STATE.md's derived counters, todos, quick tasks and milestones belong to the
runtime — a workflow that edits them by hand drifts from it.

| Area | Responsibility |
|---|---|
| [PROJECT](../.planning/PROJECT.md) | Human purpose and boundaries |
| [REQUIREMENTS](../.planning/REQUIREMENTS.md) | Desired outcomes |
| [ROADMAP](../.planning/ROADMAP.md) | Phase ordering, plan checklists and milestones |
| [STATE](../.planning/STATE.md) | Derived current summary |
| [phases](../.planning/phases/README.md) | Decisions, plans and evidence per phase |
| [codebase](../.planning/codebase/README.md) | Useful maps of existing implementation |
| `.planning/specs/` | Current verified behavioral contracts |
| `.planning/decisions/` | Significant architectural rationale |
| `.planning/todos/` | Captured ideas awaiting a home |
| `.planning/quick/` | Small changes tracked outside the roadmap |
| [commands](commands/README.md) | Entry points, mirrored by `.agents/skills/` |
| [workflows](workflows/) | The procedures those commands run |
| [agents](agents/README.md) | Responsibilities and handoffs |
| `references/` | Artifact and handoff details loaded on demand |
| [templates](templates/README.md) | Complete artifact instructions and examples |
| [runtime](runtime/README.md) | The verb interface every workflow calls |
| [config](../.planning/config.yaml) | Commit behavior, model overrides and project checks |
| [truth-map](truth-map.md) | Each fact's authoritative owner |

A phase's CONTEXT owns acceptance and decisions. PLAN and SUMMARY pairs keep plan
inputs and results bounded. Independent VERIFICATION establishes completion; an
open PR is publication, not merged delivery.

See [the workflow guide](guides/PHASE-WORKFLOW.md) for the full procedure.
