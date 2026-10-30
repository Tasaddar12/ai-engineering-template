# PR 171 health-rule CI repair summary

## Scope and input

- Repository: `C:/Users/killi/.codex/worktrees/pr171-runtime-comments/ai-engineering-template`
- Branch: `review-pr171-runtime`
- Input revision: `94bd26bfcdafd02416d4aefc266538d5f723988e`
- Owned paths: `tests/test_lint_health_diagnostic_rule_table.py` and this summary.
- Assignment: repair the diagnosed stale rule-count assertion for PR 171; publication, fresh CI, and independent review remain coordinator-owned.

## Diagnosis and change

Commit `21f74234bfadf27a10eecd59f2ab7b67b7d26edb` intentionally retired W016 (`workflow.ai_integration_phase`) together with its check, repair, and documentation. The existing inventory test in `tests/test_health_diagnostic.py` expects 33 rules, and `tests/test_gen_health_docs.py` expects 33 rules plus three prechecks. The rule-table linter correctly reports 33 rules, 32 covered, and the existing W024 exemption.

Updated only the expected output counts in `RunAndCli.test_real_repo_passes` from 34/33 to 33/32. Preserved the exemption assertion, the four C0NN rules assertion, the S0NN skip assertion, and all coverage semantics. No runtime or documentation contract changed.

## Validation

Commands ran on Windows with Python bytecode disabled. Test commands used `PYTHONPATH` set to the repository's `tests` directory and `C:\Program Files\Git\cmd` prepended to `PATH`.

- `python -B -m unittest discover -s tests -p test_lint_health_diagnostic_rule_table.py -v`: 38 tests passed.
- `python -B -m unittest test_health_diagnostic test_gen_health_docs`: 163 tests passed.
- From `engineer/bin`, `python -B -m lib.lint_health_diagnostic_rule_table`: exit 0; 33 rules, 32 covered, one W024 exemption; four C0NN rules covered; S0NN skipped because `state_validate.py` is absent.
- `git diff --check`: passed.

## Deviations, remaining work, and security

No deviations or additional fixes. No security threats identified in the inspected assertion-only scope. Full CI and independent review are pending coordinator execution; the focused results do not claim full-suite verification. No shared planning records changed.
