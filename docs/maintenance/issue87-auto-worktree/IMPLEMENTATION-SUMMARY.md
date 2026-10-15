---
phase: maintenance-issue87-auto-worktree
plan: "01"
subsystem: hooks
tags: [worktrees, prewrite, tdd]
status: blocked
requirements-completed: []
acceptance: []
documentation: []
coverage:
  - id: native-prewrite
    description: Source-sensitive preparation and cancellation through installed host hooks
    verification:
      - kind: integration
        ref: tests/test_install.py#test_prewrite_claude_first_source_prepares_and_cancels_pending_mutation
        status: fail
    human_judgment: false
---

# Issue 87 implementation receipt

Tasks 1–2 only; Task 3 documentation and all integration/publication belong to
separate owners. Input/root pin: `26969d7184c2bf25a0468efe805b325471ea58c6`,
`phase-issue87-auto-code-171041844`,
`D:/Codex/2026-10-15/task-2/repo/.worktrees/issue87-auto-code-171041844`.

## TDD Evidence

RED ran against unchanged production at the input revision plus test-only edits.
Command (PowerShell; approved Python 3.13 executable):

```text
C:/Users/killi/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe -m unittest discover -s tests -p test_install.py -k prewrite -v
```

Observed: exit 1, 3 tests, 30.687s, two assertion failures and one passing control.

- `test_prewrite_claude_first_source_prepares_and_cancels_pending_mutation`:
  expected aggregate denial; observed `False`, assertion “S1/H1: installed Claude
  editing pipeline allowed the original source mutation”.
- `test_prewrite_codex_shared_parent_cancels_without_guessing_unit`: expected
  aggregate denial; observed `False`, assertion “S2/H1: installed Codex editing
  pipeline allowed an ambiguous shared-parent source mutation”.
- `test_prewrite_untracked_note_without_identity_warns_and_continues`: passed
  for both installed hosts, with advisory warning, fake note mutation and no
  extra registered checkout.

The fixture installs actual assets/settings from a committed disposable source,
commits a disposable offline target, launches every handler in its one editing
group (including actual Codex commandWindows), interprets synchronous native
denial/exit 2, and executes its fake pending mutation only when allowed. Both
target failures reached their behavioral assertion after successful launcher
execution. Missing modules/scripts/verbs, setup errors and hook exit 1 do not
establish this RED. GREEN and future helper coverage have not run.

## Matrix / expected decisions

Bounded independent RED review requested CR-01 and IN-01 before GREEN. A second
test-only run at `1414979` plus corrected tests used the same command above:
exit 1, 4 tests, 46.432s, the same two intended source denial assertion failures,
both note controls passing. Codex now supplies native `apply_patch` with
`tool_input.command` and complete Update File framing. New
`test_prewrite_external_temporary_note_without_identity_continues` exercises
actual fake create/update for both installed pipelines under a canonical plain
OS-temp directory outside every repository; it verifies fake bytes, unchanged
exact worktree listing and unchanged preparation inventory. No source changed.
CR-01 belongs to T-AW-01; IN-01 to T-AW-03. The allowed range is location based,
not extension/content based: resolved OS temp, outside every repository, plain
unlinked create/update only. Other paths, mixed operations, deletes, renames,
links and repository targets gain no exemption.

Independent input: [MATRIX.md](MATRIX.md), committed by its separate owner.
The following named coverage is required during Task 2; rows beyond the three
installed tests above are planned, not claimed executed at RED.

| Matrix | Named test family | Expected behavior |
|---|---|---|
| N1, CR-01 | installed `test_prewrite_untracked_note_without_identity_warns_and_continues`, `test_prewrite_external_temporary_note_without_identity_continues`; `test_notes_and_read_controls` | ordinary untracked nested notes and plain external OS-temp note create/update allow without identity; read does nothing |
| S1, H1 | installed `test_prewrite_claude_first_source_prepares_and_cancels_pending_mutation`; `test_native_tools_prepare_once` | exact denial; one committed-base destination; zero original mutation |
| S2 | installed `test_prewrite_codex_shared_parent_cancels_without_guessing_unit`; `test_identity_and_explicit_request_binding` | no shared-parent or missing-Claude-actor inference; explicit request mapping only |
| S3, V2 | `test_conflicting_and_stale_records` | reject ambiguous, mismatched, missing or drifted destination |
| M1, M2, M3 | `test_note_bypass_matrix` | whole mixed/tracked/delete/rename operation treated as source |
| P1, P2 | `test_path_and_link_matrix` | reject traversal/cross-root/linked/nested-repository targets; allow valid local path spellings |
| D1, D2 | `test_dirty_primary_snapshot_and_fresh_destination` | exact byte/index preservation; fresh reads, no dirty copy or replay |
| B1, V1 | `test_old_root_and_destination_continuation` | old root/marker remains denied; actual validated destination-local rebuilt call allows |
| B2 | `test_concurrent_and_uncertain_recovery` | exact deterministic reuse or actionable preserved refusal |
| I1 | `test_malformed_and_deadline_failures` | structural refusal and internal budget; wrapper exit 2; outer host failure stays a limitation |
| R1 | `test_notes_and_read_controls` | no creation/bookkeeping for reads |

## Checks / Task Commits

RED command and its bounded test-only rerun above are the only execution receipts
so far. No source changes yet; awaiting coordinator acknowledgement of corrected
behavioral RED and reconciled plan clarification.

## Threat Outcomes

| Owning PLAN / Threat | Canonical issue | Outcome | Git state | Evidence |
|---|---|---|---|---|
| [PLAN T-AW-01](PLAN.md#threat_model) | [T-AW-01](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-01) | unresolved / unimplemented | OPEN per coordinator input; no worker readback | RED only; mitigation pending |
| [PLAN T-AW-02](PLAN.md#threat_model) | [T-AW-02](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-02) | unresolved / unimplemented | OPEN per coordinator input; no worker readback | RED only; mitigation pending |
| [PLAN T-AW-03](PLAN.md#threat_model) | [T-AW-03](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-03) | unresolved / unimplemented | OPEN per coordinator input; no worker readback | fixture cancellation currently absent; live host transition unverified |

## Remaining

Task 2 source/coverage/checks remain. Task 3 and independent review/verification
are separate later assignments. No supported installed host/version or actual
automatic session transition has been established. Hooks cannot guarantee
enforcement for outer failures, cloud orchestration, existing exec sessions,
opaque shell/external writers or opted-out specialized tools. No provider
writes, merge, installation or real cleanup performed.
