Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

# --power mode — bulk question generation, async answering

> **Lazy-loaded.** Read this file from `.ai/library/workflows/discuss-phase.md` when
> `--power` is present in `$ARGUMENTS`. The full step-by-step instructions
> live in the existing `discuss-phase-power.md` workflow file (kept stable
> at its original path so installed `@`-references continue to resolve).

## Dispatch

```
Read @.ai/library/workflows/discuss-phase-power.md
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

This complete authoring guide retains its source content, examples, and methods.
Only recorded namespace/reference substitutions and explicit local conflict
corrections have been made. Source attribution and exact original hashes are
isolated in `.ai/library/THIRD-PARTY-NOTICES.md` and `PROVENANCE.json`.

Read `.ai/library/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/template-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The retained `config.json`, `/workflow:*` commands, tool
names, hooks, and Node CLI examples describe supporting source capabilities;
this import does not install or activate them. Source catalog pointers in examples
identify provenance, not executable command arguments. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
