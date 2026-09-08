# Saved configuration integration note

TASK-038 identified that the frozen workflow-run record has no direct fields for
max_parallel, max_review_cycles, required_sandbox, or a general resolved settings
object. This does not authorize new v1 fields or a graph change.

The existing workflow-run policy_ref can identify an immutable, schema-valid
effective policy record. State-event payload_ref and operation evidence_refs can
identify tracked, hashed supporting payloads. Configuration decoding will expose
an immutable portable saved-settings representation and strict hydration. Resume
must use the saved snapshot, preserve its limits, and reject unrecorded simultaneous
overrides. Approved ephemeral environment bindings remain outside that snapshot.

TASK-009 and TASK-034 own durable storage and composition through the existing
transaction and evidence mechanisms. They must persist the necessary settings,
verify their identity/content on restart, and reconstruct the saved values without
substituting changed project defaults. This note records an integration requirement;
it does not claim those persistence or CLI behaviors have been implemented. The
TASK-038 accepted handoff will define the exact encoder/decoder API after review.

The coordinator confirmed the existing schema fields and communicated this bounded
approach to TASK-038 on 2026-09-08. No policy, permission, acceptance criterion,
public frozen signature, schema, or structural graph field was changed.
