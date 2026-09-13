# Runtime-Aware Subagent Dispatch (epic #2505 Phase 4 / #2508)

Workflow workflows dispatch specialized subagents by role (planner, executor,
verifier, …). On **named-dispatch runtimes** (Claude Code, OpenCode, Cursor,
Cline, … — every runtime whose descriptor declares `hostIntegration.dispatch.namedDispatch: true`), the role name dispatches the named subagent directly.

On **built-in-only runtimes** (kimi-code — three built-in subagents only:
`coder`, `explore`, `plan`; no custom registration per
`moonshotai.github.io/kimi-code/en/customization/agents`), a Workflow role name is
unknown and the dispatch must use the closest built-in.

## Resolution

Before dispatching a subagent by role, resolve the type for the current runtime
via the `resolve-dispatch-type` query. Pass the requested role name; the query
returns the name unchanged on named-dispatch runtimes and maps to the closest
built-in (`coder`/`explore`/`plan`) on kimi-code. The `|| echo` fallback
preserves named-dispatch behavior on older Workflow installs that lack the query.

The persona rides `${AGENT_SKILLS_<ROLE>}` (Phase 3 / #2510) regardless of the
resolved type — on non-Claude runtimes with no `agent_skills` config,
`workflow_run query agent-skills <role>` returns the installed agent prompt as
the block. So a coder dispatch with the planner persona injected gives kimi-code
the planner's behavior in the coder built-in's process.

## Suffix → built-in map

| Agent role suffix | Built-in | Rationale |
|---|---|---|
| `-planner`, `-roadmapper`, `-selector`, `-spec` | `plan` | Plans/designs; no file writes |
| `-researcher`, `-mapper`, `-checker`, `-verifier`, `-auditor`, `-analyzer`, `-synthesizer`, `-profiler`, `-curator`, `-classifier`, `-reviewer` | `explore` | Read-only investigation |
| everything else (`-executor`, `-fixer`, `-writer`, `-debugger`, …) | `coder` | General-purpose with full tool set |
| `general-purpose`, `general`, `default`, `sonnet`, `opus`, `haiku` | `coder` | Already-generic names |

## Why not a hook?

Kimi Code's documented PreToolUse hook API
(`moonshotai.github.io/kimi-code/en/customization/hooks`) supports only
`permissionDecision: allow|deny` on blockable events — it cannot rewrite the
dispatch payload's role field in flight. A PreToolUse-remap hook (the epic's
original "Option B") is therefore infeasible; this per-dispatch resolution
(Option A) is the documented-API-correct path.


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
