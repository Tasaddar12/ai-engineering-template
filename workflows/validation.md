---
name: validation
trigger: Coordinator selects configured named checks for an exact subject revision
responsible_role: orchestrator
required_inputs:
- subject
- exact_revision
- command_names
permitted_effects:
- run_named_commands
- write_bounded_redacted_evidence
outputs:
- validation_result
stop_conditions:
- command_denied
- failed_or_incomplete_check
- revision_changed
resume: Repair in the same worktree and run a fresh complete validation on the new head.
---
# Validation

Validation executes only named commands from `.ai/constraints/commands.yaml`. Plan text,
agent output and future artifacts cannot introduce executable commands or widen policy.

1. Bind subject, worktree, exact head, selected command names and applicable task
   narrowing before execution.
2. Resolve argv, cwd, timeout and role/workflow limits from current configuration.
3. Run every subprocess through `CommandRunner` with deny-by-default policy, bounded
   redacted evidence and descendant termination.
4. Record each actual exit/status and bind the aggregate result to the exact head.

Missing, denied, timed-out, failed, truncated or stale evidence is not PASS. A code
change invalidates validation and requires a complete fresh run. Dry-run is reported
as DRY_RUN and never as successful validation.
