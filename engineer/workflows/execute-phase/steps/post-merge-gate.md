# Checks after integrated wave

From the exact session worktree, capture the integrated revision and run `engineer_run query verification.run-checks` when check execution is authorized. Use configured check argv, timeouts and bounded output tails; do not sniff a build system to invent another command. Reuse only receipts with current matching inputs and fingerprints.

Join every check result before accepting the wave. A failed, unavailable or timed-out required check blocks dependent waves and completion. Route known bounded in-scope defects to targeted-fixer or executor in a fresh isolated checkout; route unknown causes to debugger. Preserve the complete failure evidence and acceptance target. Wait for the correction worker to stop and commit before integrating it, then rerun invalidated checks at the new revision. A passed unrelated check cannot replace the failed requirement. User-deferred execution stays pending; do not fabricate a receipt or ask whether to ignore the failure.
