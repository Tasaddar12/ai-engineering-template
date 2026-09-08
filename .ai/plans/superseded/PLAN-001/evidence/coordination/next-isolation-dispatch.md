# TASK-015 coordination reminders

Dispatch only after accepted003/013/014/017/039. Own isolation.py, its declared
test leaf and handoff. Consume actual IsolationService.review(IsolationRequest)
and IsolationDecision, AgentAdapter and accepted graph/scope APIs; do not create
parallel public port shapes or require unowned scheduler/state implementation.

Validate complete graph/task snapshot agreement, actual structural task digest,
plan acceptance coverage, cycles and all unsequenced path/read/resource conflicts.
039 TaskContractSnapshot.content_ref permits supplied verified full records;
the minimal snapshot alone is not the full structural digest input. Build explicit
bounded review context from actual request material and bind the agent result to
the requested graph revision, task-set digest and exact checklist version.

Require all ISO-01 through ISO-12 exactly once, applicable passing evidence,
correct runtime review kind, no unresolved blocking/major findings, and matching
current graph identity. The DTO constructor's successful status alone does not
establish a passing isolation verdict. Missing, stale, conflicting, unknown or
truncated required material cannot approve a graph. Deterministic graph checks
still apply even if a scripted agent claims pass.

Use configured capability/profile and permission semantics from actual017/003;
explicit deterministic simulation remains labelled. Return the existing typed
decision and concrete evidence. Coordinator/state commits canonical approval;
an internal proposal or successful agent run does not grant publication authority.
Test initial and rewritten graphs with actual graph/scope APIs, scripted agent
output, relevant stale/digest/checklist/identity failures and material mutations.
Fresh higher-capability independent task reviews remain required for this source.
