<!-- generated-by: doc-writer -->
# Coding and architecture standards

Choose the domains matching the task, then select references in their indexes.
Follow the [bounded-read procedure](../references/coding-standards.md#bounded-reads).
These are references, not skills. Project instructions and existing project
conventions retain their authority.

| Task concern | Routing index |
|---|---|
| Python conventions, design, async code, tests, security or operations | [Python](python/index.md) |
| REST contracts, authentication, Flask or FastAPI | [API](api/index.md) |
| Service boundaries, integration or feature rollout | [Architecture](architecture/index.md) |
| Relational models, queries or schema/data rollout | [SQL](sql/index.md) |

Domains combine: a Python endpoint can require Python and API references; add SQL
for persistence and architecture for service boundaries or rollout. Select only
the concerns actually involved. Unrelated domains are not required reading.

Indexes assign stable descriptive routing IDs to retained documents or sections;
the IDs are reading aliases, not commands. Original rule wording and examples
remain in their source documents. Attribution and omissions are recorded in
[source selections](SOURCES.md), [provenance](provenance.json) and
[licenses](LICENSES.md); consult these for standards maintenance. SQL coverage
limits are recorded in the [SQL index](sql/index.md#coverage-limits).
