# TASK-017 coordination reminders

Dispatch against accepted003/004/038 only. Own agents.py, agents test leaf and
TASK-017 handoff. Use actual workflow_ports AgentAdapter/AgentRequest/AgentHandle/
AgentObservation/CancelObservation and structured output values, plus injected
configuration. Do not change schemas or the shared Protocol signatures.

Provide deterministic fake start/poll/cancel behavior with idempotent handles and
structured results. Repeated start with one key must refer to one provider effect;
the same key with a materially different request conflicts. Poll/cancel must check
identity fences and preserve unknown outcomes and quiescence. A cancellation
request alone is not an observed stopped worker. Caller mutation or reordered
polling must not silently change a committed scripted result.

The later restart/E2E tasks need to query an effect after a coordinator dies between
start and recording the handle. Make that representable by the existing idempotent
start/query semantics and a deterministic fake provider store whose lifetime can
outlive one coordinator object. Document exactly what survives process restart
and how a new adapter instance reconnects. Fake provider state is distinct from
canonical workflow state; do not implement009/010 journals here.

Reject unsupported capability, provider/model/rank mismatch, unverifiable required
provenance and inadequate review rank. Configured model binding is distinct from a
role recommendation and configured:false must not silently become a production
grant. Tests may explicitly inject deterministic fake capabilities/observations;
they must not claim an actual OpenAI/Claude invocation took place. Keep requested,
submitted and observed facts distinct using existing DTO/evidence surfaces, without
invented v1 fields. Read the existing effort-provenance clarification.

Concrete review gate independence is TASK-020 and orchestration lease admission is
TASK-021; expose required facts and enforce the adapter's own request/handle
contract without duplicating those services. Return a concrete representation gap
instead of expanding another owner's source. No credentials/network/provider spend.
