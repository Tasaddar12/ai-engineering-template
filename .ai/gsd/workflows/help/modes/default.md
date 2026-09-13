Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

<purpose>
One-page newcomer-oriented tour of GSD Core. Output ONLY the `<reference>` content below. No additions.
</purpose>

<reference>
# GSD Core — Git. Ship. Done.

Plan-driven development for solo agentic work with Claude Code. GSD Core turns a vague idea into a hierarchical plan, then executes it phase by phase with state tracking and atomic commits.

## Start here (3 commands)

```text
/gsd:new-project        # Greenfield: questioning → research → requirements → roadmap
/gsd:onboard            # Existing codebase: map → ingest docs → initialize planning
/gsd:plan-phase 1       # Create a detailed plan for phase 1
/gsd:execute-phase 1    # Execute all plans in the phase
```

Existing codebase? Run `/gsd:onboard` to map the repo, ingest existing docs, and initialize planning safely.

## Common commands

| Command | Purpose |
|---|---|
| `/gsd:progress` | Where am I, what's next — also routes freeform intent with `--do "..."` |
| `/gsd:quick` | Small ad-hoc task with GSD guarantees (planning dir + atomic commit) |
| `/gsd:fast "<task>"` | Trivial inline change — no subagents, ≤3 file edits |
| `/gsd:discuss-phase <N>` | Capture vision and decisions before planning |
| `/gsd:debug "<symptom>"` | Persistent debug session, survives `/clear` |
| `/gsd:capture` | Save an idea, todo, note, seed, or backlog item |
| `/gsd:verify-work <N>` | Conversational UAT for a completed phase |
| `/gsd:ship <N>` | Open a PR from a completed phase |
| `/gsd:help --full` | Complete reference (every command, every flag) |

## Want more?

```text
/gsd:help --brief         # 10-line refresher of top commands
/gsd:help --full          # complete reference
/gsd:help <topic>         # one section only — see topics below
/gsd:help --brief <topic> # compact scoped lookup — signature + one-line summary
```

Topics: `workflow` · `planning` · `execute` · `quick` · `debug` · `capture` · `ship` · `config` · `milestones` · `spike` · `sketch` · `review` · `audit` · `progress`

## Update GSD

```bash
npx @opengsd/gsd-core@latest
```
</reference>


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
