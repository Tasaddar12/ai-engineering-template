Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

# --power mode — bulk question generation, async answering

> **Lazy-loaded.** Read this file from `.ai/gsd/workflows/discuss-phase.md` when
> `--power` is present in `$ARGUMENTS`. The full step-by-step instructions
> live in the existing `discuss-phase-power.md` workflow file (kept stable
> at its original path so installed `@`-references continue to resolve).

## Dispatch

```
Read @.ai/gsd/workflows/discuss-phase-power.md
```

Execute it end-to-end. Do not continue with the standard interactive steps.

## Summary of flow

The power user mode generates ALL questions upfront into machine-readable
and human-friendly files, then waits for the user to answer at their own
pace before processing all answers in a single pass.

1. Run the same phase analysis (gray area identification) as standard mode
2. Write all questions to
   `{phase_dir}/{padded_phase}-QUESTIONS.json` and
   `{phase_dir}/{padded_phase}-QUESTIONS.html`
3. Notify user with file paths and wait for a "refresh" or "finalize"
   command
4. On "refresh": read the JSON, process answered questions, update stats
   and HTML
5. On "finalize": read all answers from JSON, generate CONTEXT.md in the
   standard format

## When to use

Large phases with many gray areas, or when users prefer to answer
questions offline / asynchronously rather than interactively in the chat
session.

## Combination rules

- `--power --auto`: power wins. Power mode is incompatible with
  autonomous selection — its purpose is offline answering.
- `--power --chain`: after the power-mode finalize step writes
  CONTEXT.md, the chain auto-advance still applies (Read `chain.md`).


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
