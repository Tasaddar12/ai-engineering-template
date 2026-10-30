# PR 171 documentation comments

## Comment mapping

- Restored the phase ID convention reference and the execute-phase context guard's original `/pause-work` behavior.
- Restored planner review snapshot anchoring and the literal `reviewer/severity enum` wording.
- Restored the full PROJECT.md evolution review method and unconditional milestone invocation; restored the full discussion command flow and selected-area continuation; restored the explore workflow's original source-authority context.
- Replaced the submodule-specific worktree downgrade/blocking logic with mandatory worktree isolation and separate `files_modified` / `files_deleted` records.
- Regenerated the health diagnostic and repair tables with the existing generator, preserving its generated footnote.
- Restored the ship-time `ref.agent` in-context validation, `resolve-model` call and native agent dispatch protocol. No external review CLI was added.

## Validation

- `python -m lib.gen_health_docs --write` — wrote 36 diagnostic codes and 6 repair actions.
- `python -m lib.gen_health_docs --check` — passed; generated health documentation is current.
- `python -m unittest discover -s tests -p test_agent_sources.py` — 16 passed.
- `python -m unittest discover -s tests -p test_workflow_links.py` — 4 passed.
- `python -m unittest discover -s tests -p test_workflow_size_budget.py` — 43 passed, 11 skipped.
- `python -m unittest discover -s tests -p test_gen_health_docs.py` — 30 tests ran; one unexpected success because `test_shipped_health_md_already_passes_check` is still marked expected-failure. The coordinator assigned that marker to the runtime coder.
- `git diff --check` — passed.

## Notes

The PROJECT review step was recovered from `1eb6c97b` because it was absent at the requested PR base. No `.ai/` or `.planning/` records or YAML files were changed.
