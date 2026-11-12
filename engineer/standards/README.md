<!-- generated-by: doc-writer -->
# Coding and architecture standards

Choose the domains matching the task, then select references in their indexes.
Follow the Bounded reads rules below.
These are references, not skills. Project instructions and existing project
conventions retain their authority.

| Task concern | Routing index |
|---|---|
| Python conventions, design, async code, tests, security or operations | `engineer/standards/python/index.md` |
| REST contracts, authentication, Flask or FastAPI | `engineer/standards/api/index.md` |
| Service boundaries, integration or feature rollout | `engineer/standards/architecture/index.md` |
| Relational models, queries or schema/data rollout | `engineer/standards/sql/index.md` |

Domains combine: a Python endpoint can require Python and API references; add SQL
for persistence and architecture for service boundaries or rollout. Select only
the concerns actually involved. Unrelated domains are not required reading.

Indexes assign stable descriptive routing IDs to retained documents or sections.
`engineer/standards/routing.json` is the routing source of truth:
`engineer_run query standards-read` resolves IDs from it to exact sections at read
time, and plans pin them per task in `<standards>`. The index tables are generated
from it; edit the JSON, then run `python -I engineer/bin/lib/gen_standards_routing.py --write`.
`--check` fails on stale tables or on menu text that disagrees with an entry's
`section`, `whole` or `include §N` fields. Rename an ID by adding the old name to
`aliases` so pinned plans keep resolving. The rule documents retain instructions,
examples and original heading capitalization; levels, grouping and spacing are
edited for navigation.
Attribution, source selections and editorial changes are recorded in
`engineer/standards/SOURCES.md`, `engineer/standards/provenance.json` and
`engineer/standards/LICENSES.md`; consult these for standards maintenance. SQL coverage
limits are recorded in `engineer/standards/sql/index.md` §Coverage limits.

## Bounded reads

Read the sections an index row selects, not whole documents.

| Step | Do |
|---|---|
| Pick | One routing row. Several listed sections are alternatives — take only what the task needs. |
| Locate | Find the actual heading text and level with a heading-only search or outline. Ignore headings inside code fences. |
| Read | Use offset/limit or a line range: from the heading to the next heading of equal or higher level, or EOF. Keep subsections and full examples. An anchor alone does not mark where a read ends. |
| Widen | Add the applicability notes, enclosing intro rules and prerequisites the section depends on. Widen again when the task raises new concerns. |

**Whole rules:** an entry marked **whole** is a focused rule — read all of it,
including the bad/good examples.

- **Already in context?** Reuse it; don't read it again. Merge overlapping reads.
- **Handing off?** Pass routing IDs, not copied standards. Each independent agent reads its own sections.
- **Heading missing or ambiguous?** Report a routing gap; don't fall back to reading the whole document.
- **Never** truncate instructions to save tokens. Line offsets are found at read time, not stored.
