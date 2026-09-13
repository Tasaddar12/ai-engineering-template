Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

# DISCUSSION-LOG.md template — for discuss-phase git_commit step

> **Lazy-loaded.** Read this file only inside the `git_commit` step of
> `.ai/gsd/workflows/discuss-phase.md`, immediately before writing
> `${phase_dir}/${padded_phase}-DISCUSSION-LOG.md`.

## Purpose

Audit trail for human review (compliance, learning, retrospectives). NOT
consumed by downstream agents — those read CONTEXT.md only.

## Template body

```markdown
# Phase [X]: [Name] - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** [ISO date]
**Phase:** [phase number]-[phase name]
**Areas discussed:** [comma-separated list]

---

[For each gray area discussed:]

## [Area Name]

| Option | Description | Selected |
|--------|-------------|----------|
| [Option 1] | [Description from AskUserQuestion] | |
| [Option 2] | [Description] | ✓ |
| [Option 3] | [Description] | |

**User's choice:** [Selected option or free-text response]
**Notes:** [Any clarifications, follow-up context, or rationale the user provided]

---

[Repeat for each area]

## Claude's Discretion

[List areas where user said "you decide" or deferred to Claude]

## Deferred Ideas

[Ideas mentioned during discussion that were noted for future phases]
```


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

The complete upstream body above is retained from GSD-Core at
`c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977`; only recorded reference substitutions
and explicit local conflict corrections have been made. See
`.ai/gsd/PROVENANCE.json` for exact source hashes and changes.

Read `.ai/gsd/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/gsd-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The upstream `config.json`, `/gsd:*` commands, tool
names, hooks, and Node CLI examples describe GSD's system; this import does not
install or activate that system. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
