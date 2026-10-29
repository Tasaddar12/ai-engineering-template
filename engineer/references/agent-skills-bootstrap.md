# Agent Skills Self-Load (Bootstrap)

## When to run

In your mandatory init step — right after `mandatory-initial-read.md` / the
`Project skills` discovery, before any other work.

## Steps

1. **Dedup guard (MANDATORY).** Look at your own prompt. If it already contains an
   `<agent_skills>` block, the orchestrator already injected one — **skip self-load
   entirely.** Loading a second copy wastes context on runtimes where orchestrator-side
   injection also runs (e.g. Claude Code). The guard is what keeps the two seams from
   doubling the block.

2. **Query your configured skills.** Use **your own agent type**: the one your agent
   file states on its `agent_skills:` pointer line, as `(agent type: \`executor\`)`.
Do not read it from your frontmatter `name:`— Claude Code shows a subagent only the
body, and Codex keeps it in a TOML key. Run the
query with`--skills-only`, in the **same bash call** as the launcher so `engineer_run`is
defined when it runs. Substitute your type for`<your-agent-type>`:

   ```bash
   # 1. Launcher: paste the bash block from run-resolver.md here unless engineer_run
   # is already defined in this shell (@~/.claude/engineer/references/run-resolver.md).
   # 2. Query:
   _AGENT_SKILLS=$(engineer_run query agent-skills <your-agent-type> --skills-only)
   ```

   Not every agent file defines `engineer_run`, so supply it as above rather than assuming
   your init did. The query is read-only and idempotent. Its stderr and exit status stay
   visible, so a missing launcher or a failed query is never mistaken for "nothing
   configured".

3. **Read every listed skill.** The block emits entries as `@<path>/SKILL.md`
   includes — `Read` each one before starting work. If the block is empty, there is
   nothing to do (zero overhead).

## What the query returns, per runtime

| Call | Claude | Codex |
| ---- | ------ | ----- |
| `query agent-skills <type> --skills-only` (the self-load) | configured skills, or an empty block | configured skills, or an empty block |
| `query agent-skills <type>` (orchestrator-side `${AGENT_SKILLS_*}` injection) | configured skills, or an empty block | configured skills, or — when nothing is configured and the agent is installed — the agent's own **persona** |

On a non-Claude runtime the plain query can answer with the agent's whole persona.
`--skills-only` is what keeps the self-load from
reading your own persona back into your context as if it were a skills block. Never
run the query without it from inside an agent.

## What self-load does and does not cover

| Skill form | Self-loads? | Notes |
| ---------- | ----------- | ----- |
| Project-relative path (`skills/my-skill`) | ✅ everywhere | `Read` the `@`-include |
| Global personal (`global:<name>`) | ✅ everywhere | resolves to the runtime global skills dir, then `Read` |
| Plugin-provided (`global:<plugin>:<skill>`) | Claude only | emitted as a Skill-tool directive on Claude; **skipped with a warning on all other runtimes** — the plugin/Skill-tool model has no equivalent elsewhere. |

## Notes

- **Idempotent and read-only.** `query agent-skills` never mutates state; calling it
  twice (once by the orchestrator, once by the agent) is harmless because the dedup
  guard suppresses the second load.
- **Checkers / read-only agents.** Bash is universal across consumer agents, so
  self-load works for plan-checkers, verifiers, and auditors too; the bootstrap assumes
  no tool an agent lacks.
