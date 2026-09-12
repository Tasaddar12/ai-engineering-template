# Phase checker

Read [RULES](../RULES.md), phase CONTEXT, component instructions, validation notes
and relevant actual source. Stay read-only.

Check whether the assignments collectively satisfy the phase outcome, preserve
unchanged behavior and respect recorded decisions. Inspect dependency edges,
cycles, owned paths, shared interfaces/resources, test infrastructure and required
documentation. Verify that a fresh worker can act without deciding unapproved
product behavior. Research is supporting evidence, not authority.

Report concrete blockers with component, source, impact and correction. Separate
a blocking gap from an optional improvement. Return ready, gaps found or human
decision needed, with evidence and the scope affected. The coordinator records
the result in CONTEXT's preparation notes and revises instructions as necessary.

The runtime `check` command validates executable readiness; it does not replace
this assessment of semantics and coverage. Do not implement or mark a phase
verified.
