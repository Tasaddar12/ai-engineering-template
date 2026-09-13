Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

<purpose>
One-page newcomer-oriented tour of Workflow Core. Output ONLY the `<reference>` content below. No additions.
</purpose>

<reference>
# Workflow Core — Git. Ship. Done.

Plan-driven development for solo agentic work with Claude Code. Workflow Core turns a vague idea into a hierarchical plan, then executes it phase by phase with state tracking and atomic commits.

## Start here (3 commands)

```text
/workflow:new-project        # Greenfield: questioning → research → requirements → roadmap
/workflow:onboard            # Existing codebase: map → ingest docs → initialize planning
/workflow:plan-phase 1       # Create a detailed plan for phase 1
/workflow:execute-phase 1    # Execute all plans in the phase
```

Existing codebase? Run `/workflow:onboard` to map the repo, ingest existing docs, and initialize planning safely.

## Common commands

| Command | Purpose |
|---|---|
| `/workflow:progress` | Where am I, what's next — also routes freeform intent with `--do "..."` |
| `/workflow:quick` | Small ad-hoc task with Workflow guarantees (planning dir + atomic commit) |
| `/workflow:fast "<task>"` | Trivial inline change — no subagents, ≤3 file edits |
| `/workflow:discuss-phase <N>` | Capture vision and decisions before planning |
| `/workflow:debug "<symptom>"` | Persistent debug session, survives `/clear` |
| `/workflow:capture` | Save an idea, todo, note, seed, or backlog item |
| `/workflow:verify-work <N>` | Conversational UAT for a completed phase |
| `/workflow:ship <N>` | Open a PR from a completed phase |
| `/workflow:help --full` | Complete reference (every command, every flag) |

## Want more?

```text
/workflow:help --brief         # 10-line refresher of top commands
/workflow:help --full          # complete reference
/workflow:help <topic>         # one section only — see topics below
/workflow:help --brief <topic> # compact scoped lookup — signature + one-line summary
```

Topics: `workflow` · `planning` · `execute` · `quick` · `debug` · `capture` · `ship` · `config` · `milestones` · `spike` · `sketch` · `review` · `audit` · `progress`

## Update Workflow

```bash
npx @openworkflow/workflow-core@latest
```
</reference>


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
