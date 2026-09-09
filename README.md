# AI Engineering Framework

AI Engineering Framework is a Python 3.11+ coordinator for explicit planning,
fixed-worktree implementation, validation, independent review, recovery and PR delivery
to `main`.

Authored Python modules live directly in `src` and install as the `ai_engineering`
namespace. Reusable project defaults have one authored source in `agents/`, `templates/`,
`workflows/`, `constraints/` and `framework.yaml`. `ai init` installs derived copies of
those assets into a project's `.ai` directory without copying framework development
history or granting implementation authority.

## Command line

```text
ai init . --name example
ai --root . status
ai --root . plan create "Add a feature" --scope src
ai --root . plan implement PLAN-001
python -m ai_engineering --help
```

Planning delivery never starts implementation. `plan implement`, `plan resume` and
`bugfix` are explicit operations and remain subject to the current plan, revision,
scope and provider authority recorded by the coordinator.

Dedicated operating contracts are installed under `.ai/workflows/`. All product
subprocesses, including Git, validation, delivery and provider bridges, pass through
the central command runner. Hard blocks are metadata on the current lifecycle phase;
there are no blocked lifecycle folders.

## Development state

Current implementation work is described only by `.ai/plans/active/PLAN-003.md` in
this repository. Validation for the consolidated implementation pass is explicitly
deferred by the user and is not represented as passing.
