<!-- generated-by: doc-writer -->
# Coding and architecture standards

References for development and review. Read the relevant sections of the matching
documents; unrelated languages, frameworks and topics are not required reading.
These are reference documents, not skills. Project instructions and existing
project conventions retain their authority.

| Task concern | Reference | Sections to read |
|---|---|---|
| Python coding conventions | [Code style](python/code-style.md) | Prime directive; relevant numbered topic: layout 2, imports 3, comments 8, docstrings 9, naming 10, annotations 11, programming recommendations 12, anti-patterns 13, configuration 15 |
| Project and package organization | [Folder structure](python/folder-structure.md) | Layout 2; project archetype 3–7; naming 8; layer boundaries 9; module design 10 |
| Error behavior and boundaries | [Error handling](python/error-handling.md) | Hierarchy 1; transport mapping 2; raising/catching 3–4; logging 5; concurrent failures 6; response shape 7 |
| Application or library logging | [Logging](python/logging.md) | Library choice 1; configuration 2; levels 4; fields 5; request context 6; exceptions 7; sensitive data 8; slow queries 9 |
| Async jobs and event-driven code | [Async patterns](python/async-patterns.md) | Celery 1; retries 2; idempotency 3; dead letters 4; events 5; ARQ 6 |
| Performance changes | [Performance](python/performance.md) | Async I/O 1; caching 2; relationship loading 3; process memory 5 |
| Service tracing and monitoring | [Observability](python/observability.md) | Telemetry setup 1; spans 3; metrics 4; log correlation 5; RED/USE 6; instrumentation rules 7 |
| Tests and regression review | [Testing](python/testing.md) | Principles 0; categories 2; naming/AAA 3; fixtures 4–5; coverage 6–8; Django assertions 10; parametrization 11; assertion guide 12; skipping 13; cleanup 14; subtests 15; async tests 16 |
| Dependencies and package updates | [Dependency management](python/dependency-management.md) | Pinning/locks 1; audits 2; updates 3; private registries 4 |
| Security-sensitive code | [Security](python/security.md) | Secrets 1; JWT/passwords 2; validation 3; SQL parameters 4; rate limits 5; CORS 6; response sanitization 7; headers 9; review checklist 10 |
| CI quality gates | [CI/CD](python/ci-cd.md) | Pipeline stages 1; lint/type/test/build example 2; rules 3; required checks 4 |
| Container/service implementation | [Deployment](python/deployment.md) | Container layout 1–2; liveness/readiness 3; shutdown 4; 12-factor checklist 5; local configuration 6 |
| Relational models and queries | [Database design](sql/db-design.md) | Model foundation 1; naming 2; relationships 3; partial/GIN indexes 4.3; migrations 5; query loading 6.1; decimals 7 |
| Schema/data rollout | [Data migrations](sql/data-migrations.md) | Rollout rules 1; expand/contract 2; committed batch backfills 3; dangerous operations 4; Alembic 5; Django state/database separation 6 |
| REST contracts | [API design](api/design.md) | URLs 1; methods 2; status codes 3; request/success shapes 4; pagination/filtering 5–6; versioning 7; documentation 8; datetime/sensitive fields 9–10 |
| Authentication and permissions | [API authentication](api/authentication.md) | JWT lifecycle 2; OAuth2 3; RBAC 4; ABAC 5; API keys 6; service authentication 7 |
| Flask code | [Flask](api/flask.md) | Structure; factories/extensions; routes; error handlers; configuration rules; application context; hooks; MethodView; decorators; security; Celery; async views; testing |
| FastAPI code | [FastAPI](api/fastapi.md) | Structure; app factory; routes; Pydantic schemas; session generator; background tasks; health; lifespan; annotated dependencies; RORO |
| Service boundaries and integration | [Microservices](architecture/microservices.md) | Boundaries 1; communication 2; contract/versioning 3; shared libraries 4; data ownership 6 |
| Incremental feature rollout | [Feature flags](architecture/feature-flags.md) | Types 1; implementation 2; rollout 3; lifecycle 4; registry 6 |

Additional focused Python examples:

| Concern | References |
|---|---|
| Public contracts | [Type hints](python/doc-type-hints.md), [docstrings](python/doc-docstring.md) |
| Guard clauses and failures | [Early returns](python/design-early-return.md), [observable exceptions](python/error-no-silent-exceptions.md) |
| Component design | [Design principles](python/design-philosophy.md), [single responsibility](python/design-single-responsibility.md), [dependency injection](python/design-dependency-injection.md), [pure functions](python/design-pure-functions.md) |
| Interfaces and object state | [Composition](python/oop-composition-over-inheritance.md), [interface segregation](python/solid-isp.md), [substitution](python/solid-lsp.md), [dataclasses](python/oop-dataclass.md), [properties](python/oop-property.md) |
| Input trust boundaries | [Pydantic validation](python/validation-pydantic.md) |
| Async ownership | [Context managers](python/async-context-manager.md), [concurrent I/O](python/async-gather.md), [background tasks](python/async-create-task.md), [concurrency limits](python/async-semaphore.md) |
| Collection performance | [Set lookups](python/perf-set-lookup.md), [generators](python/perf-generator-expression.md), [comprehensions](python/perf-list-comprehension.md), [dictionary defaults](python/perf-dict-get.md) |

SQL coverage comes from Python/ORM sources. A general SQL style guide, query-plan
analysis, isolation-level guidance, stable database pagination and dialect-specific
performance standards still need a suitable source.

Original sections and examples are retained verbatim. Only specific faulty
passages, skill framing and redundant extracted fragments are excluded. See
[source selections](SOURCES.md), [exact retained ranges and omissions](provenance.json)
and the complete [source licenses](LICENSES.md).
