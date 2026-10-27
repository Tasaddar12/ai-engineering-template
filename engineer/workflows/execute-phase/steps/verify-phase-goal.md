# Verification consumer boundary

Only verify-work may include this fragment. Execute-phase hands off through its final run_verify_work step; it does not dispatch a second competing verifier or complete the phase itself.

Use the phase locator and init.verify-work in the actual phase session. Resolve verifier model and effort inline, omitting inherit, and resolve any needed skills with `engineer_run query agent-skills verifier --raw`. Give the verifier the full phase goal, CONTEXT, requirements, plans, summaries, source revision and current check receipts. Its work is read-only and its output belongs to the single frozen batch in verify-work.

When a SECURITY artifact exists with `threats_open > 0`, record the open threats as blockers. Include gap-closure-artifacts.md for an applicable decimal follow-up and regression-gate.md when required. Read applicable fragments directly; no manifest controls whether they are loaded. Do not duplicate execute-phase's review gate.

ORCHESTRATOR RULE: wait for every read-only result before editing source or accepting the batch. If the runtime supports verification.fingerprint, bind the report to the actual phase inputs; a missing or failed supported fingerprint is not a pass. Join canonical verdict and issue-link evidence through verify-work, not a separate next-step prompt.
