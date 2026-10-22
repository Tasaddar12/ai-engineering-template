# Screenshot coverage evidence

Apply inside existing UI preparation, execution and verification. Use the
[scope and producer scaffold](../templates/screenshot-manifest.md) in the
consumer's existing development/test environment. This repository has no browser
application and supplies no actual page observations.

## Ownership and scope

The preparer declares the expected criterion × route × state × viewport matrix in
an external scope JSON before capture. It references the approved acceptance IDs
and [UI contract](ui-contract.md), exact served revision and URLs, deterministic
state procedures and viewport dimensions. Inspect actual route/shared-source
usage to enumerate dependencies. Record that source mapping and exclusions in the
existing PLAN. Unknown dependency coverage is a gap, not permission to use only
the homepage. Keep the scope separate from the capture manifest.

- Local screen edits require every affected route after the edits.
- Shared theme, layout, token or component edits require ALL dependent routes
  after the edits. Set `change_kind: shared`; the validator requires every route
  in the dependent inventory regardless of `affected_routes`.
- Update the inventory when routes or dependencies change. The validator proves
  coverage of the declared inventory; source review establishes its completeness.
- Preserve existing criterion IDs through PLAN, SUMMARY and Acceptance/Findings.
  A homepage capture covers only its declared cells, never all pages.

Assign ONE browser evidence producer within existing execution/check work. It
uses the actual consumer harness and the runtime `produce` callback interface.
The same manifest feeds configured checks and the existing verifier; do not add
a second browser sweep, mandatory phase, specialist or review loop. After edits,
recapture the required matrix at the candidate revision. Reuse only evidence
whose revision, URL, procedure, state, viewport and artifact bytes still match.

## Validation and consumption

Run the read-only existing-runtime verb using the frozen revision:

```text
python .ai/runtime/phase.py query verification.screenshots --scope-file /private/scope.json --manifest-file /private/captures.json --expected-revision <full-commit-id>
```

Use the installed host runtime path where applicable. The JSON output reports
`status: complete|gaps_found`, `revision`, `required_count`, `covered_count`,
`covered`, `missing` (with a reason per required cell) and structural `errors`.
Malformed scope/file inputs return the runtime's handled error. A valid query
returns exit zero even for `gaps_found`; a configured check wrapper must assert
`status == "complete"` before exiting successfully. Declare the scope, manifest,
images and browser environment among that check's inputs; disable check reuse
when the served environment is volatile. Follow existing
[verification evidence](verification-evidence.md) currentness and receipt rules.

The validator requires exact bindings and recomputes each artifact SHA-256. Missing,
failed, duplicate, unavailable, empty, mismatched or stale records do not cover a
cell. Unexpected rows and malformed manifests also prevent complete status. Local
private artifacts are valid; retain private references and share a bounded result
with the verifier. Do not force raw screenshot publication or upload.

The existing verifier joins this output with source and behavioral evidence in
Acceptance/Findings at the same revision. Preserve every missing cell and error;
use existing gap/human-needed rules for evidence that cannot be established.
`complete` means the declared capture matrix is intact, not that visual acceptance,
interaction, accessibility or actual browser behavior automatically passed. The
producer adapter must establish served revision, resolved URL, state and readiness;
JSON validation alone cannot attest those observations. Do not invent them.
