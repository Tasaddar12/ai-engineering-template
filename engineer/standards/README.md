<!-- generated-by: doc-writer -->
# Coding and architecture standards

References for development and code review. Read only the files matching the
task's language, framework and design concerns; these are not skills.

| Task concern | References |
|---|---|
| Python imports and names | [Imports](python/imports.md), [naming](python/naming.md) |
| Python public contracts | [Type hints](python/doc-type-hints.md), [docstrings](python/doc-docstring.md) |
| Python mutable defaults | [Mutable defaults](python/mutable-defaults.md), [dataclasses](python/oop-dataclass.md) |
| Python control flow and failures | [Early returns](python/design-early-return.md), [exceptions](python/error-no-silent-exceptions.md) |
| Python component design | [Design principles](python/design-philosophy.md), [single responsibility](python/design-single-responsibility.md), [dependency injection](python/design-dependency-injection.md) |
| Python interfaces | [Interface segregation](python/solid-isp.md), [substitution](python/solid-lsp.md), [properties](python/oop-property.md) |
| Untrusted Python input | [Boundary validation](python/validation-pydantic.md) |
| Async I/O and resource ownership | [Context managers](python/async-context-manager.md), [concurrent I/O](python/async-gather.md), [background tasks](python/async-create-task.md), [concurrency limits](python/async-semaphore.md) |
| Python collection performance | [Set lookups](python/perf-set-lookup.md), [generators](python/perf-generator-expression.md), [comprehensions](python/perf-list-comprehension.md), [dictionary defaults](python/perf-dict-get.md) |
| Logging and monitoring | [Structured logging](python/structured-logging.md), [sensitive data](python/logging-sensitive-data.md), [spans, metrics and trace correlation](python/monitoring.md) |
| SQL parameters and names | [Parameterized queries](sql/parameterized-queries.md), [database naming](sql/naming.md) |
| Database query performance | [Relationship loading](sql/query-loading.md), [pagination](sql/pagination.md) |
| Database values and schema changes | [Decimal values](sql/decimal-values.md), [migrations and backfills](sql/migrations.md) |
| REST API design | [URLs, status codes, pagination, documentation and sensitive fields](api/design.md) |
| API authorization | [Attribute-based access policy](api/authorization.md) |
| Flask implementation | [Factories, extensions, routes and context resources](api/flask.md) |
| FastAPI implementation | [Schemas and annotated dependencies](api/fastapi.md) |

SQL coverage is limited to the supplied Python/ORM sources. These references do
not yet provide a general SQL style guide, query-plan analysis, isolation-level
guidance or dialect-specific performance standards.

The reference bodies retain selected source text and examples verbatim. See
[sources and selection boundaries](SOURCES.md), the [fragment manifest](provenance.json)
and the complete [source licenses](LICENSES.md).
