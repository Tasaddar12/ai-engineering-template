# R2 finding 001: bounds of the private text decoder

This is a static inventory of every persisted string family routed through
`agents._text` or `_optional_text`, checked against the accepted constructors.
It supplements the [public restart probes](TASK-017-a2-c3-R2-probes-windows.json.txt)
and the focused [payload audit program](TASK-017-a2-c3-R2-payload-audit.py) /
[captured result](TASK-017-a2-c3-R2-payload-audit.json.txt). It does not require
upstream support for arbitrary strings that those constructors already reject.

## Affected typed string families

Accepted `workflow_ports._text` rejects empty/surrounding-whitespace text but
preserves the remaining value. `agents._text` additionally rejects Unicode
categories Cc/Cf/Cs and normalizes to NFC. Every field below is therefore decoded
with a narrower or changing rule than its workflow DTO constructor:

| Decoder | Persisted workflow string fields |
| --- | --- |
| `_decode_request` | `spec_refs[]`, `role`, `context_ref`, `allowed_command_ids[]`, `acceptance_criteria[].id/description/verification`, `dependency_handoffs[]`, `checklist_ids[]`, `model_profile`, `policy_ref`, `permission_subset[]`, `idempotency_key` |
| `_decode_output` | `artifact_refs[]`, `command_evidence_refs[]`, `discoveries[]`, `scope_change_requests[]`, optional `error_category`, `summary` |
| `_decode_run` | `request_ref`, `adapter_id`, optional `external_handle`, optional `output_ref`, optional `error_category` |
| `_decode_handle` | `adapter_id`, `idempotency_key`, optional `external_handle` |
| `_decode_model` | `profile`, `provider`, `model_id`, `invocation_id`, both for saved expected identity and every scripted/last observation model |

These are sites to audit, not separate claims that every field accepts every
spelling at dispatch. Configuration, capability membership, deterministic handles,
and request/output references place further constraints on identity fields. For
example, initial role/command/permission admission must match normalized injected
capabilities, initial keys are checked by the adapter, and consumed model/reference
facts must match the exact effect. Those guards must remain. Free-form description,
verification, discovery, scope-change and summary payloads must not inherit model
metadata normalization merely because all happen to be strings.

The five fresh-process scenarios reproduce actual accepted request/output failures,
including multiline payload rejection and changed terminal output. The focused
audit additionally establishes a provenance consequence without changing any
candidate source: a copied real-loader configuration has selected model ID
`r2-review-caf\u00e9`; a typed future scripted identity contains
`r2-review-cafe\u0301`. Poll correctly rejects that unequal identity and leaves its
cursor/backing bytes unchanged. Reopening normalizes the stored script to the
expected identity, and the same handle now returns success. Thus normalization can
silently repair deliberately invalid unconsumed provenance. Preserve submitted
metadata exactly and apply the existing exact identity comparison at use; do not
normalize a mismatching observation into an accepted one. This also links finding
001 to TASK-017-AC2.

## Significant whitespace in path values

`ScopePath` already rejects controls, normalizes NFC, and rejects trailing spaces
or dots in components. It permits a significant leading space in a portable
component. The additional global `value == value.strip()` check changes that
accepted path contract when the first component begins with whitespace.

The impacted decoding sites are `_decode_request` scope `write_paths[]`,
`read_paths[]`, `prohibited_paths[]`, and `_decode_evidence.path` everywhere evidence
occurs (poll/cancel observations and nested error evidence). A request with
`write_paths=(" leading-file.txt",)` validates and starts, then fails restoration.
An `EvidenceRef(" leading-evidence.json", ...)` is admitted and returned with a
successful poll, then fails restoration. Both rejections preserve saved bytes.
These focused cases use sequential object recreation, not additional subprocess
or platform matrices.

This finding does not ask for surrounding whitespace in workflow prose, nor
trailing whitespace in paths. The upstream constructors reject those inputs; the
focused audit confirms the relevant boundaries. It also confirms that an internal
newline in `DomainError.message` is already rejected by TASK-001 and therefore is
not an additional unsupported requirement.

## Existing metadata and shape validation to preserve

- Request/output/run/handle entity IDs and plan IDs already use TASK-001 canonical
  constructors. Scope resources already use `_require_text`. Evidence hashes,
  status/error enums, Git OIDs, schema identities, numeric ranks/cursors and encoded
  datetimes have their existing typed constraints. This audit found no need to
  loosen them.
- `_decode_provider_model` handles provider/name/model/reasoning_effort/effort. Real
  TASK-038 loading already applies the same normalization/control rules to configured
  values. Full saved-vs-selected profile equality, including both effort fields,
  remains necessary at every settings-bearing adapter use. `DomainError.message`
  likewise already follows TASK-001's strict canonical text rule.
- `EvidenceRef.metadata` and `DomainError.details` use `FrozenJsonObject`, whose
  arbitrary JSON string keys/values are payload. Their decoders route the mapping
  directly to that type rather than through `_text`. The focused metadata control
  preserves leading/trailing whitespace, internal newline/tab, nested values and
  decomposed Unicode exactly through success and reopening. Error-details handling
  was statically traced through the same accepted type; no separate dynamic claim
  is made for it.
- Exact nested key sets, allowed private format/source, DTO status/evidence rules,
  deterministic effect identities, complete selected model/effort binding, consumed
  history/cursor/quiescence checks and explicit simulation provenance remain
  required. Payload preservation is not permission to weaken any of these checks.

The audit ran once on Windows Python 3.12.14 using only this R2's own helper and
candidate modules. It exited 0, capturing both counterexamples and passing controls.
No source, prerequisite, schema, prior review, policy or canonical record changed.
