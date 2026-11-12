# Coding standards

Read before planning, implementing, fixing, investigating, verifying or reviewing code.

## Load Standards

| Situation | Run |
|---|---|
| Your task has a `<standards>` field | `engineer_run query standards-read <ids> --raw` |
| Reviewing, fixing or verifying planned work | `engineer_run query standards-read --plan <PLAN.md> --raw` |
| No pinned IDs (`no-pinned-standards`, planning, quick or debug work) | `engineer_run query standards-list <domain> --raw`, pick IDs, then `standards-read` |
| Runtime unavailable | Route by hand using Where to Read below |

Quote an ID with a heading selector: `standards-read "python.errors.hierarchy@Exception chaining"`.

`standards-read` returns only the selected sections with their required context.
Do not also open the index or the full document for the same IDs.

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
