# SPEC-001 — Autonomous local engineering lifecycle

Status: active foundation specification.

## Problem and users

An engineer should be able to give a plan to a reusable Python tool and get coordinated implementation that survives agent/session loss. A fresh agent should recover project knowledge from Git, and reviewers should verify exact code and architecture context.

## Requirements

REQ-01 structured repository memory and source-of-truth separation; REQ-02 isolated Git task worktrees and reconciliation; REQ-03 plan/task coverage, isolation and DAG; REQ-04 parallel agents with minimal explicit context; REQ-05 validation plus independent R1/R2 higher-capability review; REQ-06 autonomous bounded recovery and supersession; REQ-07 final integration review, authorized PR/CI/merge and archive; REQ-08 install/adopt/upgrade ownership; REQ-09 cross-platform Python CLI, command evidence and resumable execution.

## Non-requirements

Distributed coordination, UI, a database service, a specific commercial model provider, production deployment and unattended authority escalation. A production adapter remains required for real autonomous code generation after the fake-adapter MVP proves the engine.

## Acceptance

PLAN-001 AC-01 through AC-09 operationalize REQ-01 through REQ-09 respectively. Validate failure scenarios as well as the happy path. Both review stages and plan integration must pass; no code mutation may reuse stale approval. Review failures trigger defect repair or structural recovery without ordinary human interruption.

## Security, scale and observability

Single-host local filesystem initially, bounded parallelism and run-wide budgets. Capture every process execution with redacted argv, cwd, exit code or explicit unknown/timeout, timestamps and log refs. Worktree scope is not a security sandbox. Provenance, idempotency, fencing and authorization are required at side-effect boundaries.

## References and unresolved choices

See the [internal architecture](../../../shared/architecture/overview.md) and ADR-001–005 under `.ai/decisions/`. Real model/provider credentials, hosting integration and public licensing are deferred explicit configuration/release decisions, not blockers for local deterministic implementation.
