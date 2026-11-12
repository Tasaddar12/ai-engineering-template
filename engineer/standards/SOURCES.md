<!-- generated-by: doc-writer -->
# Standards sources

Rule instructions, examples, notes, references and severity labels are preserved.
Editorial cleanup repairs heading levels and spacing and groups related framework
sections while preserving original heading capitalization and content. Larger
source documents remain together; specialist examples remain separate. No replacement standards or
corrected examples have been invented.

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

[provenance.json](provenance.json) records original source selections separately
from edited destinations. Both complete MIT notices remain unchanged in
[LICENSES.md](LICENSES.md), inside the exported standards tree.

## Editorial provenance

Manifest schema 2 preserves each upstream repository, pinned revision, path,
selected original line range and fragment SHA256, plus all earlier omitted
ranges and reasons. These spans describe the original source selection, not
verbatim ranges in the edited destination.

- `source_selection_sha256` retains the prior curated destination hash before
  editorial cleanup; `sha256` hashes the current destination's UTF-8 Git blob.
- `editorial_basis_revision` identifies the pre-cleanup collection. Per-file
  `editorial_changes` records heading replacements/removals, new grouping
  headings, intact section moves, horizontal-rule removal and blank-line cleanup.
- Style subsections 12.11–12.15 now belong under section 12, with idiom children
  one level deeper. Flask error sections share an Error Handling parent; FastAPI
  database-session and dependency-annotation sections share Dependencies.
- Five pre-existing user edits remove decorative comment markers in the style
  examples. Their exact before/after lines and input hash are recorded as
  `retained_user_edits` and `input_sha256`; every other example remains unchanged.
- `content_sha256` hashes compact JSON of sorted `[line, count]` pairs for exact
  nonblank, non-heading, non-separator prose lines outside code fences.
  `examples_sha256` hashes compact JSON of sorted complete fenced-block strings,
  including delimiters, newlines and duplicates. Both use UTF-8,
  `ensure_ascii=false`, sorted keys and separators `(',', ':')`. These summaries
  preserve multiplicity when intact sections move; they do not replace the
  original fragment hashes. Ordered direct bodies under each mapped heading
  were also checked independently of whole-file order.

Substantive prose, lists and tables keep their order within every retained
section. Only the redundant second style title is removed; its authority and
applicability preamble remains under the main title. Retained heading text keeps
its original capitalization, identifiers, attribution and priority labels;
recorded boilerplate removal does not impose a new casing convention. Separators
and repeated blank lines outside examples carry no rule content and are removed.
Read the indexes and rules for task work; this manifest is for source maintenance.

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
