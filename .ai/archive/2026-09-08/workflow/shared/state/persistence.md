# Durable state and concurrency protocol

## Authority

Git is authoritative for branches, refs, commits, ancestry, worktree registration, tracked/untracked changes and actual merge results. Framework records are authoritative for intended lifecycle, scope, permissions, review decisions, graph versions and attempts. Status never substitutes intended branch names for observed Git facts.

One coordinator is the sole writer per project. An OS-backed exclusive lock in the Git common directory protects its entire ownership tenure; a heartbeat is diagnostic, not permission to steal a live lock. Release on process death is OS-managed. No lock-file timestamp-based takeover. Initial supported execution is a single machine on a local filesystem; multi-host/shared-filesystem coordinators are rejected. Plan-owned records are addressed by `(kind, plan_id, local_id)`; local IDs are never looked up globally.

## Transaction algorithm

1. Acquire/retain the coordinator lock; read control branch and current generation. Reject stale `expected_generation`.
2. Validate input schemas, entity references, graph invariants, transition guards and policy. Allocate an operation ID once.
3. Append and fsync a local intent journal before side effects. Never promise atomicity across files and Git.
4. Write immutable event and updated projections into the control worktree using temp files and replace. A lifecycle relocation updates the plan/task location, status fields, registry, logical references, and manifest effects in this same transaction. Record manifest hashes and old/new generation.
5. Stage only transaction-owned paths, create a checkpoint commit, then atomically compare-and-update the state ref from the expected parent. A committed checkpoint is the durable acceptance boundary.
6. Mark local journal committed and acknowledge. Projections can be reconstructed from committed events. A crash before acknowledgment uses operation-ID deduplication to return the existing result.

Implementation must use an isolated transaction staging index/ref or equivalent so partial worktree writes are not mistaken for a checkpoint. A recovery scan resets only coordinator-owned uncommitted projections from the committed state and replays verified pending intents. It never resets a developer's worktree.

## Side effects and resumption

Persist intent before Git worktree creation, agent dispatch, integration, push or PR creation. Each intent has an idempotency key, expected base/head, desired resource identity and reconciliation strategy. Persist the observed result afterward. If a crash occurs between action and recording, inspect Git/provider by that identity first; ambiguous effects enter reconciliation, never blind duplicate dispatch/PR creation.

Agents write to unique local outboxes with request ID, attempt and hashes. The coordinator imports only outputs matching a current lease, request and graph revision; stale results are retained as rejected evidence. Parallel workers never update status JSON themselves. Lease generation fences late callbacks, while coordinator ownership is protected by the OS lock. Cancellation must terminate or isolate workers before releasing their scope.

## Portability

Checkpoint evidence required to verify a gate is tracked and content-addressed; large raw logs can remain local only when sanitized summaries and required excerpts suffice. If a gate depends on unavailable evidence, it cannot pass. Record full content digests and external artifact locations when explicitly configured. Historical manifest references resolve relative to the immutable snapshot directory that owns the manifest, then verify the stored digest; relocation never edits the retained snapshot or its original review. Git commit object IDs in handoffs refer to task code, avoiding self-referential state-commit fields; checkpoint IDs are observed through refs/events rather than embedded in their own commit.

`STATE.json` stores a compact current summary and references, not every historical event. Projection generation is an integer independent of Git hash. On another host, reconstruct logical worktrees at new paths, mark process leases unknown, inspect remote handles, and resume after reconciliation. Never persist secrets or host-specific absolute paths in portable records.
