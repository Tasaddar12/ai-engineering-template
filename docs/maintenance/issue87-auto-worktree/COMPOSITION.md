---
phase: maintenance-issue87-auto-worktree
status: source_composition_verified_live_unverified
production_input: 21488caa19e3b76b11d84165bf4c69fb58f3ac96
composition: a9e3145d2b657f23a3c2e9e3a1eb1a88ec4d7d66
---

# Final seven-PR composition evidence

The evidence-only runtime-created checkout
`issue87-native-composition-final-204725284` composes PR97 with the original six
frozen drafts. It was not published or imported into PR97. No original draft was
rewritten, merged or marked complete.

## Inputs and provenance

| Input | Exact revision |
|---|---|
| Original-six integration | e464c73dd0ae8dc0a139faee0144917b04029ead |
| Native/planning source reviewed before fixture correction | 9f762c305572004e76f44f8572566b02bc04b234 |
| Initial clean automatic composition | 9d14d2234290ab6a1623c5a8bab28393124b2f42 |
| Reviewed corrected production input | 21488caa19e3b76b11d84165bf4c69fb58f3ac96 |
| Final clean automatic composition | a9e3145d2b657f23a3c2e9e3a1eb1a88ec4d7d66 |
| PR88 | 4bafcd6ca0f477f872243aed610e54389deb7474 |
| PR89 | d48d10d9fa9fb33dc05ad8552329aceee4e7d5cc |
| PR91 | 560cf1cf6e986075a63b775b567921e0e5074f68 |
| PR92 | d8f2c8bd0c4dca0f82a7fc8a95e4f0abb8bcd2b6 |
| PR93 | 47593a3d3f71739bd146a6c2c3590798d7c73c2e |
| PR94 | 135b824b0155ab3c25306ca594b137f9c76743fa |

Initial composition has native9f and original-six e464 as its two parents.
Final composition has initial9d14 and corrected production21488ca as parents.
Both merges were automatic and clean: no manually resolved source conflicts.
The earlier prototype9060 RED is historical and is not claimed as final GREEN.

## Executed checks

Exact executable: Windows Python3.13.14 with PyYAML6.0.3:
`C:/Users/killi/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe`.
Each command below is `EXE -m unittest discover -s tests -p FILE -v`, run from
initial9d14 with independent disposable offline fixtures. Exit0 for every row.

| FILE | Cases / seconds | Skips and outcome |
|---|---|---|
| test_same_agent_worktree.py | 13 /134.043 | none; installed denial/native/planning/new-existing ordinary session controls pass; host is explicitly SIMULATED |
| test_install.py | 42 /491.768 | 1 unavailable Windows symlink privilege; actual both-host hook union/planning/verb controls pass |
| test_install_update.py | 66 /483.832 | 4:two Windows symlink cases and two Claude instances of Codex-only settings checks; native plus original updater/line-ending integration passes |
| test_session_delivery.py | 60 /99.360 | none; existing ownership/base/selection/delivery controls pass |

After all four checks and independent source inspection joined, the corrected
production input was merged into the evidence checkout. The entire delta has
only `tests/test_install_migration.py` and four native maintenance records.
`git diff --exit-code 9d14d2234290ab6a1623c5a8bab28393124b2f42 a9e3145d2b657f23a3c2e9e3a1eb1a88ec4d7d66 -- .ai .agents AGENTS.md .gitattributes .planning .github tests/test_install.py tests/test_install_update.py tests/test_session_delivery.py tests/test_same_agent_worktree.py`
passed. The unchanged `.ai` tree is9ba7e03aa4108d7fa978ebfe998b23fc4c14873a.
The four suite receipts therefore retain their exact source-input boundary;
they were not retagged as new executions or needlessly rerun.

The affected migration method was executed on finalC:
`EXE -m unittest discover -s tests -p test_install_migration.py -k test_existing_managed_hooks_relocate_without_duplicate_registration -v`:
1 test/3.525s, exit0, no skips. Full migration18 passed in the isolated correction;
root also independently checked the method at productiona502 (1/3.904s).

Task4 planning47 and phase-runtime162 GREEN remain source-slice receipts in
[STACK-SUMMARY](STACK-SUMMARY.md), not invented finalC full-suite runs. The phase
wrapper and planning implementation/test bytes are unchanged by composition;
the native/installer checks above exercise their joined installed boundary.
Original-six758 Python/351 Bash evidence remains scoped to its earlier source;
no full original-six suite or benchmark was repeated here.

## Independent integration review

Repository integration-checker (`gpt-6-luna/medium`) inspected initial9d14,
then independently reconciled finala9e3145 and its exact five-path delta. It ran
no tests, changed no files and created no children. Both captured revisions were
clean. No additional broken interface was found. The known migration fixture
finding is corrected; [REVIEW-04](REVIEW-04.md) closes it with zero findings.

The review traced native denial/request/begin/callback/confirm and six workflow
consumers; exact native-adapter versus ordinary planning warning paths; grouped
hooks/platform launchers; destructive refusal versus advisory behavior; cleanup
approval/revalidation/readback; raw updater fingerprints/line endings; guard
regression-test workflow; parallel status/risk/provider audit consumers. Original
GitHub/GitLab boundaries and work73/74 remain separate. The final test-only delta
preserves these source interfaces, so the initial bounded wiring review applies.

## Preservation and remaining limits

- Against main77b5668, `.planning`, advisory `worktree-guard.sh`, delivery.py and
  `.github/workflows` have empty diffs. Attributes equal original-six e464,
  including PR88's intended nginx LF additions; they are not asserted equal main.
- Production97 contains frozen93/92 ancestry and its own native/join delta only.
  Original-six e464 and finalC were never merged into production97.
- All draft PRs and issues remain open; no PR merge, real cleanup, infrastructure
  change, host installation or Whiskance/game checkout write occurred.
- Installed hooks and Git are real; same-host actor/default context in fixtures
  is SIMULATED. Actual eligible-Claude native movement, permissions/context,
  later-turn defaults and lifecycle accounting still need live evidence.
- Current production CI38832833234 was running when this record was prepared;
  no pending job is represented as GREEN. Final verifier/provider evidence owns
  the later result. This record proves scoped source composition, not full goal
  completion, merge readiness or live host binding.
