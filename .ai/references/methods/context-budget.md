# Context Budget Rules

Standard rules for keeping orchestrator context lean. Reference this in workflows that spawn subagents or read significant content.

## Universal Rules

1. Read your assigned role, core rules and required assignment inputs. Do not assume
   the host auto-loaded them, and do not load every unrelated role.
2. Pass focused paths and revision-specific context to workers rather than copying
   entire repositories into prompts. Only the coordinator dispatches workers.
3. Select evidence using metadata and headings, then read the complete relevant
   record. Never omit evidence needed to assess an acceptance claim to save tokens.
4. Use bounded assignments and dependency handoffs to keep work coherent. Workers
   return committed results to the coordinator rather than starting nested workers.
5. When context pressure threatens reliable work, preserve decisions, current
   revision, evidence and remaining actions in the assigned handoff. Do not claim
   completion because context is low.

## Context Degradation Tiers

Treat these as rough planning heuristics, not measured quality guarantees or runtime settings:

| Tier | Approximate usage | Response |
|---|---|---|
| PEAK | 0-30% | Read the relevant evidence and establish interfaces. |
| GOOD | 30-50% | Keep assignments bounded and avoid duplicate reads. |
| DEGRADING | 50-70% | Reduce irrelevant context and prepare a precise handoff. |
| POOR | 70%+ | Preserve progress and resume with enough context for reliable work. |

## Context Degradation Warning Signs

Quality degrades gradually before panic thresholds fire. Watch for these early signals:

- **Silent partial completion** -- agent claims task is done but implementation is incomplete. Self-check catches file existence but not semantic completeness. Always verify agent output meets the plan's must_haves, not just that files exist.
- **Increasing vagueness** -- agent starts using phrases like "appropriate handling" or "standard patterns" instead of specific code. This indicates context pressure even before budget warnings fire.
- **Skipped steps** -- agent omits protocol steps it would normally follow. If an agent's success criteria has 8 items but it only reports 5, suspect context pressure.

A worker summary alone establishes neither semantic correctness nor completeness. Inspect outcome evidence and use independent verification against must_haves.truths.

## Tool Context Cost

Available tools and large outputs can consume context depending on the host.
Choose relevant tools and focused queries. Do not alter the user's host settings
or disable integrations solely for a planning task. If an actual host limitation
blocks work, report it with evidence; no external host manual is required to use
this method.

---

# Phase Sizing (phase-preparer)

## Estimate Emission

A plan may carry an optional advisory `estimate` block. It is the quantitative reason a phase must be sliced — tracer-first says *slice thin*, the estimate says *how thin, for this codebase*.

**Compute it:**
1. Sum `estimateTokens`-scale cost across the plan: implementation + the files each task reads + verification output. Roughly chars/4 over what the executor will actually touch.
2. If comparable historical measurements exist, cite them and state any correction factor. Otherwise label the estimate uncalibrated; there is no calibration CLI here.
3. Report measurement count and limitations. Never invent observed costs or claim self-rated confidence is measured history.

**Over budget?** The plan-checker flags a plan whose estimate exceeds the assignment's known context budget. This is advisory — it never blocks. When flagged, re-slice: a tracer plus expansion slices, each inside the budget. Prefer more, smaller plans over one that spends the agent's best early-context tokens and finishes degraded.

## Context Budget Rules

Plans should complete within ~50% context (not 80%). No context anxiety, quality maintained start to finish, room for unexpected complexity.

**Task sizing target: 2-3 tasks per plan, not a mandatory count.** Enforce `execution.max_tasks_per_component` when set; apply the mandatory split conditions in [phase-preparer](../../agents/phase-preparer.md) (`estimate_scope`) even when the numeric cap is null. The table below supplies sizing estimates, not permission to exceed the context handoff threshold.

| Context Weight | Tasks/Plan | Context/Task | Total |
|----------------|------------|--------------|-------|
| Light (CRUD, config) | 3 | ~10-15% | ~30-45% |
| Medium (auth, payments) | 2 | ~20-30% | ~40-50% |
| Heavy (migrations, multi-subsystem) | 1-2 | ~30-40% | ~30-50% |

## Split Signals

**Review for splitting when:**
- More than 3 tasks
- Multiple subsystems exceed a coherent thin end-to-end slice
- Any task with >5 file modifications
- Checkpoint + implementation in same plan
- Discovery + implementation in same plan

**CONSIDER splitting:** >5 files total, natural semantic boundaries, context cost estimate exceeds 40% for a single plan. Context size is not permission to remove required outcomes; propose a scope split to the coordinator.

See [planner-guidance.md](planner-guidance.md) for Granularity Calibration table (Coarse/Standard/Fine plans-per-phase).
