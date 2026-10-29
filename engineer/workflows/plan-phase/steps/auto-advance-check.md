@~/.claude/engineer/references/run-resolver.md

Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

# Plan phase auto-advance and implementation authority gate

Read this step at the end of plan-phase before deciding whether to dispatch
execute-phase.

## Resolve whether a chain was requested

Treat `--auto` or `--chain` in the current plan-phase invocation, or the
ephemeral `workflow._auto_chain_active` value, as an auto-advance request.
`workflow.auto_advance` is a persistent preference used by discuss-phase to
continue into planning; it is not implementation authorization. Do not infer
an execute request from the roadmap, plan readiness, suggested next steps, or
the presence of `--auto`/`--chain`.

If no chain trigger is active, clear a stale ephemeral flag and show the normal
next-step choices. Do not dispatch execute-phase.

## Check the user's phase-scoped authorization

Read `${phase_dir}/${padded_phase}-CONTEXT.md` and inspect its
`<execution_authorization>` section alongside the existing session history.
Execution is authorized only when all of these are supported by a direct user
instruction that remains in force:

- `Status: Granted`.
- A direct instruction from the user to implement this exact phase.
- Scope that names the current phase and does not exceed the user's instruction.

If the current context predates this section, an earlier direct instruction in
the context or existing session history still counts when it names this phase
and has not been withdrawn. Carry that instruction and its scope into the
section before dispatch; do not ask the user to repeat it. An absent or default
record with no such evidence, ambiguous wording, or a scope mismatch fails
closed. `--auto`, `--chain`, the persistent preference, phase discussion,
planning approval, and plan readiness do not change that result. This is an
orchestrator evidence check; no runtime command parses or grants permission
from the section.

When authorization is absent or invalid:

1. Clear the ephemeral chain flag:
   ```bash
   engineer_run query config-set workflow._auto_chain_active false
   ```
2. Tell the user that planning is complete and implementation awaits an
   explicit instruction for this phase.
3. Route to the normal next-step output. Do not invoke the Skill tool for
   execute-phase.

## Dispatch only after the gate passes

When a chain trigger is active and the phase-scoped authorization is valid,
dispatch execute-phase for the same phase through the Skill tool using the
workflow's established arguments and `--no-transition` behavior. Preserve the
existing return-status handling. Do not broaden the authorized phase scope or
carry permission forward to another phase.
