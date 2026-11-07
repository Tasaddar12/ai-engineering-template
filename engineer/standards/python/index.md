<!-- generated-by: doc-writer -->
# Python routing

Use the [bounded-read procedure](../../references/coding-standards.md#bounded-reads).
IDs below have the prefix `python.`; `errors.chaining` means
`python.errors.chaining`. Numbers select existing headings, not lines. Each row
is a menu: read only the matching section or child. Prefer focused **whole** rules
for their specific concern; expand into broad references for version, framework
or boundary details. Do not automatically read overlapping references twice.

## Style and contracts

For style decisions, also read [rule precedence](code-style.md#prime-directive).

| ID suffix / concern | Reference and section selectors |
|---|---|
| `style.layout` — layout and whitespace | [Style §2](code-style.md#2-code-layout); quotes §5, whitespace §6 or commas §7 |
| `style.imports` — import ordering and paths | [Style §3](code-style.md#3-imports); module dunders §4 |
| `style.comments` — comments and TODOs | [Style §8](code-style.md#8-comments) |
| `style.docstrings` — detailed formats | [Style §9](code-style.md#9-docstrings-pep-257); select docstring kind |
| `style.naming` — naming and visibility | [Style §10](code-style.md#10-naming-conventions) |
| `style.annotations` — version-sensitive typing | [Style §11](code-style.md#11-type-annotations); compatibility §11.1, version strategy §11.2, patterns §11.3 or Any §11.4 |
| `style.expressions` — language expressions | [Style §12.1](code-style.md#121-singleton-comparisons); booleans §12.2, returns §12.3, strings §12.6, lambda §12.7, comparisons §12.8 or finally §12.9 |
| `style.exceptions` — exception syntax | [Style §12.4](code-style.md#124-exception-handling--complete-reference); context managers §12.5 |
| `style.defaults` — mutable defaults | [Style §12.10](code-style.md#1210-mutable-default-arguments) |
| `style.closures` — loop-variable capture | [Style §12.11](code-style.md#1211-late-binding-closures) |
| `style.idioms` — unpacking and collections | [Style §12.12](code-style.md#1212-python-idioms-reference); select named child |
| `style.arguments` — argument design | [Style §12.13](code-style.md#1213-function-arguments--design-rules) |
| `style.purity` — side effects | [Style §12.14](code-style.md#1214-pure-functions--minimising-side-effects) |
| `style.variable-types` — stable variable meaning | [Style §12.15](code-style.md#1215-variable-naming-under-dynamic-typing) |
| `style.antipatterns` — production pitfalls | [Style §13.1](code-style.md#131-silent-exception-swallowing); broad catches §13.2, global state §13.3, type checks §13.4, formatting §13.5 or suppression §13.6 |
| `style.tooling` — tools and compatibility | [Style §1](code-style.md#1-toolchain); version matrix §14, pyproject §15.1 or pre-commit §15.2 |
| `contracts.types` — public annotations | [Type hints](doc-type-hints.md), **whole** |
| `contracts.docstrings` — public documentation | [Docstrings](doc-docstring.md), **whole** |

## Components and data

| ID suffix / concern | Reference and section selectors |
|---|---|
| `structure.layout` — package/application layout | [Structure §2](folder-structure.md#section-2--src-layout-vs-flat-layout); choose archetype §3 web, §4 library, §5 ETL, §6 CLI or §7 ML |
| `structure.boundaries` — module/layer ownership | [Structure §9](folder-structure.md#section-9--what-never-goes-where); naming §8 or module design §10; include core principle §1 |
| `design.principles` — DRY, YAGNI and KISS | [Design philosophy](design-philosophy.md), **whole** |
| `design.responsibility` — cohesive components | [Single responsibility](design-single-responsibility.md), **whole** |
| `design.injection` — explicit dependencies | [Dependency injection](design-dependency-injection.md), **whole** |
| `design.purity` — transformations | [Pure functions](design-pure-functions.md), **whole** |
| `design.guards` — guard clauses | [Early returns](design-early-return.md), **whole** |
| `objects.composition` — inheritance alternatives | [Composition](oop-composition-over-inheritance.md), **whole** |
| `objects.interfaces` — consumer interfaces | [Interface segregation](solid-isp.md), **whole** |
| `objects.substitution` — substitutability | [Substitution](solid-lsp.md), **whole** |
| `objects.dataclasses` — data containers | [Dataclasses](oop-dataclass.md), **whole** |
| `objects.properties` — computed attributes | [Properties](oop-property.md), **whole** |
| `validation.boundaries` — external input | [Pydantic validation](validation-pydantic.md), **whole** |

## Errors, concurrency and performance

| ID suffix / concern | Reference and section selectors |
|---|---|
| `errors.hierarchy` — domain exceptions | [Errors §1](error-handling.md#section-1--exception-hierarchy-design) |
| `errors.boundaries` — catching and HTTP mapping | [Errors §2](error-handling.md#section-2--where-exceptions-are-raised-and-caught); response shape §7 |
| `errors.chaining` — preserve exception context | [Errors §3.1](error-handling.md#31-exception-chaining--always-preserve-context) |
| `errors.catching` — catch selection and scope | [Errors §4.1](error-handling.md#41-always-catch-the-most-specific-exception); minimal try §4.2 or OS errors §4.4 |
| `errors.groups` — concurrent failures, Python 3.11+ | [Errors §6](error-handling.md#section-6--python-311-exception-groups) |
| `errors.observable` — swallowed failures | [Observable exceptions](error-no-silent-exceptions.md), **whole**; errors §5 for logging integration |
| `async.resources` — async cleanup | [Context managers](async-context-manager.md), **whole** |
| `async.gather` — independent concurrent I/O | [Gather](async-gather.md), **whole** |
| `async.tasks` — task ownership and failures | [Background tasks](async-create-task.md), **whole** |
| `async.limits` — bounded concurrency | [Semaphores](async-semaphore.md), **whole** |
| `jobs.delivery` — queues and events | [Async patterns §1](async-patterns.md#section-1--task-queue-celery); retries §2, idempotency §3, DLQ §4, events §5 or ARQ §6; include rules §7 |
| `performance.services` — service performance | [Performance §1](performance.md#section-1--async-programming); caching §2, N+1 §3 or monitoring §5 |
| `performance.membership` — repeated lookups | [Set lookup](perf-set-lookup.md), **whole** |
| `performance.generators` — large iterations | [Generators](perf-generator-expression.md), **whole** |
| `performance.comprehensions` — collections | [Comprehensions](perf-list-comprehension.md), **whole** |
| `performance.defaults` — dictionary defaults | [Dictionary access](perf-dict-get.md), **whole** |

## Tests and operations

| ID suffix / concern | Reference and section selectors |
|---|---|
| `testing.design` — test scope and cases | [Testing §0](testing.md#section-0--testing-principles-the-hitchhikers-rules); categories §2, naming/AAA §3 or required cases §6 |
| `testing.fixtures` — isolation and cleanup | [Testing §4](testing.md#section-4--fixtures-and-conftest); factories §5, mocking §7 or lifecycle §14 |
| `testing.assertions` — assertion selection | [Testing §12](testing.md#section-12--assert-method-selection-guide); select assertion family; Django §10 |
| `testing.execution` — tooling and variants | [Testing §1](testing.md#section-1--toolchain); coverage §8, parametrization §11, skips §13, subtests §15 or async §16 |
| `logging.application` — logging behavior | [Logging §1](logging.md#section-1--library-choice-and-rationale); configuration §2, logger §3, levels §4, fields §5, context §6, exceptions §7, sensitive data §8 or slow queries §9 |
| `observability.services` — tracing and metrics | [Observability §1](observability.md#section-1--opentelemetry-setup); spans §3, metrics §4, correlation §5 or RED/USE §6; include rules §7 |
| `security.boundaries` — secrets and user data | [Security §1](security.md#section-1--secrets-management); authentication §2, validation §3, SQL parameters §4, rate limits §5, CORS §6, sanitization §7, headers §9 or review checklist §10 |
| `dependencies.lifecycle` — dependency changes | [Dependencies §1](dependency-management.md#section-1--pinning-strategy); audits §2, updates §3 or registry §4; include rules §5 |
| `ci.quality` — pipeline quality gates | [CI/CD §1](ci-cd.md#section-1--pipeline-stages); template §2, rules §3 or required checks §4 |
| `deployment.services` — service lifecycle | [Deployment §1](deployment.md#section-1--dockerfile-multi-stage); ignore file §2, health §3, shutdown §4, 12-factor §5 or configuration §6; include rules §7 |

Add [API](../api/index.md) for contracts/frameworks,
[SQL](../sql/index.md) for persistence and
[architecture](../architecture/index.md) for service/rollout decisions.
