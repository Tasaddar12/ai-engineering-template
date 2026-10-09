## Bounded correction dispatch

- Use the [targeted-fixer assignment/result contract](../agents/targeted-fixer.md) as the sole repair input schema.
- Route by the diagnosed defect and current source evidence:

| Condition | Coordinator action |
|---|---|
| Debugger diagnosis or independently validated reviewer finding; complete bounded inputs | Dispatch `targeted-fixer` |
| Missing, stale or contradictory diagnosis/finding or instructions | Return to the originating debugger/reviewer through the coordinator |
| Unknown cause or needed source discovery | Assign `debugger`; route discovery under the scout contract |
| Broader design, API, schema, security-policy or out-of-scope change | Return to the originating debugger/reviewer; route authorized broader work to preparer/coder |
| Specifically assigned security bug; complete bounded inputs | Dispatch `targeted-fixer` |

1. Validate the diagnosis/finding and exact disjoint ownership against current HEAD.
2. Populate the central assignment schema, including named symbols, constraints, focused checks and result/SUMMARY destinations.
3. Resolve fresh dispatch values directly; never read a fixer key from init bundle maps.

```bash
FIXER_MODEL=$(phase_run query resolve-model targeted-fixer --raw)
FIXER_EFFORT=$(phase_run query resolve-effort targeted-fixer --raw)
EXPECTED_BASE=$(git rev-parse HEAD)
ISOLATION=$(phase_run query dispatch-isolation --raw)
```

4. Apply the existing [executor worktree lifecycle](../workflows/execute-phase.md) for creation and integration.
5. Under `orchestrator-worktree`, create the owned checkout through `worktree.create` and embed its [root pin](worktree-path-safety.md).
6. Under `harness-worktree`, embed [worktree-branch-check](worktree-branch-check.md) with `EXPECTED_BASE` and pass `isolation="worktree"`.
7. Bind assignment checkout/branch through coordinator/runtime or harness; set revision to `EXPECTED_BASE`.
8. Dispatch with fresh context and the populated assignment; omit inherited effort.

```
Agent(
  prompt="Follow .ai/agents/targeted-fixer.md.\n${fixer_assignment}\n${isolation_guard}",
  subagent_type="targeted-fixer",
  model="${FIXER_MODEL}",
  ${FIXER_EFFORT === 'inherit' ? '' : `effort="${FIXER_EFFORT}",`}
  ${ISOLATION === 'harness-worktree' ? 'isolation="worktree",' : ''}
  description="Repair ${diagnosed_defect}"
)
```

9. Wait for the fixer; read its committed SUMMARY and exact-owned commits.
10. Integrate through coordinator-owned `worktree.merge-wave`; rerun affected checks.
11. Resume the calling workflow's fresh independent review and verification gates for the repaired revision.
12. Return to the calling workflow's retry limit and continuation; never treat fixer checks as independent approval.

## Review and repair handoffs

- Return bounded debugger proposals and validated reviewer findings to the coordinator for [bounded correction dispatch](#bounded-correction-dispatch).
- Return fixer input contradictions or broader decisions to the originating debugger/reviewer through the coordinator.
