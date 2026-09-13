@.ai/gsd/references/response-language-directive.md

<purpose>
Autonomous repair operator for failed task verification. Invoked by execute-plan when a task fails its done-criteria. Proposes and attempts structured fixes before escalating to the user.
</purpose>

<inputs>
- FAILED_TASK: Task number, name, and done-criteria from the plan
- ERROR: What verification produced — actual result vs expected
- PLAN_CONTEXT: Adjacent tasks and phase goal (for constraint awareness)
- REPAIR_BUDGET: Max repair attempts remaining (default: 2)
</inputs>

<repair_directive>
Analyze the failure and choose exactly one repair strategy:

**RETRY** — The approach was right but execution failed. Try again with a concrete adjustment.
- Use when: command error, missing dependency, wrong path, env issue, transient failure
- Output: `RETRY: [specific adjustment to make before retrying]`

**DECOMPOSE** — The task is too coarse. Break it into smaller verifiable sub-steps.
- Use when: done-criteria covers multiple concerns, implementation gaps are structural
- Output: `DECOMPOSE: [sub-task 1] | [sub-task 2] | ...` (max 3 sub-tasks)
- Sub-tasks must each have a single verifiable outcome

**PRUNE** — The task is infeasible given current constraints. Skip with justification.
- Use when: prerequisite missing and not fixable here, out of scope, contradicts an earlier decision
- Output: `PRUNE: [one-sentence justification]`

**ESCALATE** — Repair budget exhausted, or this is an architectural decision (Rule 4).
- Use when: RETRY failed more than once with different approaches, or fix requires structural change
- Output: `ESCALATE: [what was tried] | [what decision is needed]`
</repair_directive>

<process>

<step name="diagnose">
Read the error and done-criteria carefully. Ask:
1. Is this a transient/environmental issue? → RETRY
2. Is the task verifiably too broad? → DECOMPOSE
3. Is a prerequisite genuinely missing and unfixable in scope? → PRUNE
4. Has RETRY already been attempted with this task? Check REPAIR_BUDGET. If 0 → ESCALATE
</step>

<step name="execute_retry">
If RETRY:
1. Apply the specific adjustment stated in the directive
2. Re-run the task implementation
3. Re-run verification
4. If passes → continue normally, log `[Node Repair - RETRY] Task [X]: [adjustment made]`
5. If fails again → decrement REPAIR_BUDGET, re-invoke node-repair with updated context
</step>

<step name="execute_decompose">
If DECOMPOSE:
1. Replace the failed task inline with the sub-tasks (do not modify PLAN.md on disk)
2. Execute sub-tasks sequentially, each with its own verification
3. If all sub-tasks pass → treat original task as succeeded, log `[Node Repair - DECOMPOSE] Task [X] → [N] sub-tasks`
4. If a sub-task fails → re-invoke node-repair for that sub-task (REPAIR_BUDGET applies per sub-task)
</step>

<step name="execute_prune">
If PRUNE:
1. Mark task as skipped with justification
2. Log to SUMMARY "Issues Encountered": `[Node Repair - PRUNE] Task [X]: [justification]`
3. Continue to next task
</step>

<step name="execute_escalate">
If ESCALATE:
1. Surface to user via verification_failure_gate with full repair history
2. Present: what was tried (each RETRY/DECOMPOSE attempt), what the blocker is, options available
3. Wait for user direction before continuing
</step>

</process>

<logging>
All repair actions must appear in SUMMARY.md under "## Deviations from Plan":

| Type | Format |
|------|--------|
| RETRY success | `[Node Repair - RETRY] Task X: [adjustment] — resolved` |
| RETRY fail → ESCALATE | `[Node Repair - RETRY] Task X: [N] attempts exhausted — escalated to user` |
| DECOMPOSE | `[Node Repair - DECOMPOSE] Task X split into [N] sub-tasks — all passed` |
| PRUNE | `[Node Repair - PRUNE] Task X skipped: [justification]` |
</logging>

<constraints>
- REPAIR_BUDGET defaults to 2 per task. Configurable via config.json `workflow.node_repair_budget`.
- Never modify PLAN.md on disk — decomposed sub-tasks are in-memory only.
- DECOMPOSE sub-tasks must be more specific than the original, not synonymous rewrites.
- If config.json `workflow.node_repair` is `false`, skip directly to verification_failure_gate (user retains original behavior).
</constraints>


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

The complete upstream body above is retained from GSD-Core at
`c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977`; only recorded reference substitutions
and explicit local conflict corrections have been made. See
`.ai/gsd/PROVENANCE.json` for exact source hashes and changes.

Read `.ai/gsd/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/gsd-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The upstream `config.json`, `/gsd:*` commands, tool
names, hooks, and Node CLI examples describe GSD's system; this import does not
install or activate that system. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
