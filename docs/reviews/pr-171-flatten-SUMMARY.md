# PR 171 manager dispatch correction

- Root: `C:/Users/killi/.codex/worktrees/pr171-runtime-comments/ai-engineering-template`
- Branch: `review-pr171-runtime`
- Input revision: `48ce2980b0b3bfec27c71bea9d1b8bfe95a9036e`
- Parent contract inspected: `5ad2f56f75be94185fea3edc5d3b232291934571:engineer/workflows/manager.md`.

Restored the parent manager's complete background plan/execute handlers alongside its inline handlers. Both retain full Skill pipelines and manager flags; background workers retain failure reporting and no-duplicate-work waiting. Compound false-mode actions dispatch all background plan/execute orchestrators before inline verification/discussion; true-mode actions finish the same pipelines inline in order.

The manager now captures and validates one `dispatch-should-flatten --raw` result during initialization. Only literal `true` and `false` are accepted. Query errors and invalid output stop initialization instead of inventing an inline default. Dashboard refreshes and action handlers reuse that captured value. Startup/dashboard labels and mirrored command/skill descriptions follow the resolved mode. Removed the constant-result justification and stale registry/host nesting claims; no retired workspace, file-output or wake scheduling routes were restored.

Validation on the completed source changes before this bookkeeping summary:

- `python -m unittest discover -s tests -p test_manager_routing.py -v`: 5 tests passed. Executes the documented Bash resolver with a runtime stub for true, false, invalid values and failing queries, checks exactly one capability call, and parses every documented Bash block with `bash -n`.
- `python -m unittest discover -s tests -p test_agent_sources.py -v`: 16 tests passed, including all command/skill mirror parity checks.
- `git diff --check`: passed.

Limitations: `engineer.py` still implements the pre-existing constant-true capability stub. It is unchanged and is not authority for removing the planned false route. Stub tests establish resolver behavior, not live host support for nested background orchestration. No runtime implementation, JSON readers, `.ai/` or `.planning/` records were changed. Earlier JSON rollback changes remain intact. No push or merge performed.

Threats: none identified within the bounded workflow routing and description changes.
