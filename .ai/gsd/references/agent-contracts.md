# Agent Contracts

Completion markers and handoff schemas for all GSD agents. Workflows use these markers to detect agent completion and route accordingly.

This doc describes what IS, not what should be. Casing inconsistencies are documented as they appear in agent source files.

---

## Agent Registry

| Agent | Role | Completion Markers | Consumed by | Kind |
|-------|------|--------------------|--------------|------|
| gsd-ai-researcher | AI framework research | No marker (writes the AI-SPEC.md framework section via Edit) | `.ai/gsd/workflows/ai-integration-phase.md` reads the AI-SPEC.md section after the agent returns | artifact+query |
| gsd-planner | Plan creation | `## PLANNING COMPLETE`, `## OUTLINE COMPLETE`, `## PHASE SPLIT RECOMMENDED`, `## ⚠ Source Audit`, `## CHECKPOINT REACHED`, `## PLANNING INCONCLUSIVE`, `## REVISION_CONFLICT` | `.ai/gsd/workflows/plan-phase.md`, `.ai/gsd/workflows/plan-phase/steps/chunked-planning-mode.md`, `.ai/gsd/workflows/plan-review-convergence.md`, `.ai/gsd/workflows/quick.md`, `.ai/gsd/workflows/quick/steps/plan-checker-loop.md`, `.ai/gsd/workflows/verify-work.md` | sentinel-match |
| gsd-executor | Plan execution | `## PLAN COMPLETE`, `## CHECKPOINT REACHED` | `.ai/gsd/workflows/plan-phase.md`, `.ai/gsd/workflows/plan-phase/steps/chunked-planning-mode.md`, `.ai/gsd/agents/gsd-debug-session-manager.md`, `.ai/gsd/agents/gsd-debugger.md` | sentinel-match |
| gsd-phase-researcher | Phase-scoped research | `## RESEARCH COMPLETE`, `## RESEARCH BLOCKED` | `.ai/gsd/workflows/plan-phase.md`, `.ai/gsd/workflows/quick/steps/research-phase.md`, `.ai/gsd/agents/gsd-project-researcher.md` | sentinel-match |
| gsd-project-researcher | Project-wide research | `## RESEARCH COMPLETE`, `## RESEARCH BLOCKED` | `.ai/gsd/workflows/plan-phase.md`, `.ai/gsd/workflows/quick/steps/research-phase.md`, `.ai/gsd/agents/gsd-phase-researcher.md` | sentinel-match |
| gsd-plan-checker | Plan validation | `## VERIFICATION PASSED`, `## ISSUES FOUND` | `.ai/gsd/workflows/plan-phase.md`, `.ai/gsd/workflows/plan-phase/steps/stall-detection-helpers.md`, `.ai/gsd/workflows/quick/steps/plan-checker-loop.md`, `.ai/gsd/workflows/import.md`, `.ai/gsd/workflows/ui-phase.md`, `.ai/gsd/workflows/verify-work.md`, `.ai/gsd/agents/gsd-ui-checker.md` | sentinel-match |
| gsd-research-synthesizer | Multi-research synthesis | `## SYNTHESIS COMPLETE`, `## SYNTHESIS BLOCKED` (unconsumed: blocked-research return — spawners detect failure via the #222 SUMMARY.md-on-disk check, no dispatch branch keys on the marker) | `.ai/gsd/workflows/new-milestone.md`, `.ai/gsd/workflows/new-project.md` | sentinel-match |
| gsd-debugger | Debug investigation | `## DEBUG COMPLETE`, `## ROOT CAUSE FOUND`, `## CHECKPOINT REACHED`, `## INVESTIGATION INCONCLUSIVE`, `## TDD CHECKPOINT`, `## FIX REJECTED BY GUARDRAIL` | `.ai/gsd/agents/gsd-debug-session-manager.md`, `.ai/gsd/workflows/diagnose-issues.md`, `.ai/gsd/workflows/plan-phase.md`, `.ai/gsd/agents/gsd-executor.md` | sentinel-match |
| gsd-debug-session-manager | Debug checkpoint loop | `## DEBUG SESSION COMPLETE`, `## CONTINUE_REQUIRED` | `.ai/gsd/workflows/debug.md` | sentinel-match |
| gsd-roadmapper | Roadmap creation/revision | `## ROADMAP CREATED`, `## ROADMAP REVISED`, `## ROADMAP BLOCKED` | `.ai/gsd/workflows/new-milestone.md`, `.ai/gsd/workflows/new-project.md` | sentinel-match |
| gsd-ui-auditor | UI review | `## UI REVIEW COMPLETE` | `.ai/gsd/workflows/ui-review.md` | sentinel-match |
| gsd-dom-verifier | Live-DOM UAT verification | No marker (writes `{phase}-DOM-VERIFY.md` directly; the frontmatter `outcome` / `reason` scalars carry the verdict, and `could_not_look` is never conflated with `nothing_to_report`) | `{phase}-DOM-VERIFY.md` artifact, written by the `live-dom-uat` capability's `execute:wave:post` step dispatched from `.ai/gsd/workflows/execute-phase.md` | artifact+query |
| gsd-ui-checker | UI validation | `## ISSUES FOUND`, `## UI-SPEC VERIFIED` | `.ai/gsd/workflows/plan-phase.md`, `.ai/gsd/workflows/quick/steps/plan-checker-loop.md`, `.ai/gsd/workflows/ui-phase.md`, `.ai/gsd/workflows/verify-work.md`, `.ai/gsd/agents/gsd-plan-checker.md` | sentinel-match |
| gsd-ui-researcher | UI spec creation | `## UI-SPEC COMPLETE`, `## UI-SPEC BLOCKED`, `## REVISION_CONFLICT` | `.ai/gsd/workflows/ui-phase.md` | sentinel-match |
| gsd-verifier | Post-execution verification | `## Verification Complete` (unconsumed: Marker Rule 2 recorded decision — intentional title-case marker; completion is detected via the artifact route, nothing matches the marker) | `*-VERIFICATION.md` artifact + `gsd_run query verification.status` in `.ai/gsd/workflows/verify-work.md` | artifact+query |
| gsd-integration-checker | Cross-phase integration check | `## Integration Check Complete` (unconsumed: Marker Rule 2 recorded decision — intentional title-case marker; the auditor reads the inline report, nothing matches the marker) | `.ai/gsd/workflows/audit-milestone.md` reads the agent's inline return text directly (agent has no Write tool -- it cannot write an artifact) | structured-return |
| gsd-nyquist-auditor | Sampling audit | `## PARTIAL`, `## ESCALATE`, `## GAPS FILLED` (non-standard) | `.ai/gsd/workflows/validate-phase.md`, `.ai/gsd/workflows/secure-phase.md`, `.ai/gsd/agents/gsd-security-auditor.md` | sentinel-match |
| gsd-security-auditor | Security audit | `## OPEN_THREATS`, `## ESCALATE`, `## SECURED` (non-standard) | `.ai/gsd/workflows/secure-phase.md`, `.ai/gsd/workflows/validate-phase.md`, `.ai/gsd/agents/gsd-nyquist-auditor.md` | sentinel-match |
| gsd-codebase-mapper | Codebase analysis | No marker (writes docs directly) | `.planning/codebase/*.md` artifacts, checked via `ls`/`wc -l` in `.ai/gsd/workflows/map-codebase.md` | artifact+query |
| gsd-code-fixer | Applies code-review fixes | No marker (fix commits + REVIEW.md updates) | `.ai/gsd/workflows/code-review-fix.md` reads REVIEW.md resolution state + git log | artifact+query |
| gsd-code-reviewer | Source-code review | No marker (writes REVIEW.md) | `.ai/gsd/workflows/code-review.md` reads REVIEW.md | artifact+query |
| gsd-assumptions-analyzer | Assumption extraction | No marker (returns `## Assumptions` sections) | `.ai/gsd/workflows/discuss-phase-assumptions.md` reads the inline `## Assumptions` sections from the agent's return | structured-return |
| gsd-doc-classifier | Planning-doc classification | No marker (writes `.planning/intel/classifications/*.json`) | `.ai/gsd/workflows/ingest-docs.md` reads the classification JSON | artifact+query |
| gsd-doc-verifier | Doc validation | No marker (writes JSON to `.planning/tmp/`) | `.planning/tmp/verify-{doc_filename}.json` artifact, read by `.ai/gsd/workflows/docs-update.md` | artifact+query |
| gsd-doc-writer | Doc generation | No marker (writes docs directly) | generated doc files, consumed by `.ai/gsd/workflows/docs-update.md` and `.ai/gsd/workflows/docs-update/steps/dispatch-monorepo-packages.md` | artifact+query |
| gsd-domain-researcher | Domain research | No marker (writes the AI-SPEC.md domain section via Edit) | `.ai/gsd/workflows/ai-integration-phase.md` reads the AI-SPEC.md section after the agent returns | artifact+query |
| gsd-eval-auditor | Evaluation coverage audit | No marker (writes the REVIEW.md audit section) | `.ai/gsd/workflows/eval-review.md` reads REVIEW.md | artifact+query |
| gsd-eval-planner | Evaluation strategy design | No marker (writes the AI-SPEC.md evaluation section via Edit) | `.ai/gsd/workflows/ai-integration-phase.md` reads the AI-SPEC.md section after the agent returns | artifact+query |
| gsd-framework-selector | Framework decision matrix | No marker (returns the interactive decision matrix inline) | `.ai/gsd/workflows/ai-integration-phase.md` reads the returned matrix | structured-return |
| gsd-advisor-researcher | Advisory research | No marker (utility agent) | `.ai/gsd/workflows/discuss-phase/modes/advisor.md` reads the inline comparison table from the agent's return | structured-return |
| gsd-user-profiler | User profiling | No marker (returns JSON in analysis tags) | `.ai/gsd/workflows/profile-user.md` extracts the inline `<analysis>` JSON block from the agent's return | structured-return |
| gsd-intel-updater | Codebase intelligence analysis | No marker (`.planning/intel/*.json` artifacts) | `.planning/intel/*.json` artifacts, read via `gsd_run intel query` / `intel validate` (no `*.md` workflow currently spawns this agent -- see `docs/adr/22-plan-drift-guard.md`, "never auto-spawned") | artifact+query |
| gsd-mempalace-curator | Ship-time MemPalace curation | No marker (writes the session diary + cross-links) | `.ai/gsd/workflows/ship.md` reads the diary artifacts | artifact+query |
| gsd-pattern-mapper | Codebase pattern mapping | `## PATTERN MAPPING COMPLETE` | `.ai/gsd/workflows/plan-phase.md` (also spawned by `.ai/gsd/workflows/settings.md`) | sentinel-match |
| gsd-doc-synthesizer | Doc synthesis for `/gsd:ingest-docs` | No marker (SYNTHESIS.md and INGEST-CONFLICTS.md artifacts) | `.planning/intel/SYNTHESIS.md` and `.planning/INGEST-CONFLICTS.md` artifacts, read by `.ai/gsd/workflows/ingest-docs.md` | artifact+query |

## Marker Rules

1. **ALL-CAPS markers** (e.g., `## PLANNING COMPLETE`) are the standard convention
2. **Title-case markers in gsd-verifier and gsd-integration-checker are intentional as-is, not bugs — a recorded decision.** Their rows are `artifact+query`/`structured-return` (completion is detected through the row's `Kind` route), and the markers are carried as `(unconsumed: Marker Rule 2 recorded decision …)` annotations: an auditable exemption, never deleted and never silently passed. `## Synthesis Complete` in gsd-doc-synthesizer was NOT covered by this rule; #3565 deleted it deliberately because it case-collides with gsd-research-synthesizer's `## SYNTHESIS COMPLETE` and nothing matched it
3. **Non-standard markers** (e.g., `## PARTIAL`, `## ESCALATE`) in audit agents indicate partial results requiring orchestrator judgment
4. **`Kind` describes how a caller actually detects an agent's completion, and is exactly one of:**
   - `sentinel-match` -- a workflow, command, or another agent detects completion by an exact-case string match against a declared marker
   - `artifact+query` -- the agent writes a file (report, JSON, generated doc) and the caller reads or queries that artifact instead of matching any marker text
   - `structured-return` -- the agent has no way to write files (no `Write` tool) or simply doesn't; it returns parseable sections, a table, or JSON inline, and the caller reads that return text directly
5. Markers must appear as H2 headings (`## `) at the start of a line in the agent's final output
6. The `Consumed by` / `Kind` columns are machine-enforced by `check:contract-drift` (`scripts/check-contract-drift.cjs`), which cross-checks this table against what each `.ai/gsd/agents/*.md` file actually emits in-fence and what every `.ai/gsd/workflows/**`, `.ai/gsd/commands/**`, and `.ai/gsd/agents/**` file actually consumes. Update this table whenever an agent's return contract changes -- a stale row is a violation the check will report, not something to leave for later.
7. A marker entry annotated `(unconsumed: <reason>)` is emitted deliberately but matched by no workflow, command, or agent — a display/presentation format no orchestrator branch consumes (the `## ROADMAP DRAFT` header was the canonical case until #3797 folded its content into `## ROADMAP CREATED`). The check still verifies the marker is declared **and** emitted, and still counts it for case-collision purposes; only the consumer requirement is waived. Use it for display formats, never to silence a real orphan.

## Key Handoff Contracts

### Planner -> Executor (via PLAN.md)

| Field | Required | Description |
|-------|----------|-------------|
| Frontmatter | Yes | phase, plan, type, wave, depends_on, files_modified, autonomous, requirements |
| `<objective>` | Yes | What the plan achieves |
| `<tasks>` | Yes | Ordered task list with type, files, action, verify, acceptance_criteria |
| `<verification>` | Yes | Overall verification steps |
| `<success_criteria>` | Yes | Measurable completion criteria |

### Executor -> Verifier (via SUMMARY.md)

| Field | Required | Description |
|-------|----------|-------------|
| Frontmatter | Yes | phase, plan, subsystem, tags, key-files, metrics |
| Commits table | Yes | Per-task commit hashes and descriptions |
| Deviations section | Yes | Auto-fixed issues or "None" |
| Self-Check | Yes | PASSED or FAILED with details |

## Workflow Regex Patterns

Workflows match these markers to detect agent completion:

**plan-phase.md matches:**
- `## RESEARCH COMPLETE` / `## RESEARCH BLOCKED` (researcher output)
- `## PLANNING COMPLETE` (planner output)
- `## CHECKPOINT REACHED` (planner/executor pause)
- `## VERIFICATION PASSED` / `## ISSUES FOUND` (plan-checker output)

**execute-phase.md matches:**
- `## PHASE COMPLETE` (all plans in phase done)
- `## Self-Check: FAILED` (summary self-check)

> **NOTE:** `## PLAN COMPLETE` is the gsd-executor's completion marker but execute-phase.md does not regex-match it. Instead, it detects executor completion via spot-checks (SUMMARY.md existence, git commit state). This is intentional behavior, not a mismatch.


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
