# TASK-038 a1 c1 — R1 implementation review

**Verdict: fail.** Two reproducible defects require a new candidate and fresh R1/R2.

Reviewed `5ce39a43fce2449af60ff53b645c212e7558435b` against current base
`ca6fac788dc5273d346d2a671e3e74185da0f757`. Candidate:
`reviews/candidates/CANDIDATE-TASK-038-a1-5ce39a43fce2.json`; fingerprint
`a4f856e1b67a9dc9205fba35a1986f0ceea3cb1eaa42d9818dfea8ccdb8315f3`.
The raw binary diff, all 12 committed context hashes, ROOT validation hash,
policy/model digest, clean HEAD, exact three added paths, approved r4 structural
digest, and accepted TASK-004 ancestry were independently verified. The handoff's
older dispatch base is historical; this review binds the supplied current base.

Fresh reviewer session `/root/r1_038_c1`, request `R1-REQUEST-TASK-038-a1-c1-050849`,
invocation `R1-INVOCATION-TASK-038-a1-c1-050849`. Coordinator-observed native
selection: OpenAI `gpt-6-astra`, `xhigh`, `review_high`, rank 4; implementation
session `/root/implement_038`: `gpt-5.6-sol`, `xhigh`, rank 3. These are observed
submitted selections, not separately provider-returned identity or effort.
Neither provider confirmation nor a provider invocation UUID was exposed.
This follows `evidence/effort-provenance-clarification.md`; no schema fields added.

## Findings

1. **R1-TASK-038-001 — major: the actual source project cannot load.**
   `load_project_settings(worktree, load_installation_record(worktree))` raises
   `invalid_input`: `unknown policy actions: local_containers`. The unchanged
   source policy explicitly authorizes that action, but `src/config.py:32` omits
   it from the closed vocabulary and `src/config.py:1002` rejects it. This blocks
   normal configuration loading for the existing supported `.ai` installation.
   Add the established action to the appropriate closed classification without
   changing project policy; test the real source-policy shape as well as fresh
   installed defaults. Links: TASK-038-AC1/AC2, PLAN-001 AC-01/AC-08.

2. **R1-TASK-038-002 — major: an accepted override emits an invalid effective policy.**
   `settings.effective_policy(RunOverrides(max_agent_invocations=0)).to_wire()`
   returns a policy with zero, but the accepted registry rejects it at
   `/max_agent_invocations`: `0 is less than the minimum of 1`.
   `RunSettings` and `RunOverrides` permit zero (`src/config.py:561`, `:594`),
   and `effective_policy` copies it into the advertised schema-valid snapshot
   (`src/config.py:693`). Thus TASK-009/034 cannot persist the proposed
   `workflow-run.policy_ref` snapshot through the frozen contract.
   Keep configured invocation limits within the existing policy minimum across
   overrides, hydration, and effective snapshots. Preserve the distinct valid
   `max_rewrites=0` boundary and leave observed usage/remaining-budget facts to
   their owners. Add a regression validating every accepted effective-policy
   boundary against the registry. No schema or policy change is needed.
   Links: TASK-038-AC1/AC2, PLAN-001 AC-01/AC-08.

## Validation and complete checklist

The declared command ran with the required interpreter from the exact worktree:
`-m unittest discover -s tests/unit/config/ -p test_*.py` — exit 0, **27 tests**, OK.
Imports resolve to this worktree's `src/config.py` and `src/contracts.py`.
Independent evidence records **4 positive checks, 31 expected rejections, and
2 reproduced defects**. No source files changed; HEAD remained clean.

| Check | Result | Decisive evidence |
| --- | --- | --- |
| R1-01 acceptance | fail | Both ACs are incomplete: actual source loading and accepted effective-policy compatibility fail. |
| R1-02 specification/exclusions | fail | Existing `.ai` support and schema-valid reconstruction regress; provider, credential, and persistence exclusions are otherwise respected. |
| R1-03 functional correctness | fail | Traced load → registry → policy decoding, model lookups, override resolution, and effective snapshot; findings 001/002 reproduce. |
| R1-04 errors/cleanup | pass | Missing/unknown/malformed inputs use explicit non-retryable domain errors; read-only loading has no resource acquisition or writes. Real junction refusal passed. |
| R1-05 boundaries | fail | Namespace ambiguity, traversal, ownership overlap, capability, and sandbox checks are covered, but current source action and zero-invocation boundaries fail. |
| R1-06 meaningful tests | fail | 27 useful tests pass, but the synthetic source fixture omits the existing action; the zero-limit test affirms an incompatible value without validating its effective policy. |
| R1-07 bounded scope | pass | Configuration-only implementation; no provider dispatch, credentials, persistence implementation, new schema, or argv decoding. |
| R1-08 unrelated changes | pass | Exact diff adds only `src/config.py`, `tests/unit/config/test_config.py`, and the owned handoff. |
| R1-09 interfaces/maintainability | pass | Frozen signature is exact; typed frozen values, detached payloads, explicit model recommendations/bindings and decoder functions use the accepted registry. |
| R1-10 security/trust | pass | All nine sensitive actions rejected as autonomous; configured-model mismatch, broader overrides, unknown payload fields, and external junction reads rejected; native settings confer no binding. |
| R1-11 documentation | fail | Handoff correctly bounds persistence/argv ownership, but claims schema-valid effective policy for all accepted values and source loading despite findings 001/002. |

The saved payload is a closed non-record value. JSON round-trip and relocation to
a different project root preserve restrictive saved settings despite changed
defaults; simultaneous new overrides are rejected. Persistence and hash verification
remain TASK-009/034 work through existing `policy_ref` and hashed payload/evidence
references. No direct workflow-run fields were demanded. The actual v1 installation,
policy, and model schemas define no project command-reference field; plan-owned
command definitions and argv stay with TASK-002/006. Neither point is a finding.

Reproduction and full observed output: `TASK-038-a1-c1-R1-evidence.py` and
`TASK-038-a1-c1-R1-evidence.txt`. Structured result:
`TASK-038-a1-c1-R1.json`. No other correction or scope expansion is requested.
