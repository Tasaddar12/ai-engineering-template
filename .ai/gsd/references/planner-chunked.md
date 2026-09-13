# Chunked Mode Return Formats

Used when `plan-phase` spawns `gsd-planner` with `CHUNKED_MODE=true` (triggered by `--chunked`
flag or `workflow.plan_chunked: true` config). Splits the single long-lived planner Task into
shorter-lived Tasks to bound the blast radius of Windows stdio hangs.

## Modes

### outline-only

Write **only** `{PHASE_DIR}/{PADDED_PHASE}-PLAN-OUTLINE.md`. Do not write any PLAN.md files.
Return:

```markdown
## OUTLINE COMPLETE

**Phase:** {phase-name}
**Plans:** {N} plan(s) in {M} wave(s)

| Plan ID | Objective | Wave | Depends On | Requirements |
|---------|-----------|------|-----------|-------------|
| {padded_phase}-01 | [brief objective] | 1 | none | REQ-001, REQ-002 |
| {padded_phase}-02 | [brief objective] | 1 | none | REQ-003 |
```

The orchestrator reads this table, groups rows by `Wave` (ascending, blank treated as `1`), then
spawns one single-plan Task per row — one Wave at a time, serially across Waves. Within a Wave,
Tasks are spawned one at a time by default, or together (`run_in_background=true` on each, issued
in one message) when `planning.chunked_parallel: true` and the host's negotiated dispatch capacity
supports it (#3777; see `.ai/gsd/workflows/plan-phase/steps/chunked-planning-mode.md` §8.5.2).

### single-plan

Write **exactly one** `{PHASE_DIR}/{plan_id}-PLAN.md`. Do not write any other plan files.
Return:

```markdown
## PLAN COMPLETE

**Plan:** {plan-id}
**Objective:** {brief}
**File:** {PHASE_DIR}/{plan-id}-PLAN.md
**Tasks:** {N}
```

The orchestrator verifies the file exists on disk after each return, commits it, then moves
to the next plan entry from the outline.

## Resume Behaviour

If the orchestrator detects that `PLAN-OUTLINE.md` already exists (from a prior interrupted
run), it skips the outline-only Task and goes directly to single-plan Tasks, skipping any
`{plan_id}-PLAN.md` files that already exist on disk.


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
