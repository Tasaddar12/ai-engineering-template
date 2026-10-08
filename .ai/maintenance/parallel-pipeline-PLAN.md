# Parallel chunk pipeline implementation scope

Authorization: the user requested a new worktree, parallel coding and scouts,
cached handoffs and Luna summarization, pushed as a separate PR without merging.
This maintenance branch starts at main dcb5c78; PR56 cf607677 remains frozen.
No adoption records, benchmark fixtures or product workflow pins are changed.

Acceptance:
- Committed reviewable chunks pin reviewer and test worktrees to one immutable SHA.
- Dependency and owned-path rules block only linked work; independent coding can continue.
- Structured review and check evidence cannot pass with missing, stale or failed results.
- Source/context reuse records source revision, hashed inputs, exact scope, acceptance,
  evidence, provenance and invalidation; this makes no provider prompt-cache claim.
- Luna scouts extract, summarize, classify and propose transformations without execution.
- Final integrated correctness, security, integration and aggregate check gates remain.

Slices: runtime and regression tests; workflow/agent/handoff contracts; final checks
and fresh independent review. Native host dispatch remains coordinator-owned; the
runtime must enforce persisted state, snapshot validation and deterministic readiness.
PR56 check receipts will be inspected for compatibility rather than copied wholesale.

Validation: focused subprocess tests, the repository unittest aggregate and four
hook suites; GitHub Linux/Windows validation. No engine, Docker or model benchmark runs.
