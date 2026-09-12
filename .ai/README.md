# Engineering workflow

Start at [RULES](RULES.md), [PROJECT](PROJECT.md) and [STATE](STATE.md), then
load the selected [command](commands/README.md) and [role](agents/README.md).
This is a reusable template; onboarding supplies the adopting project's identity.

| Area | Responsibility |
|---|---|
| [PROJECT](PROJECT.md) | Human purpose and boundaries |
| [REQUIREMENTS](REQUIREMENTS.md) | Desired outcomes |
| [ROADMAP](ROADMAP.md) | Phase ordering and navigation |
| [STATE](STATE.md) | Derived current summary |
| [phases](phases/README.md) | Decisions, assignments and evidence per capability/change |
| [codebase](codebase/README.md) | Useful maps of existing implementation |
| `specs/` | Current verified behavioral contracts |
| `decisions/` | Significant architectural rationale |
| [commands](commands/README.md) | Procedures from intake through publication |
| [agents](agents/README.md) | Responsibilities and handoffs |
| [skills](../docs/AGENT-SKILLS.md) | Reusable engineering methods selected per assignment |
| `references/` | Artifact and handoff details loaded on demand |
| [templates](templates/README.md) | Artifact shapes |
| [runtime](runtime/README.md) | Executable phase coordination |
| [config](config.yaml) | Actual worker routes, capacity and checks |
| [truth-map](truth-map.md) | Each fact's authoritative owner |

A phase's CONTEXT owns acceptance and decisions. IMPLEMENT/SUMMARY pairs keep
component inputs and results bounded. Independent VERIFICATION and applicable
UAT establish completion; an open PR is publication, not merged delivery.

See [the workflow guide](../docs/PHASE-WORKFLOW.md). Historical records describe
their original revisions and do not define a second active workflow.
