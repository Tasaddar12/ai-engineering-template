# Discuss a phase

Agreement on scope or design is not permission to implement. Record execution
approval only from an explicit user instruction to implement this phase; follow
[phase authority](../RULES.md#phase-authority).

Read [RULES](../RULES.md), selected CONTEXT, project constraints and relevant
requirements. Use the source-search order below before asking implementation
questions. Create
`NN-DISCUSSION-LOG.md` from the discussion-log template at the first exchange;
append each later exchange rather than replacing earlier history.

## Phase selection and focused source search

1. Resolve the requested phase number or name to exactly one directory under
   `.planning/phases/`. List matching CONTEXT filenames; do not read every phase
   body to find the target. If no phase matches or several match, report the
   matches and ask which phase the user means; do not guess or create a phase.
2. Read the selected CONTEXT's Canonical References and Existing Code Insights
   first, then relevant supplied codebase maps. Confirm the named paths exist
   and the cited symbols and relationships still match current source. Treat
   missing paths, stale maps and unverified relationships as investigation leads.
3. Use `rg` within those exact files or directories first; use the host's Grep
   tool if `rg` is unavailable. Take search terms from the discussed behavior,
   entry point or symbols. Read the matching definitions
   and follow their imports, callers, state boundaries and relevant tests. A
   search hit alone is not evidence that the behavior runs.
4. If no useful source paths are recorded, start with filename/path discovery
   and the nearest relevant entry point. Use the `codebase-recon` skill when the
   entry point or affected flow remains unclear; scope it to that question.
   Broaden each content search only to answer a named unresolved question, and
   state that question and the next directory or dependency being inspected.
   Do not begin with repository-wide content dumps or load every codebase map.
5. Record confirmed repository-relative paths, relevant symbols, their purpose
   and the inspected revision under the existing CONTEXT code-insight categories.
   Record uncommitted source changes when they affect a finding. Replace stale
   entries after checking their replacements; do not maintain a separate index.
6. Reuse unchanged material already read in this session. Check whether its files
   changed after edits, integration or a checkout change; reopen affected sources
   and their relevant consumers. Reopen additional sections when a new question
   requires them. Never omit required core instructions or evidence to save tokens.

## Recommendations and questions

- Before recommending an approach, inspect the relevant code, manifests,
  configuration and version-matched primary documentation that support it.
  Validate compatibility, prerequisites and the claimed benefit. Cite the exact
  source or existing check evidence in CONTEXT and the discussion log. Run a
  focused check only when authorized; if a claim remains unverified, state the
  evidence gap and investigate it before recommending that option.
- Compare sufficient solutions by complexity, operational dependencies,
  maintenance, testability and the extensions required by the agreed scope.
  Prefer existing project behavior, standard-library or native capabilities,
  already-installed dependencies, then the minimum new implementation. Use
  existing extension points and explicit interfaces; do not add speculative
  abstractions or reduce required behavior to make an option look simpler.
- Recommend installing a new library or running an additional server/service
  only after documenting why the existing or dependency-free options cannot
  satisfy the agreed requirements and why the addition is the smallest sufficient
  solution. Explain its installation, operation and maintenance costs.
- In user-facing questions and recommendations, describe each referenced item
  in one sentence using its behavior or purpose. Do not use identifiers such as
  `D-15` or `AUTH-01` as labels or explanations. Keep identifiers in internal
  records for traceability; for example, say "Keep sign-in sessions on the server
  so credentials are not stored in the browser" rather than "According to D-15."

## Discussion record

1. Establish the observable outcome, included behavior and exclusions.
2. Identify consequential choices. Reuse settled decisions and distinguish areas
   the user delegated from choices requiring human resolution.
3. Write stable acceptance IDs such as A1. Preserve the exact intended behavior;
   broad labels such as "authentication works" are insufficient.
4. After every exchange, update CONTEXT and append the actual questions, all
   options considered, recommendation evidence, user replies and rationale to
   DISCUSSION-LOG. Mark unanswered questions pending; never invent a response.
   Link log entries to the corresponding CONTEXT decisions. Commit both records
   together before ending the turn, including when discussion pauses.
5. Record actual execution authorization and its boundaries. Mark approved only
   when the real instruction authorizes that scope. Pending choices identify
   what they block. While discussion is pending, continue bounded fact-finding;
   prepare independent component PLANs only after discussion is complete.
6. Record unrelated discoveries in Deferred with sources and reasons. A required
   unresolved behavior cannot be deferred out of the phase's completion criteria.

Set CONTEXT frontmatter `discussion: complete` only after the user has discussed
the current outcome, scope, acceptance and consequential choices and both records
capture that exchange. Leave `approval: pending` unless implementation was
explicitly authorized. A short discussion still requires a log; an existing plan
or implementation request cannot auto-complete discussion. For an earlier missing
log, recover actual conversation evidence or discuss the unresolved scope with
the user; do not fabricate a retrospective exchange.

Continue to [research](phase-research.md)
when uncertainty warrants it, or [prepare](phase-prepare.md) when the approach
is sufficiently understood. A changed approved target must be reconciled with
any active execution attempt before more dispatch.

## Template and downstream use

Read the complete [context template](../templates/context.md) and its good/bad
examples before authoring. Use domain-specific decision categories, numbered
decisions, canonical references with real paths, reusable code insights and
explicit deferred ideas. Preserve the user's locked decisions verbatim where
required; document delegated discretion separately. The researcher needs to know
what to investigate and the planner needs to know which choices are fixed.

Use [discussion-log](../templates/discussion-log.md) for every phase discussion
and [spec](../templates/spec.md) for a phase-level specification of desired
behavior. A phase specification is distinct from a current-behavior contract.
Add the [runtime fields](../runtime/TEMPLATE-CONTRACT.md) to the full context
output. The coordinator carries these decisions into the existing research and
preparation procedures; [adaptation](../runtime/README.md#template-runtime-behavior) resolves
local authority, host and storage differences.
