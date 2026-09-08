# TASK-005 a1 c1 — R1 implementation review

**Verdict: PASS.** Both task criteria and all 11 R1 checks pass. No unresolved findings.

## Candidate and review provenance

- Plan/task: `PLAN-001/TASK-005`; graph r4, approved structural digest
  `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e`.
- Read-only source: `D:/Codex Projects/ai-engineering-template/.worktrees/TASK-005-a1`.
- Review integration base: `60a2a37f04b5d23561ce1fbc66f71b130c212f90`.
  Exact head: `0216c03b18698a3ff4bc89c9b0ae9749255425ef`.
- [Candidate](candidates/CANDIDATE-TASK-005-a1-0216c03b1869.json), fingerprint
  `e38bebfb47b00e775c3c8462a7051f21cd41313ebd268c7b6426852e27010e58`.
- Reviewer session `/root/r1_005_c1`; implementation session `/root/implement_005`.
  Request `REQUEST-TASK-005-a1-c1-R1-20260908T043638Z`; invocation
  `manual-native:/root/r1_005_c1:20260908T043638Z`.
- Coordinator-observed native selection: OpenAI `gpt-6-astra`, `xhigh`,
  `review_high`, rank 4; implementation was `gpt-5.6-sol`, `xhigh`, rank 3.
  These are submitted native settings. Separate provider-returned effective model,
  effort, and invocation UUID were unavailable. The invocation ID above is a local
  review identifier, following the [provenance clarification](../evidence/effort-provenance-clarification.md).

Independent verification reproduced the raw binary diff digest, all 12 context
file hashes, coordinator validation hash, policy/model digest, canonical candidate
fingerprint, clean source head, and approved graph/task digest. The frozen ROOT
head equals the review base. Accepted TASK-004 candidate and integration commits
are ancestors of that base, and its matching R1/R2 reports pass. The earlier
dispatch base in the implementation handoff is correctly distinguished from this
review's integration base.

## Acceptance and checklist

| Check | Result and decisive evidence |
| --- | --- |
| R1-01 | **Pass.** AC1: each supported root has 86 sorted assets, comprising 76 framework assets and 10 seeds; canonical guides/templates/workflows, 27 schemas, defaults, and four reachable tools are included. AC2: every payload digest is checked, with hash/content/metadata/order/completeness tampering and path aliases/escapes rejected. See independent probes 02–04 and the 10 declared tests. |
| R1-02 | **Pass.** REQ-08/AC-08 and ADR-005 ownership are preserved. Seeds remain project-owned after instantiation. Initialization, upgrades, migration, runtime wiring and final packaging remain with their declared owners. |
| R1-03 | **Pass.** Traced source discovery, provider rendering, immutable assets, ownership-root coverage, registry validation and exact manifest comparison. Actual Codex/Claude installations match every framework payload byte and manifest entry. Catalog-emitted tools import and validate fresh projects in isolation. |
| R1-04 | **Pass.** Missing sources/helpers/index, malformed reachable Python, invalid roots and overlapping ownership fail. Catalog construction has no target writes or retained resources. Source containment/link guards were inspected; independent temporary fixtures were cleaned. |
| R1-05 | **Pass.** Three provider roots, LF-normalized bytes, Unicode/case aliases, ancestor collisions, Windows reserved/stream/trailing names, absolute/UNC/traversal paths, mutated payloads and a cyclic transitive helper closure were checked. |
| R1-06 | **Pass.** Declared command ran 10 tests, not empty discovery. Five independent tests cover exact identity, actual installed bytes, isolated runtime imports, 90 mutation/constructor cases, and source/closure failure cases. |
| R1-07 | **Pass.** Catalog-only behavior and the bounded ownership-root correction fit TASK-005. No later workflow or package implementation was required or added. |
| R1-08 | **Pass.** Exactly four changed paths match task scope: `src/assets.py`, its leaf tests, `docs/defaults/FRAMEWORK.json`, and the task handoff. No prohibited or unrelated file changed. |
| R1-09 | **Pass.** Explicit flat-module API, frozen typed values, immutable bytes/records, shared `ScopePath`/digest/errors, and accepted `ContractRegistry` avoid new mutable or central registration boundaries. |
| R1-10 | **Pass.** Exact selected-root destination validation, portable path comparison, source containment, offline schemas and recomputed payload hashes protect the catalog boundary. No development history, credentials, provider calls or external writes enter the catalog. |
| R1-11 | **Pass.** Handoff accurately describes APIs, counts, ownership, actual-byte rendering, temporary installer parity, and deferred dynamic seed instantiation. Adding `framework.json` to owned roots matches its existing installer-managed classification. |

## Executed evidence and limits

- [Declared command](TASK-005-a1-c1-R1-declared.txt): exit 0, **10 tests**, `OK`.
- [Independent probes](TASK-005-a1-c1-R1-evidence.py) and
  [results](TASK-005-a1-c1-R1-evidence.txt): exit 0, **5 tests**, `OK`.
  They verified all 258 provider payloads; 78 manifest mutations, three payload
  mutations and nine constructor aliases/collisions; transitive imports with a
  cycle; and exclusion of an unreachable module.
- Actual Codex and Claude installations each matched all 76 managed catalog
  payloads and all seed destinations. Static seeds matched exactly. Dynamic
  project identity/time/model-policy seed instantiation is explicitly deferred
  in the API and was not mistaken for canonical seed-byte parity.
- Catalog-emitted tools ran with `-I -B` from an unrelated directory. All four
  module origins were the emitted tools directory; the validator passed each
  fresh target: 27 schemas, 6 artifacts, zero plans/tasks, 90 local links.
- Native file-symlink fixture creation was denied by Windows (`WinError 1314`).
  No executed symlink-rejection result is claimed; source containment and link
  rejection were reviewed statically. This optional fixture limit does not
  remove either task criterion's path/hash evidence.
- `git diff --check` passed. Final schema, frozen identity and source-cleanliness
  confirmation are in [report validation](TASK-005-a1-c1-R1-report-validation.txt).

R2 should independently assess the same candidate's consistency, especially
the documented canonical-seed/instantiation boundary and retained bootstrap
installer parity. R1 does not approve downstream installer/upgrade integration.
