# TASK-006 a2 candidate validation failure

The single bounded recovery allowance recorded in
[the coordinator decision](TASK-006-coordinator-decision.md) has been consumed.
The coordinator stops candidate formation and returns immediately to independent
recovery. No further repair, review waiver or rewrite is authorized by this record.

Observed ROOT base `17595809d6ee74b2585265d94535cb1630d3a900`; source snapshot `4fe9e7a30378e13b43dc51745593adae2bb8b051` in the clean retained
TASK-006-a2 branch/worktree. Owner `/root/implement_006_a2` stopped with FINAL at
`5e455de46416758f0438c95ecda71c0630dc64a8`; coordinator merged the current ROOT
metadata before exact validation. The binary diff SHA-256 is
`7e50dd79d2a38622fa380ab2f7a31c7f258a701006cb9cd8b11716c7a765488d`. It changes only the original three owned
paths; the post-salvage repair changes only tests and handoff. Production remains
Git blob `39828108eb7d198d81d810c8fd9e136e3f64f8f0` / SHA-256 `700079bb47853a1d4cdebaa89bafcacf03885a81f9ef57687ec7203338ec29d0`.
Failed a1, all c1/c2 reviews and the first recovery remain preserved.

## Actual coordinator validation

Windows Python3.12.14:22 discovered,21 non-skipped,one established skip, exit0.
Linux Python3.12.3:22 discovered,21 non-skipped,one established skip, exit1,
one assertion failure. Both runtime/origin probes passed with jsonschema4.26.0
and commands.py from the exact a2 tree. Exact declared argv was used through
the local interpreters and WSL --exec. The coordinator did not run the remaining
Windows/Linux3.11 stages after this failure. Owner-reported four-environment
success remains preserved as prior evidence and does not override this rerun.

- [TASK-006-a2-4fe9e7a30378.txt](../validation/TASK-006-a2-4fe9e7a30378.txt): SHA-256 `9f9a9ac0269d508461dbfb85eb3abb2f80388029766bf2d243f34f35220c8700`.
- [TASK-006-a2-4fe9e7a30378-linux.txt](../validation/TASK-006-a2-4fe9e7a30378-linux.txt): SHA-256 `e7033e14f5ec0287797d127b12c798eb2c6c86f694768e09085dcb5add0f011d`.

Linux failure: inherited-pipe cancellation subcase, test_commands.py line799:
`assertGreaterEqual(elapsed, 0.75 if mode == "timeout" else 0.15)`.
Actual elapsed `0.10913950300891884` is below the required `0.15` seconds.
The same subcase reports phase `inherited_after_parent_exit`, startup0.051996s,
cancel response0.057143s, one native termination call, both exact identities gone,
readers settled and no watchdog intervention. The assertion fails before the
later status/EOF/schema assertions in this subcase, so those later assertions
are not claimed to have executed here. All four fixture cleanup summaries report
confirmed teardown. No production defect is established by this failure alone.

The coordinator read the exact failing line and preserved raw results without
rerunning tests or changing source. The observed minimum-duration assertion is
inconsistent with a readiness-triggered fast cancellation, but independent
recovery must assess the cause and any justified next bounded action. This
record itself grants none. No final candidate fingerprint or c3 R1/R2 exists:
candidate formation stopped at failed validation. Cumulative formal history
remains c1 R1FAIL, c2 R1PASS/R2FAIL; one additional post-recovery validation
allowance failed. AllTASK-006 descendants stay undispatched/unaccepted.

Generation32 advances to33; TASK-006 is repairing with independent recovery
required. Nine of39 tasks remain accepted. Native accounting before recovery
dispatch is73/300; the next fresh recovery invocation will be74. Historical
rewrites remain3/3 used,0remaining. Keep lineage usage/history and original
permissions/criteria intact; no ordinary retry or fourth rewrite is available.
TASK-024 continues independently in its owned worktree. No runtime active_run
identity exists, so no synthetic runtime recovery record is created.
