<!-- generated-by: doc-writer -->
# Architecture routing

Use the Bounded reads rules in `engineer/standards/README.md`.
IDs have the prefix `architecture.`. Select the applicable section or child.

| ID suffix / concern | Reference and section selectors |
|---|---|
| `services.boundaries` — splitting services | `engineer/standards/architecture/microservices.md` §1; When to Split or Bounded Context Heuristic |
| `services.communication` — sync vs events | `engineer/standards/architecture/microservices.md` §2; select transport and decision guidance |
| `services.contracts` — inter-service contracts | `engineer/standards/architecture/microservices.md` §3 |
| `services.libraries` — shared code ownership | `engineer/standards/architecture/microservices.md` §4 |
| `services.data` — service data ownership | `engineer/standards/architecture/microservices.md` §6 |
| `flags.types` — flag selection | `engineer/standards/architecture/feature-flags.md` §1 |
| `flags.implementation` — evaluation and usage | `engineer/standards/architecture/feature-flags.md` §2; select service, code or endpoint child |
| `flags.rollout` — gradual rollout | `engineer/standards/architecture/feature-flags.md` §3 |
| `flags.lifecycle` — expiry and cleanup | `engineer/standards/architecture/feature-flags.md` §4 |
| `flags.registry` — flag tracking | `engineer/standards/architecture/feature-flags.md` §6 |

Add `engineer/standards/api/index.md` for contracts/authentication,
`engineer/standards/sql/index.md` for schema/data changes and
`engineer/standards/python/index.md` for implementation concerns.
