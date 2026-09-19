# Discussion Log Template

Template for `.planning/phases/XX-name/{phase_num}-DISCUSSION-LOG.md` — audit trail of discuss-phase Q&A sessions.

**Purpose:** Software audit trail for decision-making. Captures all options considered, not just the selected one. Separate from CONTEXT.md which is the implementation artifact consumed by downstream agents.

**Audit record only.** The coordinator writes and updates this log. Downstream
research, planning and execution agents must not load it as instructions or add
it to `<required_reading>`; they read decisions in CONTEXT. The runtime checks
that the log exists and is nonempty, not whether its decisions are correct.

## Format

```markdown
# Phase [X]: [Name] - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** [ISO date]
**Phase:** [phase number]-[phase name]
**Areas discussed:** [comma-separated list]

---

## [Area 1 Name]

| Option | Description | Selected |
|--------|-------------|----------|
| [Option 1] | [Brief description] | |
| [Option 2] | [Brief description] | ✓ |
| [Option 3] | [Brief description] | |

**User's choice:** [Selected option or verbatim free-text response]
**Notes:** [Any clarifications or rationale provided during discussion]
**Recommendation evidence:** [Inspected source paths or primary documentation,
applicable versions, supported claims, and any unresolved evidence gaps]

---

## [Area 2 Name]

...

---

## Claude's Discretion

[Areas delegated to Claude's judgment — list what was deferred and why]

## Deferred Ideas

[Ideas mentioned but not in scope for this phase]

---

*Phase: XX-name*
*Discussion log generated: [date]*
```

## Rules

- Required for every phase discussion, including a short exchange. Create it at
  the first exchange; append updates after each exchange and before pausing.
- Record only actual discussion. Mark unanswered questions pending; never invent
  user choices, evidence or a retrospective conversation.
- Includes ALL options considered, not just the selected one
- Includes user's freeform notes and clarifications
- Clearly marked as audit-only, not an implementation artifact
- Does NOT interfere with CONTEXT.md generation or downstream agent behavior
- Committed alongside CONTEXT.md in the same git commit


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

Read this complete authoring guide, including its examples and methods.
Source attribution is available in `.ai/THIRD-PARTY-NOTICES.md`.

Read `.ai/agents/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/template-adaptation.md` for local runtime behavior,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. Only the documented local runtime commands are installed. Tool names and product
examples do not establish that a tool is available; inspect the actual project
configuration and host capabilities before using them. Bundled supporting methods provide local guidance for explicit assignments;
they do not install additional runtime features.
Local rules, recorded authorization, plan-declared ownership and verification
safeguards govern execution. Publication never merges.
<!-- LOCAL-ADOPTION:END -->
