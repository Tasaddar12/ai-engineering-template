# Contributing

Use Python3.11+ and install the project with `python -m pip install -e ".[dev]"`. Read `AGENTS.md` and the selected plan under `.ai` before changing code. All plans, plan-specific contracts, tasks and features stay under `.ai`.

Keep authored Python modules directly in `src`, reusable assets in their root directories, and all product subprocesses behind the central runner. Work in the assigned managed checkout without changing another worker's files or branch. Keep state and Git delivery coordinator-owned.

Normal contributions should include appropriate validation and a concise description of changed behavior. The current PLAN-003 implementation pass is an explicit exception: the user deferred test suites, compatibility probes and validation loops. Do not report deferred checks as passing. Fix clear defects while implementing and record unfinished bugs for later.

Do not package this repository's development `.ai` data, worktrees, caches, credentials or tests as reusable project assets. Do not restore obsolete history or add compatibility migrations for data the user requested deleted.
