<!-- workflow: complete-milestone; produces: MILESTONES.md, runtime milestone/state markers -->
<purpose>
Close an honestly delivered milestone through runtime-owned records after auditing every phase and accepted requirement. Preserve complete phase evidence; create no release tag and merge no branch here.
</purpose>
<required_reading>
@engineer/RULES.md
@engineer/references/template-contract.md
@engineer/templates/milestone.md
</required_reading>
<process>
<step name="init_context">
Read and execute engineer/workflows/_runtime-launcher.snippet.sh. Run init.complete-milestone and milestone.list. Resolve the explicitly selected milestone version/name or one unambiguous active target. Read its actual milestone_phases membership from the runtime; if unavailable, establish membership from authoritative milestone records rather than guessing by directory age or integer range. Stop when the target or membership cannot be established.
</step>
<step name="pre_close_artifact_audit">
For every target milestone phase, run init.phase-op and inspect the actual CONTEXT, plans, complete summaries, canonical passed/current VERIFICATION, required SECURITY/VALIDATION/UAT, issue relationships and provider delivery state. Show missing artifacts, open acceptance and deferred items before closeout. A roadmap checkbox is not sufficient proof. Never acknowledge all gaps or suppress an outstanding artifact solely to make readiness pass.
</step>
<step name="verify_readiness">
Require ready_to_complete evidence: every intended phase is actually verified and delivered, no unresolved acceptance/security/issue blocker remains, and outstanding requirements are either accepted complete or explicitly deferred through their owning records. A failed or pending check means not ready. There is no force/proceed-anyway path; report concrete blockers and preserve the milestone open.
</step>
<step name="requirements_completion">
**Requirements completion check (REQUIRED before presenting):**

Parse REQUIREMENTS.md traceability table:
- Count total v1 requirements vs checked-off (`[x]`) requirements
- Identify any non-Complete rows in the traceability table

Present:

```
Milestone: [Name, e.g., "v1.0 MVP"]

Includes:
- Phase 1: Foundation (2/2 plans complete)
- Phase 2: Authentication (2/2 plans complete)
- Phase 3: Core Features (3/3 plans complete)
- Phase 4: Polish (1/1 plan complete)

Total: {phase_count} phases, {total_plans} plans
Verification: {all_phases_verified ? "all phases verified" : "not ready"}
Requirements: {N}/{M} v1 requirements checked off
```

**If requirements incomplete** (N < M):

```
⚠ Unchecked Requirements:

- [ ] {REQ-ID}: {description} (Phase {X})
- [ ] {REQ-ID}: {description} (Phase {Y})
```


Route actual unchecked requirements to record_deferrals. Do not offer an acceptance waiver or count an unverified item as complete.
</step>
<step name="record_deferrals">
For each explicitly approved deferred item, run `engineer_run query state.add-deferred "${CATEGORY}" "${TEXT}" --status "Deferred" --milestone "${MILESTONE_NAME}"` and `engineer_run query requirements.set-status "${REQ_ID}" Deferred` for an actual mapped requirement. Preserve full wording, rationale and canonical issue evidence. A deferral changes scope only when the user explicitly approved that exact outcome; otherwise it stays a closeout blocker. Re-evaluate readiness after these record changes.
</step>
<step name="gather_stats">
Use actual milestone_phases for phase and plan counts. Gather commit range/date and Git diff statistics from the target milestone's known evidence. If the boundary cannot be established, say statistics are unavailable rather than scanning unrelated history or manufacturing counts. Do not count the whole repository's lines as milestone work.
</step>
<step name="extract_accomplishments">
Read each complete SUMMARY's `**Delivered:**` line and its acceptance/evidence in context. Preserve concrete delivered outcomes, important decisions and known gaps; source claims remain separate from canonical verification. Do not invent an accomplishment from a plan title or use a nonexistent summary-extract convention as evidence.
</step>
<step name="create_milestone_entry">
The runtime milestone.complete operation owns the MILESTONES entry and roadmap markers. Prepare the actual name, goal, phase membership, delivered accomplishments, dates, counts and deferred items before calling it; do not hand-render a competing entry.
</step>
<step name="complete_milestone">
Run `engineer_run query milestone.complete "${MILESTONE_NAME}" --confirm` only after readiness holds. Do not add archive-quick or release-map behavior. Preserve phase directories as evidence under the agreed runtime contract; explicit selected retirement belongs to clean-planning. If the runtime attempts an incompatible archival effect, stop with that contract mismatch rather than deleting or recreating phase evidence by hand.
</step>
<step name="review_entry">
Read the returned MILESTONES entry and authoritative runtime markers. Improve only narrative prose when it helps a human understand what shipped; preserve actual dates, counts, phase IDs, requirement outcomes and runtime-owned structure. Include concrete known gaps/deferred work and a narrative account of what remains, without launching another milestone or workflow.
</step>
<step name="write_retrospective">

**Append to living retrospective:**

Check for existing retrospective:
```bash
ls .planning/RETROSPECTIVE.md 2>/dev/null || true
```

**If exists:** Read the file, append new milestone section before the "## Cross-Milestone Trends" section.

**If doesn't exist:** Create from template at `engineer/templates/retrospective.md`.

**Gather retrospective data:**

1. From SUMMARY.md files: Extract key deliverables, one-liners, tech decisions
2. From VERIFICATION.md files: Extract verification scores, gaps found
3. From UAT.md files: Extract test results, issues found
4. From git log: Count commits, calculate timeline
5. From the milestone work: Reflect on what worked and what didn't

**Write the milestone section:**

```markdown
## Milestone: v{version} — {name}

**Shipped:** {date}
**Phases:** {phase_count} | **Plans:** {plan_count}

### What Was Built
{Extract from SUMMARY.md one-liners}

### What Worked
{Patterns that led to smooth execution}

### What Was Inefficient
{Missed opportunities, rework, bottlenecks}

### Patterns Established
{New conventions discovered during this milestone}

### Key Lessons
{Specific, actionable takeaways}

### Cost Observations
Record only measured values; unavailable model/session data stays unavailable.
- Model mix: {X}% opus, {Y}% sonnet, {Z}% haiku
- Sessions: {count}
- Notable: {efficiency observation}
```

**Update cross-milestone trends:**

If the "## Cross-Milestone Trends" section exists, update the tables with new data from this milestone.

**Commit:**
```bash
engineer_run query commit "docs: update retrospective for v${VERSION}" --files .planning/RETROSPECTIVE.md
```

</step>
<step name="update_state">
Use state.record-session for actual milestone closeout continuity. Use state.add-decision with explicit rationale/outcome only for a real consequential decision, not a fabricated decision describing every bookkeeping step. Never overwrite STATE sections directly.
</step>
<step name="git_commit">
Commit the actual changed milestone, roadmap, project, requirement, state and retrospective paths through engineer_run query commit. Do not delete REQUIREMENTS, overwrite ROADMAP, renumber phases, merge branches or tag releases. Run planning.validate only when permitted and keep its warnings warn-only; deferred validation is reported pending.
</step>
<step name="completion">
Report the actual milestone name/version, phases/plans, delivered outcomes, accepted deferrals, MILESTONES path and commit. State any preserved closeout limitation directly and stop. There is no command menu or automatic next milestone.
</step>
</process>
<milestone_naming>

**Version conventions:**
- **v1.0** — Initial MVP
- **v1.1, v1.2** — Minor updates, new features, fixes
- **v2.0, v3.0** — Major rewrites, breaking changes, new direction

**Names:** Short 1-2 words (v1.0 MVP, v1.1 Security, v1.2 Performance, v2.0 Redesign).

</milestone_naming>

<what_qualifies>

**Create milestones for:** Initial release, public releases, major feature sets shipped, before archiving planning.

**Don't create milestones for:** Every phase completion (too granular), work in progress, internal dev iterations (unless truly shipped).

Heuristic: "Is this deployed/usable/shipped?" If yes → milestone. If no → keep working.

</what_qualifies>
<anti_patterns>
Never force readiness, hand-create a competing milestone entry, delete phase evidence, reset numbering, delete requirement records, tag a release or merge a branch from milestone closeout.
</anti_patterns>
<success_criteria>
Every target phase and acceptance obligation was audited; actual deferrals were explicitly approved; runtime-owned closeout succeeded; complete evidence remains available; narrative history is accurate; and the exact records are committed with honest check outcomes.
</success_criteria>
