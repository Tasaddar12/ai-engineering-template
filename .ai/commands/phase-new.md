# Receive a phase

Read [RULES](../RULES.md), PROJECT, REQUIREMENTS and ROADMAP. Search existing
phase context and deferred findings before creating duplicate work.

If the information belongs to an existing phase, update that phase's relevant
context section within authorized scope. Preserve unresolved questions. A
separate capability or independent repair can become a new phase.

For a new phase, use the assigned integration worktree:

```text
python .ai/runtime/phase.py new authentication --title "Authentication"
```

The runtime creates a numbered stable phase with pending CONTEXT. Treat the name
above as an example, not a template requirement. Record the original request,
goal, acceptance candidates, known decisions, dependencies and sources. Add the
phase to ROADMAP and map applicable REQUIREMENTS without duplicating acceptance.

An intake request alone does not authorize implementation. Record the real
instruction in Authorization; leave approval pending when execution is not
authorized. Keep inputs committed before runtime execution.
Continue through [phase-discuss](phase-discuss.md).

Do not create a separate issue-record lifecycle for bugs or documentation. A
small repair is a small phase; preserve its symptom, cause and regression proof.
