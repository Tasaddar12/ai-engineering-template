Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

# --text mode — plain-text overlay (no AskUserQuestion)

> **Lazy-loaded overlay.** Read this file from `.ai/gsd/workflows/discuss-phase.md`
> when `--text` is present in `$ARGUMENTS`, OR when
> `workflow.text_mode: true` is set in config (e.g., per-project default).

## Effect

When text mode is active, **do not use AskUserQuestion at all**. Instead,
present every question as a plain-text numbered list and ask the user to
type their choice number. Free-text input maps to the "Other" branch of
the equivalent AskUserQuestion call.

This is required for Claude Code remote sessions (`/rc` mode) where the
Claude App cannot forward TUI menu selections back to the host.

## Activation

- Per-session: pass `--text` flag to any command (e.g.,
  `/gsd:discuss-phase --text`)
- Per-project: `gsd_run query config-set workflow.text_mode true`

Text mode applies to ALL workflows in the session, not just discuss-phase.

## Question rendering

Replace this:
```text
AskUserQuestion(
  header="Layout",
  question="How should posts be displayed?",
  options=["Cards", "List", "Timeline"]
)
```

With this:
```text
Layout — How should posts be displayed?
  1. Cards
  2. List
  3. Timeline
  4. Other (type freeform)

Reply with a number, or describe your preference.
```

Wait for the user's reply at the normal prompt. Parse:
- Numeric reply → mapped to that option
- Free text → treated as "Other" — reflect it back, confirm, then proceed

## Empty-answer handling

The same answer-validation rules from the parent file apply: empty
responses trigger one retry, then a clarifying question. Do not proceed
with empty input.


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
