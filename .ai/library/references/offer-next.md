<!--
  offer-next.md — extracted from execute-phase.md step "offer_next" (#2537).
  Eagerly @-referenced from execute-phase.md so runtime behavior is unchanged; the
  extraction restores byte-budget headroom the frozen ceiling exists to provide.
-->

**Exception:** If `gaps_found`, the `verify_phase_goal` step already presents the gap-closure path (`/workflow:plan-phase {X} --gaps`). No additional routing needed — skip auto-advance.

**No-transition check (spawned by auto-advance chain):**

Parse `--no-transition` flag from $ARGUMENTS.

**If `--no-transition` flag present:**

Execute-phase was spawned by plan-phase's auto-advance. Do NOT run transition.md.
After verification passes and roadmap is updated, return completion status to parent:

```
## PHASE COMPLETE

Phase: ${PHASE_NUMBER} - ${PHASE_NAME}
Plans: ${completed_count}/${total_count}
Verification: {Passed | Gaps Found}

[Include aggregate_results output]
```

STOP. Do not proceed to auto-advance or transition.

**If `--no-transition` flag is NOT present:**

**Auto-advance detection:**

1. Parse `--auto` flag from $ARGUMENTS
2. Read consolidated auto-mode (`active` = chain flag OR user preference; chain flag already synced in init step):
   ```bash
   AUTO_MODE=$(workflow_run query check auto-mode --pick active 2>/dev/null || echo "false")
   ```

**If `--auto` flag present OR `AUTO_MODE` is true (AND verification passed with no gaps):**

```
### AUTO-ADVANCING → TRANSITION

Phase {X} verified, continuing chain
```

Execute the transition workflow inline (do NOT use Agent — orchestrator context is ~10-15%, transition needs phase completion data already in context):

Read and follow `.ai/library/workflows/transition.md`, passing through the `--auto` flag so it propagates to the next phase invocation.

**If neither `--auto` nor `AUTO_MODE` is true:**

**STOP. Do not auto-advance. Do not execute transition. Do not plan next phase. Present options to the user and wait.**

**IMPORTANT: There is NO `/workflow-transition` command. Never suggest it. The transition workflow is internal only.**

Check whether CONTEXT.md already exists for the next phase:

```bash
ls .planning/phases/*{next}*/{next}-CONTEXT.md 2>/dev/null || echo "no-context"
```

If CONTEXT.md does **not** exist for the next phase, present:

```
## ✓ Phase {X}: {Name} Complete

/workflow:progress ${Workflow_WS} — see updated roadmap
/workflow:discuss-phase {next} ${Workflow_WS} — start here: discuss next phase before planning  ← recommended
/workflow:plan-phase {next} ${Workflow_WS} — plan next phase (skip discuss)
/workflow:execute-phase {next} ${Workflow_WS} — execute next phase (skip discuss and plan)
```

If CONTEXT.md **exists** for the next phase, present:

```
## ✓ Phase {X}: {Name} Complete

/workflow:progress ${Workflow_WS} — see updated roadmap
/workflow:plan-phase {next} ${Workflow_WS} — start here: plan next phase (CONTEXT.md already present)  ← recommended
/workflow:discuss-phase {next} ${Workflow_WS} — re-discuss next phase
/workflow:execute-phase {next} ${Workflow_WS} — execute next phase (skip planning)
```

Only suggest the commands listed above. Do not invent or hallucinate command names.


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
