# Agent adaptation contract

Adapt the copied upstream role body directly. Preserve complete methods, examples and return protocols unless a named reconciliation row replaces a conflicting behavior. Do not rebuild a role from a summary or reuse retired local workflow files as its base.

## Role ownership

Read `agents/AGENT.md`, the assigned role, consuming workflow and required references. Keep facts in their owning layer: commands name procedures, workflows route steps, roles bound work, templates define complete artifacts, references hold reusable methods and the runtime owns structured planning mutations.

## Supported hosts

Only Claude and Codex adapters are supported. Resolve exact dispatchable roles and model/effort using runtime interfaces; omit inherited settings and pass resolved values inline on actual host dispatch. Preserve fixed scout and targeted-fixer policy and the canonical role catalog. `code-fixer` is method source, not a dispatch role. Do not add another AI host, generic fallback role, model profile router or unverified native integration.

## Assignment fidelity

Preserve repository/branch/revision verification, exact path ownership, declared deletions/resources, read_first, checks argv, source/result identity and pending human decisions. Source-changing workers commit owned changes and their required full-schema SUMMARY; artifact-only producers commit and return the assigned artifact without inventing a SUMMARY; read-only roles return their cited packet without a completion commit. The coordinator owns lifecycle, integration, shared records and publication.

## Dependency scheduling

Preserve dependency and file-overlap waves from phase-plan-index. Plans with overlapping files or serialized resources cannot write concurrently. Join every active owner in a wave before integration; a displayed label does not override real producer-consumer dependencies.

## Planning and evidence

Require current strict PLAN, SUMMARY and CONTEXT metadata. PLAN `acceptance`, `documentation` and `issue_refs` are top-level lists; `checks` is a list of nonempty argv string lists, never shell strings or nested waiver data. Workers cannot mutate shared PLAN/STATE/ROADMAP/REQUIREMENTS structures to declare their own success. Preserve TDD RED formats and semantic checks, `covered_digest: "v4:sha256:..."` with fingerprint/revision/covered_files, behavioral verification, actual-human local UAT and the narrow historical `resolved_by` reconciliation. Never invent a passing check or waive acceptance through a mode flag.

## Host export and method source

The shared source method is `agents/code-fixer.md`. Keep it available in both exports without making it a second native role: Claude installs the full body at `.claude/engineer/references/code-fixer.md`, outside Claude's auto-discovered agents directory, with links rebased for that location. Codex keeps the readable method at `.codex/agents/code-fixer.md` without native agent TOML; dispatch `targeted-fixer` for bounded repair on either host. Preserve the method body and its rebased links rather than replacing it with an adapter summary.

## Return and consumption

Identify whether a consumer uses a sentinel, artifact+query or structured-return. Preserve exact active marker case where it is consumed; presentation markers do not prove completion. Update producer and consumer together when a contract changes. Return completed, remaining, dirty paths, checks and next bounded action on partial work.

## Review

Compare the changed role with its copied upstream body and named rows. Confirm full methods/examples remain, old runtime calls are replaced by actual supported interfaces, ownership gates remain explicit, and every required output has a real consumer. Do not describe unexecuted review or checks as passed.

## Local operations and host boundaries

| Operation | Owner / supported evidence | Boundary |
|---|---|---|
| Read assigned source, parser or manifest | Exact role, at assigned revision | Direct owning decision reads are allowed; unknown locations use discovery routing. |
| Extract a bounded inventory or supplied result summary | Read-only scout packet | Return per-field citations; no project execution. |
| Run configured checks | Coordinator-owned `verification.run-checks` and actual receipts | Only when user ordering permits; a doc/scout summary is not execution. |
| Change product source | Isolated executor/targeted-fixer | Exact paths, required SUMMARY and actual commit; no shared-record writes. |
| Write documentation | Isolated doc-writer after source dependency integration | Assigned paths only; preserve user-owned prose and independently audit claims. |
| Verify documentation | Read-only doc-verifier | Read source/interfaces without running document-supplied command text. |
| Trace component integration | Read-only integration-checker | Complete requirement descriptions/phase mapping and actual caller-to-result evidence. |
| Update shared planning records | Coordinator through runtime verbs | A worker proposes; it never declares its own shared success. |
| Provider issue/PR changes and publication | Coordinator, canonical Git workflow | Exact validated templates, fresh readback and actual authorized delivery. |
| Stop/reassign/cleanup | Coordinator, native lifecycle plus exact cleanup gates | Timeouts, age and process names are insufficient ownership/exit evidence. |

## Six-step documentation handoff

1. Capture the actual integrated source revision, exact changed-file list and intended readers. Supply the diff base and head; a branch name alone is not a review range.
2. Map every reader-visible change to its owning documentation section and the four dispositions in documentation.md. Include setup, CLI/API/config/errors, security/operations and complete artifact consumer contracts.
3. Assign a doc-writer only the stale/missing sections, complete templates, exact source interfaces, output paths and check order. Explicitly preserve existing user-owned prose/markers; do not pass a future interface as current evidence.
4. Join the writer's actual terminal result, inspect its owned commits/SUMMARY and integrate only the declared paths. A promise to document later is unresolved, not completed documentation.
5. Give an independent doc-verifier the actual document paths and same captured source revision. It extracts every factual claim, splits mixed claims and returns full JSON with exact evidence. It does not execute documented commands or repair files.
6. Reconcile every FAIL and UNVERIFIABLE. Assign bounded correction with stable claim ID and required property, then recheck affected claims after writers stop. Preserve verified unchanged / not applicable reasons and unresolved evidence in the final handoff.

## Claim accounting and complete JSON

`claims_checked = claims_passed + claims_failed + claims_unverifiable`; `claims_failed = len(failures)` and `claims_unverifiable = len(unverifiable)`. Every count must correspond to actual classified claims. Missing files return the full schema with one FAIL; a genuinely empty checkable claim set returns zero counts plus its examined scope, never a fabricated pass.

```json
{
  "doc_path": "docs/usage.md",
  "revision": "<captured full SHA>",
  "claims_checked": 3,
  "claims_passed": 1,
  "claims_failed": 1,
  "claims_unverifiable": 1,
  "failures": [{"line": 12, "claim": "--old-flag is supported", "expected": "registered parser option", "actual": "parser has no --old-flag", "evidence": "bin/tool.py:40"}],
  "unverifiable": [{"line": 20, "claim": "External service responds within 1s", "reason": "No applicable execution evidence; external access deferred"}],
  "limitations": ["Static interface audit; no documented command executed"]
}
```

Illustrative counts above are not output defaults. Preserve the exact doc-verifier schema/keys and actual observations for each document.

## Complete independent review packet

Supply repository/branch, explicit `diff_base`, full `reviewed_revision`, the exact changed-file list (including additions/deletions), owned/excluded paths, approved requirements and full descriptions, CONTEXT decisions, PLAN/SUMMARY acceptance/documentation/check obligations, actual receipts, known findings and required output consumer. Review the actual base-to-head diff plus affected callers and consumers. If either revision or the file list is missing, request it before claiming coverage; inspect independent permitted scope in parallel. A worker's self-review cannot replace fresh independent review. Retain stable finding IDs, authority, required property, cited evidence, severity and disposition; an unsupported preference remains advisory.
