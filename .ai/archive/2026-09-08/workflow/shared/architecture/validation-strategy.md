# Implementation validation strategy

Test deterministic domain reducers with legal/illegal transitions and stale generations. Test state store with injected crashes at intent, projection, commit and acknowledgment boundaries; reopen and prove operation deduplication. Use actual temporary Git repositories for worktree and integration behavior, not mocked Git output alone.

Use fake agent/hosting adapters with recorded deterministic scenarios: independent tasks running concurrently, dependencies waiting, invalid output, late callbacks, hidden shared contract, repeated R1 failure, R2 fix invalidating R1, integration gap, old-head CI, ambiguous PR creation, cancellation and exhausted budgets. Never use live paid model calls as mandatory unit tests.

Ownership checks include directory ancestry, case collisions, rename/delete, generated files, semantic schema resources and undeclared scope. Command tests include argv literal handling, path spaces, timeout, output truncation/redaction, launch failure and process-tree cleanup. Windows-specific execution behavior requires real Windows CI; Linux simulation is not a support claim.

End-to-end acceptance: initialize or adopt a fixture repo; implement a plan with prerequisite plus two parallel tasks; induce recovery; resume after crash; pass both exact-candidate reviews; integration-review combined behavior; prepare fake PR/CI; observe merge and archive; clone committed state and resume/read it without conversation context. Add a real provider smoke test only after a supported adapter and explicit credentials/policy exist.

Release gates will include Python 3.11+ Linux/Windows matrix, build/install package contents, schema-example validation, meaningful unit/integration tests, static checks, and no network requirement for fake-provider workflow tests. None of those future runtime gates are claimed executed in phase one.
