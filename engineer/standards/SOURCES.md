<!-- generated-by: doc-writer -->
# Standards sources

The documents retain original wording, headings and code examples. Larger source
documents remain together; specialist examples remain separate. No replacement
standards or corrected examples have been invented.

| Source | Pinned revision | Retained material |
|---|---|---|
| [ludo-technologies/python-best-practices](https://github.com/ludo-technologies/python-best-practices/tree/fa0d3f58afb8bf56c028bb559e0e7bc1538e079a/skills/coding-standards/rules) | `fa0d3f58afb8bf56c028bb559e0e7bc1538e079a` | Focused Python rule bodies without authoring frontmatter. |
| [rishapgandhi/python-skills](https://github.com/rishapgandhi/python-skills/tree/920360e791bd326d1c2495f1ff11da3272418780) | `920360e791bd326d1c2495f1ff11da3272418780` | The common documents and framework/design references listed below, with specific omissions recorded in the manifest. |

| Original path | Reference |
|---|---|
| `skills/common/code-style.md` | [Python code style](python/code-style.md) |
| `skills/common/folder-structure.md` | [Python project structure](python/folder-structure.md) |
| `skills/common/logging.md` | [Logging](python/logging.md) |
| `skills/common/async-patterns.md` | [Async patterns](python/async-patterns.md) |
| `skills/common/performance.md` | [Performance](python/performance.md) |
| `skills/common/observability.md` | [Observability](python/observability.md) |
| `skills/common/testing.md` | [Testing](python/testing.md) |
| `skills/common/error-handling.md` | [Error handling](python/error-handling.md) |
| `skills/common/dependency-management.md` | [Dependency management](python/dependency-management.md) |
| `skills/common/security.md` | [Security](python/security.md) |
| `skills/common/ci-cd.md` | [CI/CD](python/ci-cd.md) |
| `skills/common/deployment.md` | [Deployment](python/deployment.md) |
| `skills/common/db-design.md` | [Database design](sql/db-design.md) |
| `skills/common/data-migrations.md` | [Data migrations](sql/data-migrations.md) |
| `skills/common/api-auth.md` | [Authentication](api/authentication.md) |
| `skills/common/microservices.md` | [Microservices](architecture/microservices.md) |
| `skills/common/feature-flags.md` | [Feature flags](architecture/feature-flags.md) |
| `rules/api-design.md` | [API design](api/design.md) |
| `skills/flask/SKILL.md` | [Flask reference](api/flask.md) |
| `skills/fastapi/SKILL.md` | [FastAPI reference](api/fastapi.md) |

[provenance.json](provenance.json) records every retained original line range,
its SHA256, each complete destination SHA256, and specific omitted ranges with
their reasons. Both complete MIT notices are in [LICENSES.md](LICENSES.md), inside
the exported standards tree.

## Selection boundaries

- Common documents replace the earlier extracted imports, naming, defaults,
  logging, monitoring and SQL fragments. Their useful surrounding sections remain.
- Source skill activation/supersession text, Ludo authoring metadata and the stale
  common line-offset index are excluded. These references are not installed skills.
- Ludo's blanket no-global-singleton rule conflicts with framework extension
  initialization; its linked dependency-injection notes are excluded. Protocol/OCP
  serializer examples interpolate unescaped JSON/CSV, so those rules are excluded.
  The inaccurate universal string-concatenation claim is not added as a specialist
  rule; qualified guidance and string-building examples remain in code style.
- In the pure-functions rule, only the inconsistent local Item definition and its
  associated mutation example are omitted; transformation and orchestration
  examples remain.
- Specific faulty passages in the broad documents are omitted rather than
  rewritten: invalid or incompatible calls; misleading exception/typing/version
  claims; unsafe logging/idempotency examples; unsupported coverage pragmas;
  incorrect index/pagination/atomic-migration examples. Exact ranges and individual
  reasons are in the manifest.
- The API design error-envelope example duplicates the fuller error-handling
  document; its request and success examples remain. Framework-specific examples
  retain their original shapes.
- The authentication token-pair example lacks the `jti` required by its revocation
  pattern and can issue identical refresh tokens within one second. Its payload
  structure, rotation flow, revocation helpers and other authentication sections remain.
- `skills/common/llm-patterns.md` specializes prompt management, provider clients,
  conversation buffers and token-cost/rate accounting. It is outside this general
  Python, SQL and API/architecture standards collection.

The remaining SQL source gap is recorded in the [index](README.md).
