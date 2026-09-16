# Discussion Log Template

Template for `.planning/phases/XX-name/{phase_num}-DISCUSSION-LOG.md` — audit trail of discuss-phase Q&A sessions.

**Purpose:** Software audit trail for decision-making. Captures all options considered, not just the selected one. Separate from CONTEXT.md which is the implementation artifact consumed by downstream agents.

**NOT for LLM consumption.** This file should never be referenced in `<required_reading>` blocks or agent prompts.

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

- Generated automatically at end of every discuss-phase session
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
boundary, `.ai/references/template-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. Only the documented local runtime commands are installed. Tool names and product
examples do not establish that a tool is available; inspect the actual project
configuration and host capabilities before using them. Bundled supporting methods provide local guidance for explicit assignments;
they do not install additional runtime features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
