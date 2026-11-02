<!-- generated-by: doc-writer -->
# Contributing

Read [AGENTS.md](AGENTS.md) before editing. Work on a branch in an isolated
checkout. Preserve full methods, examples, template instructions and user-edited
content unless the assignment calls for changing them.

Use Python 3.11 or newer and Git. Current runtime and source tools use only the
standard library; use `python -I` for repository script entry points. A POSIX shell
is needed to exercise shell examples and `engineer_run`; on Windows, use Git Bash
rather than a WSL launcher with no configured distribution.

## Checks

Run the checks relevant to the change and report actual outcomes against a named
revision. The complete current Python suite is:

```sh
python -m unittest discover -s tests -v
```

Static source checks include:

```sh
python -I scripts/check_markdown_python.py
python -I scripts/links.py
python -I scripts/verbs.py --fail-on-unknown
```

These checks answer different questions: retired runtime-helper references,
source navigation and literal runtime query registration. A static pass does not
replace an execution check. `scripts/check.py` runs selected historical overhaul
plan checks; choose the applicable phase rather than interpreting the entire
historical plan as completed work.

Installer changes need disposable Git fixtures using the current `bin/` entry
points, including a fresh install, rerun, update/customization preservation and
the affected failure or recovery behavior. Runtime changes need real subprocess
and Git behavior where applicable. Keep test targets, temporary outputs and
processes separate from ongoing user services and benchmarks.

## Delivery

Stage only owned paths, inspect the diff and commit each completed meaningful
slice with its check evidence. Push when delivery is authorized and keep the
existing draft PR current. Use the
[Git workflow](engineer/references/git-workflow.md) and its publication templates.
Independent review, current verification and required remote checks precede
readiness; the user's specific merge authorization and repository protections
govern the merge.
