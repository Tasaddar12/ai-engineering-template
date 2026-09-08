# TASK-038 a1 c2 — R1 implementation review

**Verdict: pass.** All 11 implementation checks pass. Both c1 findings are
resolved; no new actionable findings. R2 must review this same candidate.

Candidate `6f2b12c3283ed7d6e3d4876020fe690c6e0061a3`, integration base
`c945928da13cf9081dcf85c32c849cefdf24b97c`; candidate record
`reviews/candidates/CANDIDATE-TASK-038-a1-6f2b12c3283e.json`, fingerprint
`b19e2958568f1c67da0c70f28d5e50901143bf9baf627449ae96ea5a39345e0b`.
Independent reproduction verified the raw binary diff digest, all 12 committed
context hashes, ROOT validation hash, policy/model digest, canonical fingerprint,
clean HEAD, current-base ancestry, and exactly three owned added paths. Graph r4
remains approved at structural digest
`c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e`.
Accepted TASK-004 `e3c1177f993ee74815639a83ef3333faa4ba3957` is an ancestor
of the base; its passing R1/R2 agree, and its registry source is byte-identical.
The handoff's original dispatch base is historical; this review binds the current base above.

Fresh reviewer session `/root/r1_038_c2`; request
`R1-REQUEST-TASK-038-a1-c2-053911`; invocation
`R1-INVOCATION-TASK-038-a1-c2-053911`. Coordinator-observed submitted selection:
OpenAI `gpt-6-astra`, `xhigh`, `review_high`, rank 4. Implementation session
`/root/implement_038` used coordinator-observed `gpt-5.6-sol`, `xhigh`, rank 3.
Separate provider-returned identity, effort, and provider invocation UUID were
unavailable. These IDs identify review records, not provider confirmations.
This follows `evidence/effort-provenance-clarification.md`; no schema fields added.

## Repair verification and actual validation

- **R1-TASK-038-001 resolved:** the actual unchanged source `.ai` installation now
  loads, with `local_containers` classified as autonomous. The bounded repair
  adds the established action to the closed vocabulary without editing policy.
- **R1-TASK-038-002 resolved:** zero configured invocation limits fail in
  `RunOverrides`, `RunSettings`, and strict saved hydration. Minimum 1 survives
  resolution and effective-policy serialization; `max_rewrites=0` remains valid.
- The exact declared command ran with the required ROOT virtual-environment
  interpreter from the candidate worktree: `-m unittest discover -s
  tests/unit/config/ -p test_*.py` — **29 tests, exit 0, OK**. Imports were checked
  to resolve to candidate `src`, including the accepted registry.
- Fresh independent checks validated **48 effective-policy snapshots** through
  `ContractRegistry` and observed **28 expected rejections**. Real source and
  actual fresh Codex/Claude installer outputs load; invalid native settings are
  ignored; loaded configuration bytes remain unchanged. Probes cover configured
  minima, hydration types/shape, all numeric broadening, sandbox weakening,
  saved precedence despite stricter new defaults, detached frozen values,
  unknown actions, and all nine sensitive autonomous classifications.

## Complete PLAN-001-v1 checklist

| Check | Result | Decisive evidence |
| --- | --- | --- |
| R1-01 acceptance | pass | AC1 immutable loading/precedence/compatibility and AC2 strict safe decoding pass source, installed, and boundary checks. Both prior failures are repaired. |
| R1-02 specification/exclusions | pass | REQ-01/08 and AC-01/08 retain existing `.ai` support, provider namespaces, and schema-valid settings without credentials, remote effects, or policy changes. |
| R1-03 functional correctness | pass | Traced installation discovery → accepted registry → model/policy decoding → lookups → resolution/hydration → effective policy. New regressions reproduce repaired triggers. |
| R1-04 errors/cleanup | pass | Malformed/missing/stale/incompatible inputs use explicit non-retryable domain failures. Loading only reads files; disposable installed fixtures clean up. Existing link guards are unchanged; c1 junction rejection remains historical supporting evidence. |
| R1-05 boundaries | pass | Fresh schema-bound minima and saved boundaries pass. Declared tests cover namespace/provider mismatch, compatibility, stale installation, traversal/overlap, model mismatch and unknown fields/profiles. |
| R1-06 meaningful tests | pass | Exact suite has 29 meaningful tests, now including actual source loading and registry validation of accepted policy minima; independent probes use real installer outputs and changed-default resume. |
| R1-07 bounded scope | pass | Configuration decoding only; argv stays TASK-002/006, persistence/composition TASK-009/034, observed usage/remaining facts TASK-039. No new v1 fields or concrete downstream implementation. |
| R1-08 unrelated changes | pass | Exact base/head diff adds only `src/config.py`, `tests/unit/config/test_config.py`, and owned `evidence/implementation/TASK-038.md`. Candidate remains clean. |
| R1-09 interfaces/maintainability | pass | Exact frozen `load_project_settings(root: Path, installation: InstallationRecord) -> ProjectSettings` signature; explicit flat imports, detached frozen decoded values, separate recommendations and configured bindings. |
| R1-10 security/trust | pass | Fresh sensitive-action, unknown-action, native-setting, saved-shape, broadening and sandbox checks pass. Read path/ownership/provider guards remain intact; no authorization or credential acquisition occurs. |
| R1-11 documentation | pass | Updated handoff accurately explains repair, limits, validation, provenance, immutable payload API and unimplemented persistence responsibilities. |

The saved settings representation is a closed non-record payload. Existing
`workflow-run.policy_ref` and payload/evidence references remain the intended
persistence routes; TASK-009/034 must store, verify and restore them. Configured
invocation limits remain distinct from observed or remaining usage. Current v1
installation/policy/model records have no project command-reference field;
no added schema field or argv normalization is required for this task.

Reproduction: `TASK-038-a1-c2-R1-evidence.py`; observed output:
`TASK-038-a1-c2-R1-evidence.txt`; structured result: `TASK-038-a1-c2-R1.json`.
The structured report was validated against the frozen review-result schema.
The immutable c1 report remains unchanged. No candidate or ROOT metadata edits.
