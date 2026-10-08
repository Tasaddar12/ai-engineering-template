# Reusable scout evidence packet

The coordinator stores this packet through `evidence.store --spec`; the scout
returns evidence to the coordinator and never writes the shared cache. Record only
claims supported by source or supplied evidence, with exact citations.

```json
{
  "schema": "source-evidence/v1",
  "task_class": "FACT_EXTRACTION",
  "question": "<one evidence question>",
  "source_revision": "<full current source SHA>",
  "inputs": ["<exact source file>", "<exact context file>"],
  "scope": ["<exact source file>", "<directory/>"],
  "acceptance": ["<acceptance ID>"],
  "provenance": {"role": "scout", "model": "<resolved model>", "prompt_version": "<prompt contract version>"},
  "config": {},
  "status": "complete",
  "outputs": {"answer": "<concise extraction, summary, classification or transformation proposal>"},
  "evidence": [
    {"claim": "<observed claim>", "citation": "<path:line or supplied-input id:line>", "excerpt": "<short supporting excerpt>"}
  ]
}
```

Use the same question/task class, source revision, inputs, scope, acceptance,
provenance and explicit config when looking up a packet. Revision equality is
required by default. Cross-revision reuse is permitted only when both
`reuse.cross_revision` and `reuse.complete_scope` are true and the runtime verifies
all scope bytes and inventory. A missing, invalidated, stale, partial, blocked or
failed packet is a cache miss. Store only through the coordinator. Never imply
provider prompt caching.

A packet can prevent duplicate extraction for the same evidence question. It is
not implementation, test execution, a correctness/security verdict, or final
verification. The role that owns the decision must validate consequential
citations against the current source before acting.

See the [parallel pipeline contract](../references/parallel-pipeline.md) and the
[scout dispatch procedure](../references/scout-dispatch.md).