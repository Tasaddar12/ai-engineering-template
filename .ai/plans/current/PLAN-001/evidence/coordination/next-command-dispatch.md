# TASK-006 implementation briefing supplement

Dispatch only after TASK-038 is actually accepted. Use the actual accepted
TASK-002 command DTOs, TASK-004 registry and TASK-038 configuration APIs. Read
the task record, explicit references, accepted handoffs and local agent brief.

Own only src/commands.py, tests/unit/commands/ and the TASK-006 handoff. Implement
the frozen execute(CommandRequest) -> CommandEvidence signature with injected
configuration and host-local dependencies. Constructor collaborators may express
bounded cancellation/evidence storage without changing another task's port or
inventing serialized v1 fields.

Prove actual shell=False argv execution preserving significant spaces, multiline
payloads, tabs, order and repeated arguments. A Python -c payload is a useful
real-process regression. Metadata trimming must not leak into argv handling.
Project initialization with plan_id=None and cwd_relative='.' is valid. Test all
project/worktree/control cwd policies, absent or escaped bindings, and platform
restrictions against actual local paths. Windows batch wrappers can invoke an
implicit shell; reject unsafe execution paths rather than silently treating them
as equivalent to direct executables.

Consume explicit permissions and permitted ephemeral environment bindings;
configuration decoding itself grants nothing. Never inherit arbitrary secrets
or persist host absolute paths or sensitive binding values in portable evidence.
Environment values may be empty, but process-incompatible values such as NUL
must fail before launch. Explicitly test secret redaction across read boundaries
and the output byte cap; truncation must not expose a partial secret. Retain exact
unredacted argv meaning for execution and explicit flags for evidence changes.

Record observed start/finish/status/exit or launch failure, timeout, cancellation
and unresolved/unknown states honestly. Terminating only the parent while leaving
children alive must not claim confirmed quiescence. Test local process cleanup
on this Windows host; document any Linux-only coverage separately. Evidence/log
refs must hash durable bounded redacted bytes; no stale artifact overwrite from
identity reuse. Later validation TASK-018 evaluates declared success_rule and
nonzero test counts, so don't mistake command exited0 for whole task acceptance.

Do not implement Git/state services or edit unowned modules. If an actual port
cannot represent necessary behavior, return a concrete minimal reproduction to
the coordinator. Commit a clean candidate and FINAL once access has stopped.
