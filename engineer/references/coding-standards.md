# Coding standards

Read before planning, implementing, fixing, investigating, verifying or reviewing code.

## Where to Read

| Task touches | Open |
|---|---|
| Python code, tests, async, security or operations | `engineer/standards/python/index.md` |
| REST contracts, authentication, Flask or FastAPI | `engineer/standards/api/index.md` |
| Service boundaries, integration or feature rollout | `engineer/standards/architecture/index.md` |
| Relational models, queries or schema/data rollout | `engineer/standards/sql/index.md` |
| Unsure | `engineer/standards/README.md` |

Domains combine — open every index the task touches. Read only the files matching
the task's language, framework and design concerns.

**How to read:** Outline the index's headings first and read only the tables the
task touches. Each row selects sections; read those only, using the Bounded reads
rules in `engineer/standards/README.md`.

## Missing or Conflicting Coverage

- **No matching row** — report the gap; do not invent a standard.
- **Conflicts with a project decision** — report the conflict; project
  instructions keep their authority.
