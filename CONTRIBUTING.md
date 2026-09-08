# Contributing

Use Python 3.11 or later. Install the editable package and development tools with `python -m pip install -e ".[dev]"` once the package implementation is available.

Read `AGENTS.md`, `.ai/STATE.yaml`, the selected PLAN document, its feature and included tasks. All plans, plan-specific contracts, features and tasks MUST remain under `.ai/`. Generic product documentation links to those artifacts.

Keep public Python boundaries typed. Use `ruff format`, `ruff check`, `mypy` and focused `pytest` tests. Test meaningful behavior and regression cases in temporary repositories. Use argument lists and the central command runner for subprocesses; no core Bash scripts or independent workflow subprocess calls.

Work in the feature's managed worktree and declared scope. Record real validation and a completion handoff, then obtain one independent Critical Change Review. Fix findings in the same implementation session and rerun validation and full-diff review. Structural problems return through recovery and decomposition.

Keep templates in the package asset catalog; installed `.ai/templates/` copies are project-editable. Keep model configuration independent of role behavior. Do not include this repository's `.ai/` development history in a wheel or a new project installation.
