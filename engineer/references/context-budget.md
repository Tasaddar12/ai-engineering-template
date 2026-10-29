# Context Budget Rules

Use context on the evidence that can change the decision or implementation.
This reference applies to planning, execution, review, and investigation; it
does not define a runtime context guard or authorize pausing work.

## Read and delegate deliberately

1. Read the assigned role and required inputs before acting. Expand reads when a
   decision, implementation detail, or verification claim depends on content
   beyond a summary.
2. Ask each agent to inspect its assigned source files directly instead of
   copying large files into a prompt. Include only the context needed to explain
   ownership, constraints, interfaces, and expected evidence.
3. For long outputs, begin with headings, status, conclusions, and evidence
   locations; read full sections when a claim needs inspection. Keep the
   required depth appropriate to the decision and the available context.
4. Route substantial independent work to the assigned specialist. The
   coordinator still owns integration and must verify outcomes against the
   required evidence, not just file existence or a completion claim.
5. Preserve enough context to finish verification, handoff, and the next-action
   report. If the conversation is getting crowded, summarize decisions,
   completed work, unresolved items, and exact evidence paths before continuing.

## Read depth by context window

Use the project's declared context window when it is available. A lower window
calls for more selective reading; a larger window permits fuller reads when
they help make a decision. In either case, read the complete source when the
claim depends on details that a summary could omit.

| Context window | Start with | Expand when |
|---|---|---|
| Below 500k tokens | Frontmatter, status, summaries, and relevant sections | The decision or check depends on body details |
| 500k tokens or more | Relevant summaries and source sections | Full bodies are useful for inline decisions or presentation |

## Context pressure signals

Watch for vague implementation claims, omitted procedure steps, and reports
that do not cover their stated acceptance criteria. These are prompts to inspect
the missing evidence or narrow the immediate task; they are not proof that work
is complete or a reason to skip verification.

## Phase sizing

Size plans around complete outcomes and their evidence. Make tasks small enough
that an implementer can understand the relevant source, make the change, and
verify it in one coherent slice. Split at real ownership, subsystem, dependency,
or verification boundaries. Keep prerequisite discovery separate from edits
when the findings could change scope or design. Do not split work solely to hit
a fixed task count or file count; do not combine independent changes merely to
fit one plan.

When uncertainty about scope or dependencies is high, inspect the relevant
source before committing to a plan shape. Include implementation, relevant
inputs, and verification output in the expected reading load, then leave room
for findings and repairs. An estimate can help compare plan shapes, but it is
advisory and does not replace acceptance criteria or evidence.
