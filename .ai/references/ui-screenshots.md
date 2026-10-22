# Screenshot coverage evidence

Fill the [scope and producer scaffold](../templates/screenshot-manifest.md) in the
consumer's existing browser harness. Use existing UI preparation, execution and
verification assignments.

## Ownership and scope

1. **Declare scope before capture.** Write external scope JSON with acceptance IDs,
   the effective [UI contract](ui-contract.md), exact served revision, resolved URLs,
   deterministic state procedures and viewport dimensions. Keep it separate from
   the capture manifest.
2. **Inspect route dependencies.** Record the source mapping and exclusions in PLAN.
   For local edits, include every affected route and state/viewport combination.
   For shared theme, layout, token or component edits, set `change_kind: shared`
   and include ALL dependent routes; validation ignores `affected_routes` for
   shared changes. If dependencies are unknown, record the coverage gap.
3. **Update the inventory after route/dependency changes.** Preserve criterion IDs
   through PLAN, SUMMARY and Acceptance/Findings. Verify inventory completeness
   against source; validation checks only the declared inventory. A homepage
   capture covers only its declared cells.
4. **Assign ONE browser producer.** Wire the runtime `produce` callback to the
   consumer harness. Feed its manifest to configured checks and the existing
   verifier. After edits, capture the required matrix at the candidate revision.
   Reuse evidence only if revision, URL, procedure, state, viewport and artifact
   bytes still match. Keep the existing phase and review routes.

## Validation and consumption

Run the read-only query at the frozen revision. Replace the file paths and full
commit ID with the actual evidence inputs; use the installed host runtime path
when applicable:

```text
python .ai/runtime/phase.py query verification.screenshots --scope-file /private/scope.json --manifest-file /private/captures.json --expected-revision <full-commit-id>
```

Read `status`, `revision`, `required_count`, `covered_count`, `covered`, `missing`
and `errors` from the JSON result. Each missing cell includes its reason.

- If scope/file inputs are malformed, report the runtime's handled error.
- If `status` is `gaps_found`, preserve every missing cell/error in Acceptance/Findings
  and route through existing gap/human-needed rules. The query still exits zero;
  a configured check wrapper must fail unless `status == "complete"`.
- If `status` is `complete`, join source and behavioral evidence at the same
  revision before judging acceptance. Matrix completeness alone cannot pass
  visuals, interactions, accessibility or browser behavior.

Declare scope, manifest, images and browser environment as configured-check inputs.
If the served environment is volatile, disable check reuse. Apply
[verification evidence](verification-evidence.md) currentness and receipt rules.

Validate exact bindings and recomputed SHA-256 digests. Preserve failed, duplicate,
unavailable, empty, mismatched and stale captures as gaps; unexpected rows and
malformed manifests also prevent complete status. Retain private local references
and give the verifier a bounded result with access to artifact bytes. Raw image/log
publication is optional.

Require the producer adapter to establish served revision, resolved URL, state and
readiness through actual browser observations. Record unavailable observations as
missing; JSON validation cannot establish them.
