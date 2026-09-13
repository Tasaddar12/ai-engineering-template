<!--
  offer-next.md — extracted from execute-phase.md step "offer_next" (#2537).
  Eagerly @-referenced from execute-phase.md so runtime behavior is unchanged; the
  extraction restores byte-budget headroom the frozen ceiling exists to provide.
-->

**Exception:** If `gaps_found`, the `verify_phase_goal` step already presents the gap-closure path (`/gsd:plan-phase {X} --gaps`). No additional routing needed — skip auto-advance.

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
   AUTO_MODE=$(gsd_run query check auto-mode --pick active 2>/dev/null || echo "false")
   ```

**If `--auto` flag present OR `AUTO_MODE` is true (AND verification passed with no gaps):**

```
### AUTO-ADVANCING → TRANSITION

Phase {X} verified, continuing chain
```

Execute the transition workflow inline (do NOT use Agent — orchestrator context is ~10-15%, transition needs phase completion data already in context):

Read and follow `.ai/gsd/workflows/transition.md`, passing through the `--auto` flag so it propagates to the next phase invocation.

**If neither `--auto` nor `AUTO_MODE` is true:**

**STOP. Do not auto-advance. Do not execute transition. Do not plan next phase. Present options to the user and wait.**

**IMPORTANT: There is NO `/gsd-transition` command. Never suggest it. The transition workflow is internal only.**

Check whether CONTEXT.md already exists for the next phase:

```bash
ls .planning/phases/*{next}*/{next}-CONTEXT.md 2>/dev/null || echo "no-context"
```

If CONTEXT.md does **not** exist for the next phase, present:

```
## ✓ Phase {X}: {Name} Complete

/gsd:progress ${GSD_WS} — see updated roadmap
/gsd:discuss-phase {next} ${GSD_WS} — start here: discuss next phase before planning  ← recommended
/gsd:plan-phase {next} ${GSD_WS} — plan next phase (skip discuss)
/gsd:execute-phase {next} ${GSD_WS} — execute next phase (skip discuss and plan)
```

If CONTEXT.md **exists** for the next phase, present:

```
## ✓ Phase {X}: {Name} Complete

/gsd:progress ${GSD_WS} — see updated roadmap
/gsd:plan-phase {next} ${GSD_WS} — start here: plan next phase (CONTEXT.md already present)  ← recommended
/gsd:discuss-phase {next} ${GSD_WS} — re-discuss next phase
/gsd:execute-phase {next} ${GSD_WS} — execute next phase (skip planning)
```

Only suggest the commands listed above. Do not invent or hallucinate command names.


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
