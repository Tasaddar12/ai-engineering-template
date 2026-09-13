## Converge Dispatch (Background)

If `PLAN_STRATEGY=converge`, print: `◆ Spawning background plan-convergence loop for phase ${PHASE_NUM}... (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)`

```
Agent(
  description="Plan convergence phase ${PHASE_NUM}: ${PHASE_NAME}",
  run_in_background=true,
  prompt="Run plan convergence for phase ${PHASE_NUM}: Skill(skill=\"workflow-plan-review-convergence\", args=\"${PHASE_NUM} ${CONVERGENCE_ARGS}\")"
)
```


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
