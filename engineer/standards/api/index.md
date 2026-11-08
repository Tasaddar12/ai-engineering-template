<!-- generated-by: doc-writer -->
# API routing

Use the [bounded-read procedure](../../references/coding-standards.md#bounded-reads).
IDs have the prefix `api.`. Each row is a menu: select only matching sections or
children. A framework match does not require its whole document. Add
[Python](../python/index.md) for language rules, [SQL](../sql/index.md) for
persistence and [architecture](../architecture/index.md) for service boundaries.

| ID suffix / concern | Reference and section selectors |
|---|---|
| `rest.resources` — resource and method contracts | [Design §1](design.md#1-url-structure); methods §2 or status codes §3 |
| `rest.payloads` — request/success shapes | [Design §4](design.md#4-request--response-shape); select request, single-item or list child |
| `rest.collections` — list contracts | [Design §5](design.md#5-pagination); filtering/sorting/search §6 |
| `rest.evolution` — contract evolution | [Design §7](design.md#7-versioning) or documentation §8 |
| `rest.fields` — field representation | [Design §9](design.md#9-datetime-format) or sensitive fields §10 |
| `auth.methods` — authentication selection | [Authentication §1](authentication.md#1-authentication-methods) |
| `auth.jwt` — token lifecycle | [Authentication §2](authentication.md#2-jwt-lifecycle); select structure, refresh or revocation |
| `auth.oauth` — OAuth2 flows | [Authentication §3](authentication.md#3-oauth2-flows); select authorization-code or client-credentials child |
| `auth.permissions` — authorization | [Authentication §4](authentication.md#4-rbac-role-based-access-control) RBAC or §5 ABAC |
| `auth.keys` — API keys | [Authentication §6](authentication.md#6-api-key-management) |
| `auth.services` — service authentication | [Authentication §7](authentication.md#7-service-to-service-auth) |
| `flask.setup` — Flask initialization | [App factory](flask.md#app-factory); Stack, Project structure, Extensions or Configuration as needed |
| `flask.routes` — Flask request handling | [Blueprint + route](flask.md#blueprint--route); MethodView, View decorators or Request lifecycle & hook ordering |
| `flask.errors` — Flask error responses | [Error handling](flask.md#error-handling); select Error handlers or Custom API error classes |
| `flask.context` — Flask resource lifetime | [Application context & g](flask.md#application-context--g) |
| `flask.security` — headers and cookies | [Security headers & cookie settings](flask.md#security-headers--cookie-settings) |
| `flask.jobs` — workers and async views | [Celery integration](flask.md#celery-integration) or Async views (Flask 2.0+) |
| `flask.testing` — Flask tests | [Flask testing](flask.md#flask-testing--complete-patterns); select client/fixtures, session access, redirects/context, CLI or app-context child |
| `fastapi.setup` — FastAPI initialization | [App factory pattern](fastapi.md#app-factory-pattern); Stack or Project structure as needed |
| `fastapi.routes` — FastAPI contracts | [Router + endpoint pattern](fastapi.md#router--endpoint-pattern); Pydantic schemas or RORO in FastAPI routes |
| `fastapi.dependencies` — request dependencies | [Dependencies](fastapi.md#dependencies); select Database session or Annotated dependencies (Python 3.9+) |
| `fastapi.lifecycle` — FastAPI lifecycle | [Lifespan](fastapi.md#lifespan-context-manager-replaces-deprecated-appon_event); Health check endpoint or Background tasks |

General exception boundaries and response shape are in
[Python errors §2](../python/error-handling.md#2-where-exceptions-are-raised-and-caught)
and §7. Framework examples retain their own shapes; apply project decisions when
these differ.
