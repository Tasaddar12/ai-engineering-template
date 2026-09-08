# TASK-038 a1 c2 — R2 consistency review

**Verdict: pass.** All 12 consistency checks pass; no findings or structural replan.

Candidate `6f2b12c3283ed7d6e3d4876020fe690c6e0061a3`, current base
`c945928da13cf9081dcf85c32c849cefdf24b97c`, fingerprint
`b19e2958568f1c67da0c70f28d5e50901143bf9baf627449ae96ea5a39345e0b`.
The complete bound context is the candidate record
`reviews/candidates/CANDIDATE-TASK-038-a1-6f2b12c3283e.json`.
Same-candidate R1: `reviews/TASK-038-a1-c2-R1.json`, SHA-256
`35812dc72de101edaaf1e94045ae5dda22ed76eebe00dcb80792602d0809bfd9`.
R1 is schema-valid and passes all 11 checks; its Markdown and companion hashes
are recorded in this review's evidence. Prior c1 failures remain immutable.

Fresh session `/root/r2_038_c2`; request `R2-REQUEST-TASK-038-a1-c2-055154`;
invocation `R2-INVOCATION-TASK-038-a1-c2-055154`. Coordinator-observed submitted
native selection: OpenAI `gpt-6-astra`, `xhigh`, `review_high`, rank 4.
Implementation `/root/implement_038` used submitted `gpt-5.6-sol`/`xhigh`, rank 3;
R1 session is `/root/r1_038_c2`. These are three distinct sessions.
Separate provider-returned model/effort confirmation and provider invocation UUID
were unavailable. IDs above identify this review, not provider confirmation.
This records the distinction required by `evidence/effort-provenance-clarification.md`;
automatic policy profiles remain unconfigured and no v1 field was added.

Independent verification reproduced the raw binary diff digest, all 12 committed
context hashes, ROOT validation hash, raw ROOT policy/model digest, canonical
fingerprint, clean actual head and current-base ancestry. The diff adds only
`src/config.py`, `tests/unit/config/test_config.py`, and the task handoff.
Approved graph r4 and structural digest
`c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e`
match all 39 current task dependency records. Accepted TASK-004
`e3c1177f993ee74815639a83ef3333faa4ba3957`, TASK-002
`460ab567d01912167557f2f671ed07c63f0a31e7`, and TASK-003
`d51b72ce71ea3ac3ad31adf41e3eddc84738ac0b` have matching passing reviews,
are base ancestors, and retain byte-identical relevant source. The handoff's
original dispatch base is historical; this report binds the current base above.

| Check | Result | Decisive evidence |
| --- | --- | --- |
| R2-01 Architecture | pass | Configuration reads/decodes settings only; no dispatch, state transaction, credentials, authorization or downstream implementation. |
| R2-02 ADRs | pass | ADR-001–005 retain flat Python, offline JSON, sole state writer, isolated candidate review, bounded recovery and asset ownership. |
| R2-03 Accepted siblings | pass | Accepted registry/installer/validator and local/workflow ports remain unchanged; source and both real provider installations load. |
| R2-04 Interfaces/imports | pass | Frozen `load_project_settings(root: Path, installation: InstallationRecord) -> ProjectSettings` matches exactly; imports resolve candidate `src` and use accepted errors/registry. |
| R2-05 API/versioning | pass | Explicit compatibility and upgrade refusal, immutable decoded values, distinct model recommendations/bindings, restrictive overrides and saved precedence preserve current contracts. |
| R2-06 Schemas/persistence | pass | 96 effective-policy validations and exact installation/policy field parity pass. Existing policy/content references represent saved settings; undeclared workflow-run fields reject. |
| R2-07 Conventions | pass | Flat typed module, task-owned leaf tests and plan-local handoff; precisely three allowed paths, no shared exports or metadata changes. |
| R2-08 Duplication | pass | Reuses TASK-004 registry and TASK-001 errors; command argv, persistence, runtime wiring and observed usage remain with their owners. |
| R2-09 Abstractions | pass | Closed RunSettings payload is distinct from a v1 record; policy classification creates no grant, and configured invocation limits remain distinct from usage facts. |
| R2-10 Tests | pass | Fresh declared 29-test suite plus independent source/installer, schema, immutability, precedence, rejection and command-interface probes test observable behavior. |
| R2-11 Documentation | pass | Handoff accurately describes repaired source action and invocation minimum, saved APIs, 29 tests, provenance limits and TASK-009/034 integration duties. |
| R2-12 Plan assumptions | pass | AC-01/08 and REQ-01/08 remain supported; approved graph/context and same-candidate R1 unchanged. No scope, signature, schema or dependency change needed. |

Actual validation used the prescribed ROOT virtual-environment interpreter from
the exact task worktree, with candidate module origins verified:

- Declared `test.TASK-038`: exit 0, **29 tests**, `OK`.
- Independent cross-contract probes: exit 0, **96** effective-policy registry
  validations, **54** expected rejection cases, source `.ai` plus real fresh
  `.codex`/`.claude` installs; native settings ignored and input bytes unchanged.
- Reproduced both c1 repairs: actual `local_containers` source policy loads;
  zero configured invocations reject in constructors/hydration while invocation
  minimum 1 and rewrite minimum 0 serialize to valid policies.
- Foundation validator: exit 0; 27 schemas, 154 artifacts, 39 tasks, 280 unordered
  pairs, four archive manifests and 281 local links. This complements the task
  suite and is not evidence of completed runtime implementation.
- Binary diff whitespace check passed; final candidate remained clean/frozen.

Persistence probes establish schema representability only. TASK-009/034 must
store and verify the immutable effective policy and supporting settings payload,
restore necessary saved configuration, and compose resume through existing
references. No durable IO, hash verification on restart, or full resumed workflow
is claimed here. TASK-038 does not own command argv or observed usage handling.

Reports and reproduction are the same-stem `.json`, `-evidence.py`,
`-evidence.txt`, `-foundation.txt`, and `-report-validation.txt` files. The final
JSON was validated against the frozen review-result schema. Reviewer changed
only this report and companion evidence. Coordinator integration may proceed
under its existing gate rules; this review does not accept, merge or dispatch.
