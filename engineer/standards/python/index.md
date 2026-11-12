<!-- generated-by: doc-writer -->
# Python routing

Use the Bounded reads rules in `engineer/standards/README.md`.
IDs below have the prefix `python.`; `errors.chaining` means
`python.errors.chaining`. Numbers select existing headings, not lines. Each row
is a menu: read only the matching section or child. Prefer focused **whole** rules
for their specific concern; expand into broad references for version, framework
or boundary details. Do not automatically read overlapping references twice.

## Style and contracts

Every `style.*` row includes `engineer/standards/python/code-style.md` §PRIME DIRECTIVE.

| ID suffix / concern | Reference and section selectors |
|---|---|
| `style.layout` — layout and whitespace | `engineer/standards/python/code-style.md` §2; quotes §5, whitespace §6 or commas §7 |
| `style.imports` — import ordering and paths | `engineer/standards/python/code-style.md` §3; module dunders §4 |
| `style.comments` — comments and TODOs | `engineer/standards/python/code-style.md` §8 |
| `style.docstrings` — detailed formats | `engineer/standards/python/code-style.md` §9; select docstring kind |
| `style.naming` — naming and visibility | `engineer/standards/python/code-style.md` §10 |
| `style.annotations` — version-sensitive typing | `engineer/standards/python/code-style.md` §11; compatibility §11.1, version strategy §11.2, patterns §11.3 or Any §11.4 |
| `style.expressions` — language expressions | `engineer/standards/python/code-style.md` §12.1; booleans §12.2, returns §12.3, strings §12.6, lambda §12.7, comparisons §12.8 or finally §12.9 |
| `style.exceptions` — exception syntax | `engineer/standards/python/code-style.md` §12.4; context managers §12.5 |
| `style.defaults` — mutable defaults | `engineer/standards/python/code-style.md` §12.10 |
| `style.closures` — loop-variable capture | `engineer/standards/python/code-style.md` §12.11 |
| `style.idioms` — unpacking and collections | `engineer/standards/python/code-style.md` §12.12; select named child |
| `style.arguments` — argument design | `engineer/standards/python/code-style.md` §12.13 |
| `style.purity` — side effects | `engineer/standards/python/code-style.md` §12.14 |
| `style.variable-types` — stable variable meaning | `engineer/standards/python/code-style.md` §12.15 |
| `style.antipatterns` — production pitfalls | `engineer/standards/python/code-style.md` §13.1; broad catches §13.2, global state §13.3, type checks §13.4, formatting §13.5 or suppression §13.6 |
| `style.tooling` — tools and compatibility | `engineer/standards/python/code-style.md` §1; version matrix §14, pyproject §15.1 or pre-commit §15.2 |
| `contracts.types` — public annotations | `engineer/standards/python/doc-type-hints.md`, **whole** |
| `contracts.docstrings` — public documentation | `engineer/standards/python/doc-docstring.md`, **whole** |

## Components and data

| ID suffix / concern | Reference and section selectors |
|---|---|
| `structure.layout` — package/application layout | `engineer/standards/python/folder-structure.md` §2; choose archetype §3 web, §4 library, §5 ETL, §6 CLI or §7 ML |
| `structure.boundaries` — module/layer ownership | `engineer/standards/python/folder-structure.md` §9; naming §8 or module design §10; include core principle §1 |
| `design.principles` — DRY, YAGNI and KISS | `engineer/standards/python/design-philosophy.md`, **whole** |
| `design.responsibility` — cohesive components | `engineer/standards/python/design-single-responsibility.md`, **whole** |
| `design.injection` — explicit dependencies | `engineer/standards/python/design-dependency-injection.md`, **whole** |
| `design.purity` — transformations | `engineer/standards/python/design-pure-functions.md`, **whole** |
| `design.guards` — guard clauses | `engineer/standards/python/design-early-return.md`, **whole** |
| `objects.composition` — inheritance alternatives | `engineer/standards/python/oop-composition-over-inheritance.md`, **whole** |
| `objects.interfaces` — consumer interfaces | `engineer/standards/python/solid-isp.md`, **whole** |
| `objects.substitution` — substitutability | `engineer/standards/python/solid-lsp.md`, **whole** |
| `objects.dataclasses` — data containers | `engineer/standards/python/oop-dataclass.md`, **whole** |
| `objects.properties` — computed attributes | `engineer/standards/python/oop-property.md`, **whole** |
| `validation.boundaries` — external input | `engineer/standards/python/validation-pydantic.md`, **whole** |

## Errors, concurrency and performance

| ID suffix / concern | Reference and section selectors |
|---|---|
| `errors.hierarchy` — domain exceptions | `engineer/standards/python/error-handling.md` §1 |
| `errors.boundaries` — catching and HTTP mapping | `engineer/standards/python/error-handling.md` §2; response shape §7 |
| `errors.chaining` — preserve exception context | `engineer/standards/python/error-handling.md` §3.1 |
| `errors.catching` — catch selection and scope | `engineer/standards/python/error-handling.md` §4.1; minimal try §4.2 or OS errors §4.4 |
| `errors.groups` — concurrent failures, Python 3.11+ | `engineer/standards/python/error-handling.md` §6 |
| `errors.observable` — swallowed failures | `engineer/standards/python/error-no-silent-exceptions.md`, **whole**; errors §5 for logging integration |
| `async.resources` — async cleanup | `engineer/standards/python/async-context-manager.md`, **whole** |
| `async.gather` — independent concurrent I/O | `engineer/standards/python/async-gather.md`, **whole** |
| `async.tasks` — task ownership and failures | `engineer/standards/python/async-create-task.md`, **whole** |
| `async.limits` — bounded concurrency | `engineer/standards/python/async-semaphore.md`, **whole** |
| `jobs.delivery` — queues and events | `engineer/standards/python/async-patterns.md` §1; retries §2, idempotency §3, DLQ §4, events §5 or ARQ §6; include rules §7 |
| `performance.services` — service performance | `engineer/standards/python/performance.md` §1; caching §2, N+1 §3 or monitoring §5 |
| `performance.membership` — repeated lookups | `engineer/standards/python/perf-set-lookup.md`, **whole** |
| `performance.generators` — large iterations | `engineer/standards/python/perf-generator-expression.md`, **whole** |
| `performance.comprehensions` — collections | `engineer/standards/python/perf-list-comprehension.md`, **whole** |
| `performance.defaults` — dictionary defaults | `engineer/standards/python/perf-dict-get.md`, **whole** |

## Tests and operations

| ID suffix / concern | Reference and section selectors |
|---|---|
| `testing.design` — test scope and cases | `engineer/standards/python/testing.md` §0; categories §2, naming/AAA §3 or required cases §6 |
| `testing.fixtures` — isolation and cleanup | `engineer/standards/python/testing.md` §4; factories §5, mocking §7 or lifecycle §14 |
| `testing.assertions` — assertion selection | `engineer/standards/python/testing.md` §12; select assertion family; Django §10 |
| `testing.execution` — tooling and variants | `engineer/standards/python/testing.md` §1; coverage §8, parametrization §11, skips §13, subtests §15 or async §16 |
| `logging.application` — logging behavior | `engineer/standards/python/logging.md` §1; configuration §2, logger §3, levels §4, fields §5, context §6, exceptions §7, sensitive data §8 or slow queries §9 |
| `observability.services` — tracing and metrics | `engineer/standards/python/observability.md` §1; spans §3, metrics §4, correlation §5 or RED/USE §6; include rules §7 |
| `security.boundaries` — secrets and user data | `engineer/standards/python/security.md` §1; authentication §2, validation §3, SQL parameters §4, rate limits §5, CORS §6, sanitization §7, headers §9 or review checklist §10 |
| `dependencies.lifecycle` — dependency changes | `engineer/standards/python/dependency-management.md` §1; audits §2, updates §3 or registry §4; include rules §5 |
| `ci.quality` — pipeline quality gates | `engineer/standards/python/ci-cd.md` §1; template §2, rules §3 or required checks §4 |
| `deployment.services` — service lifecycle | `engineer/standards/python/deployment.md` §1; ignore file §2, health §3, shutdown §4, 12-factor §5 or configuration §6; include rules §7 |

Add `engineer/standards/api/index.md` for contracts/frameworks,
`engineer/standards/sql/index.md` for persistence and
`engineer/standards/architecture/index.md` for service/rollout decisions.
