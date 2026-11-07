<!-- generated-by: doc-writer -->
# Architecture routing

Use the [bounded-read procedure](../../references/coding-standards.md#bounded-reads).
IDs have the prefix `architecture.`. Select the applicable section or child.

| ID suffix / concern | Reference and section selectors |
|---|---|
| `services.boundaries` — splitting services | [Microservices §1](microservices.md#section-1--service-boundary-rules); When to Split or Bounded Context Heuristic |
| `services.communication` — sync vs events | [Microservices §2](microservices.md#section-2--inter-service-communication); select transport and decision guidance |
| `services.contracts` — inter-service contracts | [Microservices §3](microservices.md#section-3--api-contracts) |
| `services.libraries` — shared code ownership | [Microservices §4](microservices.md#section-4--shared-libraries) |
| `services.data` — service data ownership | [Microservices §6](microservices.md#section-6--data-ownership-rules) |
| `flags.types` — flag selection | [Feature flags §1](feature-flags.md#section-1--flag-types) |
| `flags.implementation` — evaluation and usage | [Feature flags §2](feature-flags.md#section-2--implementation-pattern); select service, code or endpoint child |
| `flags.rollout` — gradual rollout | [Feature flags §3](feature-flags.md#section-3--gradual-rollout-strategy) |
| `flags.lifecycle` — expiry and cleanup | [Feature flags §4](feature-flags.md#section-4--flag-lifecycle) |
| `flags.registry` — flag tracking | [Feature flags §6](feature-flags.md#section-6--flag-hygiene-tracking) |

Add [API](../api/index.md) for contracts/authentication,
[SQL](../sql/index.md) for schema/data changes and
[Python](../python/index.md) for implementation concerns.
