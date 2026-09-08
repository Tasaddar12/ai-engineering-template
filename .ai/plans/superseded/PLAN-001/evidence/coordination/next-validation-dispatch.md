# TASK-018 coordination reminders

Dispatch only after actual003/006 acceptance. Own validation.py, validation test
leaf and TASK-018 handoff. Use the frozen Validator.run(ValidationRequest) ->
ValidationResult boundary and accepted command DTO/runner behavior. Inject the
configured command catalogue and local bindings; never execute caller-authored
shell text or silently enable an arbitrary discovered command.

Bind every observed outcome to the requested worktree and exact current revision.
Verify before/after revision facts using a suitable injected observation boundary;
do not import unaccepted Git/state services or treat an intended branch name as
observed revision. Missing/unknown/stale facts cannot make the suite pass.

Configured command IDs and their success rules are authoritative. A request must
not weaken unittest_nonzero_count to exit_zero. Require each command exactly as
configured and preserve fixed argv via the accepted runner. Validate returned
command identity, terminal status, observed exit and durable evidence availability.
Timeout, cancellation, unknown, launch failure, missing or mismatched evidence,
truncated output hiding required success proof and zero discovered tests cannot
be accepted as successful suite validation.

The command runner records process facts; this owner interprets success rules.
Use actual nonzero unittest output and meaningful rejection cases, rather than
tests that replace the entire runner with an always-successful stub. Hash/check
the evidence read for decisions; missing or changed log bytes are not proof.
Keep validation before candidate fingerprint creation to avoid circular hashes.
Later019/020 own candidate and review gates; no new public schema fields or imports
across undeclared task boundaries. Document actual platform coverage and limits.

The injected configured suite must determine required membership as well as each
command's success rule. Bind command_suite_id to its complete declared command set;
a request that silently omits a required check or substitutes another configured
command must not turn a partial run into a passing named suite. An internal typed
suite/catalog collaborator is permitted within validation.py; no new v1 record or
unowned configuration field is needed. Keep the actual ordered command observations
and requested run/task/revision identity available in durable validation evidence.
