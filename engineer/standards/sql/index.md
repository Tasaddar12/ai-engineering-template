<!-- generated-by: doc-writer -->
# SQL routing

Use the [bounded-read procedure](../../references/coding-standards.md#bounded-reads).
IDs have the prefix `sql.`. Each row is a menu of applicable sections or children.
Add [Python](../python/index.md) for language rules and
[architecture](../architecture/index.md) for service data ownership.

| ID suffix / concern | Reference and section selectors |
|---|---|
| `models.foundation` — ORM model design | [Database §1](db-design.md#section-1--model-foundation); naming §2 or relationships §3 |
| `models.indexes` — partial/GIN indexes | [Database §4.3](db-design.md#43-advanced-indexing) |
| `models.migrations` — migration discipline | [Database §5](db-design.md#section-5--migration-discipline-alembic) |
| `queries.loading` — relationship loading | [Database §6.1](db-design.md#61-avoid-n1-queries--always) |
| `values.money` — decimal values | [Database §7](db-design.md#section-7--decimal-handling-for-monetary-values) |
| `migrations.rollout` — safe schema rollout | [Migrations §1](data-migrations.md#section-1--zero-downtime-migration-rules); expand/contract §2 |
| `migrations.backfills` — committed batch backfills | [Migrations §3](data-migrations.md#section-3--backfill-strategies) |
| `migrations.hazards` — dangerous operations | [Migrations §4](data-migrations.md#section-4--dangerous-operations-reference) |
| `migrations.alembic` — Alembic changes | [Migrations §5](data-migrations.md#section-5--alembic-best-practices) |
| `migrations.django` — state/database separation | [Migrations §6](data-migrations.md#section-6--django-migrations-specifics) |

## Coverage limits

Coverage comes from Python/ORM sources. General SQL style, query-plan analysis,
isolation levels, stable database pagination and dialect-specific performance
standards still need a suitable source. Report these gaps when applicable;
do not infer standards from missing coverage.
