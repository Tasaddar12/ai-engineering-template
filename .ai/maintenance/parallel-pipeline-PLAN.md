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

Concrete implementation contract (independent planning-review amendments):
- Register full resolved base/head SHAs, plan/chunk IDs, declared owned paths and
  deletions, dependency IDs, acceptance IDs and checks; reject unsafe paths,
  unsupported ancestry and out-of-scope changes.
- Prepare separate detached reviewer/test snapshots at the registered SHA; validate
  Git/common-directory identity and reject dirty or revision-mismatched results.
- Require assignment/chunk IDs, SHA, complete acceptance/scope coverage, explicit
  status, findings/evidence/provenance. Imported reports never claim runtime execution.
- Dependent work requires integrated prerequisite and passing applicable gates;
  summary existence alone cannot satisfy it. Path and named resource conflicts block
  linked work only. Status returns ready/wait/blocked with explicit reasons.
- Common-repository runtime state uses serialized atomic persistence. Preserve failed
  attempts. Corrupt, partial, missing and stale evidence cannot pass.
- Content-address reusable packets by schema, question/task class, exact scope,
  acceptance, relevant byte hashes and provenance; revalidate bytes before reuse.
- Passing check receipts bind argv, working directory, exact SHA by default,
  configured inputs and explicit environment identity; cross-revision reuse requires
  a complete declared input contract. Empty, skipped, failed and timeout checks never pass.
- Chunk review/test evidence is provisional; final integrated verification independently
  checks correctness, security, docs/integration and configured aggregate gates.
