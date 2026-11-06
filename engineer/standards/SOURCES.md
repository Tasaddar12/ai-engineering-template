<!-- generated-by: doc-writer -->
# Standards sources

Reference bodies are concatenations of original source fragments, without
paraphrasing or new examples. Source frontmatter and skill activation text are
excluded. Line ranges, fragment hashes and destination hashes are recorded in
[provenance.json](provenance.json). Both MIT notices are preserved in full in
[LICENSES.md](LICENSES.md), alongside the exported references.

| Source | Pinned revision | Selected material |
|---|---|---|
| [ludo-technologies/python-best-practices](https://github.com/ludo-technologies/python-best-practices/tree/fa0d3f58afb8bf56c028bb559e0e7bc1538e079a/skills/coding-standards/rules) | `fa0d3f58afb8bf56c028bb559e0e7bc1538e079a` | Python coding rules; body text only. Dependency-injection notes referencing the omitted global-singleton rule are excluded. |
| [rishapgandhi/python-skills](https://github.com/rishapgandhi/python-skills/tree/920360e791bd326d1c2495f1ff11da3272418780) | `920360e791bd326d1c2495f1ff11da3272418780` | Selected sections from the five user-supplied locations below. |

| Original path in python-skills | Selected boundaries | Destination |
|---|---|---|
| `rules/api-design.md` | Sections 1, 3, 5, 6, 8, 9, 10 | `api/design.md` |
| `skills/flask/SKILL.md` | App Factory; Extensions; Blueprint + Route; Application Context & g | `api/flask.md` |
| `skills/fastapi/SKILL.md` | Pydantic Schemas; Annotated Dependencies | `api/fastapi.md` |
| `skills/common/api-auth.md` | ABAC | `api/authorization.md` |
| `skills/common/code-style.md` | Imports; Naming 10.1–10.2; Mutable Default Arguments | `python/imports.md`, `python/naming.md`, `python/mutable-defaults.md` |
| `skills/common/logging.md` | Structured event example and event naming; sensitive-data table | `python/structured-logging.md`, `python/logging-sensitive-data.md` |
| `skills/common/observability.md` | Custom Spans; Metrics Patterns instruments; Trace Correlation; RED + USE | `python/monitoring.md` |
| `skills/common/security.md` | SQL Injection Prevention | `sql/parameterized-queries.md` |
| `skills/common/performance.md` | N+1 Query Prevention | `sql/query-loading.md` |
| `skills/common/db-design.md` | Naming; Pagination; Decimal Handling | `sql/naming.md`, `sql/pagination.md`, `sql/decimal-values.md` |
| `skills/common/data-migrations.md` | Rules for Backfills; Alembic Best Practices | `sql/migrations.md` |

## Selection exclusions

- `_sections.md`, `_template.md`, common's line-offset index, skill activation
  instructions and stack/toolchain prescriptions are not reference standards.
- Repeated common typing, docstring, concurrency and collection examples are
  represented by the selected Python rules instead.
- The blanket no-global-singleton rule is omitted; Flask extension initialization
  retains its framework-specific scope.
- The generic API response envelope and FastAPI's blanket dict prohibition are
  omitted; framework schema examples retain their original response shapes.
- Incorrect or conflicting examples are omitted rather than corrected: PATCH
  idempotency table; date-format Deprecation header; undecorated async-generator
  context-manager use; PostgreSQL UPDATE LIMIT; backfill loop without per-batch
  commits; concurrent Django index without non-atomic migration; blanket index
  rules and server-onupdate claims; blocking psutil call inside async code;
  unbounded raw-path metric labels; inconsistent pure-function Item fields;
  interpolated JSON/CSV serializers.
- Broader deployment, CI, LLM and product-specific recipes are outside this
  coding/API reference selection. The remaining SQL coverage gap is recorded in
  the [index](README.md).
