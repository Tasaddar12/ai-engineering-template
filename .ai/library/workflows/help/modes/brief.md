Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

<purpose>
One-liner refresher for returning users. Output ONLY the `<reference>` content below. No additions.
</purpose>

<reference>
**Workflow — top commands**

```text
/workflow:new-project           Initialize a project (greenfield)
/workflow:onboard               Onboard an existing codebase (brownfield)
/workflow:map-codebase          Refresh/map codebase intelligence
/workflow:plan-phase <N>        Create a phase plan
/workflow:execute-phase <N>     Execute a phase
/workflow:progress              Where am I, what's next
/workflow:quick                 Small ad-hoc task with Workflow guarantees
/workflow:fast "<task>"         Trivial inline task — no subagents
/workflow:debug "<symptom>"     Persistent debug session (survives /clear)
/workflow:capture               Save an idea / todo / note
/workflow:ship <N>              Open a PR from a completed phase
```

More: `/workflow:help` (default tour) · `/workflow:help --full` (everything) · `/workflow:help <topic>` (one section)
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
