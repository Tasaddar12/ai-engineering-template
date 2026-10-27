# Context Budget Rules

Standard rules for keeping orchestrator context lean. Reference this in workflows that spawn subagents or read significant content.

See also: `engineer/references/universal-anti-patterns.md` for the complete set of universal rules.

---

## Universal Rules

Every workflow that spawns agents or reads significant content must follow these rules:

1. Read your assigned role and all required inputs. Discover additional files only for a named question.
2. **Never** inline large files into subagent prompts -- tell agents to read files from disk instead
3. **Read depth scales with context window** -- check `context_window` in `.planning/config.yaml`:
   - At < 500000 tokens (default 200k): read only frontmatter, status fields, or summaries. Never read full SUMMARY.md, VERIFICATION.md, or RESEARCH.md bodies.
   - At >= 500000 tokens (1M model): MAY read full subagent output bodies when the content is needed for inline presentation or decision-making. Still avoid unnecessary reads.
4. **Delegate** heavy work to subagents -- the orchestrator routes, it doesn't execute
5. **Proactive warning**: If you've already consumed significant context (large file reads, multiple subagent results), warn the user: "Context budget is getting heavy. Consider checkpointing progress."

## Read Depth by Context Window

| Context Window | Subagent Output Reading | SUMMARY.md | VERIFICATION.md | PLAN.md (other phases) |
|---------------|------------------------|------------|-----------------|------------------------|
| < 500k (200k model) | Frontmatter only | Frontmatter only | Frontmatter only | Current phase only |
| >= 500k (1M model) | Full body permitted | Full body permitted | Full body permitted | Current phase only |

**How to check:** Read `.planning/config.yaml` and inspect `context_window`. If the field is absent, treat as 200k (conservative default).

## Context Degradation Tiers

Use context percentages as heuristics, not measured proof. Preserve the current assignment and evidence before context pressure threatens completion.

| Tier | Heuristic signal | Action |
|------|------------------|--------|
| Healthy | Inputs and outputs remain bounded | Continue within assigned scope |
| Growing | Repeated large reads or vague responses | Select narrower evidence and report the next uncertainty |
| Constrained | Required context cannot fit reliably | Write a measured handoff and stop dependent work safely |

Never use a mode flag to waive gates or infer acceptance.

## Context Degradation Warning Signs

Quality degrades gradually before panic thresholds fire. Watch for these early signals:

- **Silent partial completion** -- agent claims task is done but implementation is incomplete. Self-check catches file existence but not semantic completeness. Always verify agent output meets the plan's must_haves, not just that files exist.
- **Increasing vagueness** -- agent starts using phrases like "appropriate handling" or "standard patterns" instead of specific code. This indicates context pressure even before budget warnings fire.
- **Skipped steps** -- agent omits protocol steps it would normally follow. If an agent's success criteria has 8 items but it only reports 5, suspect context pressure.

The coordinator independently verifies semantic correctness with assigned specialists and behavioral evidence; file existence and worker self-attestation alone are insufficient.

## Tool schema cost

Enabled tool schemas and results consume context according to the actual Claude or Codex host. Do not assume every schema is injected on every turn or change account/tool configuration without the user's authorization. Select the narrowest relevant tool and return bounded evidence. Configuration of MCP services belongs to the host, not `.planning/config.yaml`.

Before a long operation, identify the tools required by its scope and avoid loading unrelated outputs. Keep source paths and exact citations so a continuation can retrieve them without carrying the whole repository in its prompt.

---

# Phase Sizing (planner)

## Advisory estimates

Use `estimate_scope` to explain outcome boundaries and likely read/change/check cost. Estimate from actual relevant source, not a fixed token percentage. Label uncertain numbers as advisory; no calibration command is assumed. Read the configured task cap and honor the assigned cap. A count inside the cap does not prove a coherent plan.

## Split signals

Split when a distinct outcome can be verified independently, a producer must finish before a consumer, or exact path/resource ownership requires serialization. Preserve contract-first, thin-slice delivery. Do not split merely because there are more than five files, a checkpoint is present or several subsystems participate in one outcome. Ask the coordinator to resolve a scope change; planners do not add or defer approved scope.

Good: a persistence contract and a dependent API consumer have an actual `depends_on` edge.
Bad: split DB, API and UI mechanically when the authorized outcome requires one end-to-end slice.

Read [planner guidance](planner-guidance.md) for outcome calibration.

See @engineer/references/planner-guidance.md for Granularity Calibration table (Coarse/Standard/Fine plans-per-phase).

## Evidence selection and continuation

Read complete templates before authoring their artifacts even when general read-depth guidance favors frontmatter. Workers read exact assignment paths; scouts return cited evidence, never children. Only the coordinator schedules specialist work. A context handoff records base/head revisions, completed and remaining work, dirty paths, pending gates and first continuation.
