# TASK-037 coordination reminders

Dispatch only after actual035/036 acceptance. Read031 installer/lifecycle handoff,
034 CLI closure,005 asset closure regression history and accepted004 inventory
behavior alongside the task. Own only pyproject.toml, install.py, docs/, workflow
files, tests/package/ and your handoff. Do not edit root README/ARCHITECTURE or
unowned test parents as a shortcut. Flat src modules remain required.

The existing parent unittest discover command observes only24 bootstrap tests;
unit/e2e leaves have no package __init__.py. Final CI and the documented local
validation entry must actually run all required task leaves, restart/recovery E2E
and packaging checks with nonzero observed counts. Implement aggregate wiring
inside your owned surface; do not mistake a passing bootstrap-only run for the
complete suite. Avoid a self-recursing packaging discovery command.

Build a wheel and source distribution, then install each in clean environments
without imports or assets accidentally supplied by the checkout, PYTHONPATH or
an editable development install. Exercise the installed CLI outside the repository.
Verify the complete transitive flat module closure, exact27 schema assets and
canonical reusable guidance/defaults/templates as actually required by final
entrypoints. Test both fresh .codex and .claude initialization/adoption, default
provider aliases, safe upgrade and preservation of native/project-owned material.
Do not ship this repository's .ai plans/history, local worktrees, credentials or
provider simulation state. The asset catalog must grow with reachable source and
exclude unreachable sentinels; preserve005's independently authored fixture oracle.

Configure Linux/Windows validation and build jobs against declared supported
Python versions. Actual local Windows and Ubuntu-24.04 via WSL are available.
Use WSL --exec with its project venv; meaningful clean installation environments
must be separate from editable root imports. Distinguish local executed checks,
configured remote CI, and actual remote observed results; do not claim a GitHub
run or remote delivery without an observed authorized operation. No live provider
is needed for deterministic fake MVP tests.

Update owned reusable docs to describe final observed CLI behavior, offline/fake
adapter setup, explicit configured model bindings, saved settings on resume,
review and delivery gates, platform limits and actual commands. Keep implementation
internals out of normal user flows. Do not label unavailable production adapters
or unobserved remote merge/archival as successful. Final integrated INT review
remains a separate coordinator gate after all39 tasks are accepted.

## Minimum-version validation runtimes

Project-local Python3.11.16 with declared jsonschema4.26.0 is available on both hosts:
Windows ROOT/.ai/local/full-plan-py311-venv/Scripts/python.exe;
Linux /mnt/d/Codex Projects/ai-engineering-template/.ai/local/full-plan-linux-py311-venv/bin/python.
Use Linux through WSL Ubuntu-24.04 --exec and exact candidate cwd. Use these for
meaningful minimum-version checks or final packaging; do not repeat unrelated
suites after they pass. Existing Python3.12 environments remain the declared
coordinator test default. No remote CI execution is implied by local WSL testing.

## Explicit user gate: no ignored dependencies

The final source-checkout, wheel and sdist checks must run with no .ai/local
contents supplied. A clean clone/export has tracked sources only; create fresh
test environments separately, install declared dependencies and exercise the
complete suite plus installed CLI outside the checkout. Check that runtime
helpers, regression fixtures and reusable documentation are tracked and packaged
where required. Include the finite Git helper and actual entrypoint dependency
closure. Manual PLAN-001 coordination tools and their session records must not
be copied into the product to satisfy this gate.
