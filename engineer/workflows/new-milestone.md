<!-- workflow: new-milestone; roles: phase-researcher, codebase-mapper; produces: PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md -->
<purpose>
Gather the next concrete goal, confirm requirement scope and allocate a continuous runtime-owned phase sequence. Preserve prior milestone evidence and project identity. Creating the milestone does not authorize phase implementation.
</purpose>
<required_reading>
@engineer/RULES.md
@engineer/references/questioning.md
@engineer/templates/requirements.md
@engineer/references/template-contract.md
</required_reading>
<model_selection>
Use phase-researcher or codebase-mapper only for actual evidence needs. Resolve exact role model/effort inline and omit inherit. Isolate artifact-writing workers, wait for confirmed stop and integrate committed complete evidence before using it.
</model_selection>
<process>
<step name="load_context">
Require the actual milestone name or gather it with the goal. Read and execute engineer/workflows/_runtime-launcher.snippet.sh. Run init.new-milestone with no invented positional options. Require existing PROJECT and ROADMAP; a missing identity belongs to onboarding. Read actual state, prior milestone entry, current roadmap and requirement scope. Preserve continuous numbering and completed history.
</step>
<step name="check_open_work">
Inspect actual open phases and sessions. Show incomplete work and offer close it first, explicitly start the new milestone anyway, or cancel. Do not silently archive or reset old phases. Starting anyway records the approved overlap and preserves every old phase's scope/evidence; it does not imply implementation authority for new phases.
</step>
<step name="gather_goal">
Ask what outcome the next milestone should deliver, for whom, why it matters now, which concrete capabilities and constraints changed, and what is explicitly excluded. Reuse already supplied context and preserve examples. Text mode renders numbered choices when needed; do not fabricate a reply or replace evidence with an unattended default.
</step>
<step name="confirm_version_and_scope">
## 3. Determine Milestone Version

- Parse last version from MILESTONES.md
- Suggest next version (v1.0 → v1.1, or v2.0 for major)
- Confirm with user

## 3.5. Verify Milestone Understanding

Before writing any files, present a summary of what was gathered and ask for confirmation.

```
### ► MILESTONE SUMMARY

**Milestone v[X.Y]: [Name]**

**Goal:** [One sentence]

**Target features:**
- [Feature 1]
- [Feature 2]
- [Feature 3]

**Key context:** [Any important constraints, decisions, or notes from questioning]
```

AskUserQuestion:
- header: "Confirm?"
- question: "Does this capture what you want to build in this milestone?"
- options:
  - "Looks good" — Proceed to write PROJECT.md
  - "Adjust" — Let me correct or add details

**If "Adjust":** Ask what needs changing (plain text, NOT AskUserQuestion). Incorporate changes, re-present the summary. Loop until "Looks good" is selected.

**If "Looks good":** Proceed to Step 4.


</step>
<step name="optional_research">
Offer bounded research or skip without persisting a new global preference. When selected, dispatch one phase-researcher with inline model/effort, exact questions, existing project/map evidence, current constraints and complete output ownership. Require cited sources and actual authorized technology checks before recommendations. A usable RESEARCH PARTIAL return preserves its limitations; wait for confirmed worker stop before integrating. There is no separate synthesizer or automatic follow-on phase implementation.
</step>
<step name="define_requirements">
## 9. Define Requirements

```
### ► DEFINING REQUIREMENTS
```

Read PROJECT.md: core value, current milestone goals, validated requirements (what exists).

**If research exists:** Read the complete relevant phase-researcher evidence and extract actual feature categories.

Present features by category:
```
## [Category 1]
**Table stakes:** Feature A, Feature B
**Differentiators:** Feature C, Feature D
**Research notes:** [any relevant notes]
```

**If no research:** Gather requirements through conversation. Ask: "What are the main things users need to do with [new features]?" Clarify, probe for related capabilities, group into categories.

**Scope each category** via AskUserQuestion (multiSelect: true, header max 12 chars):
- "[Feature 1]" — [brief description]
- "[Feature 2]" — [brief description]
- "None for this milestone" — Defer entire category

Track: Selected → this milestone. Unselected table stakes → future. Unselected differentiators → out of scope.

**Identify gaps** via AskUserQuestion:
- "No, research covered it" — Proceed
- "Yes, let me add some" — Capture additions

**Generate REQUIREMENTS.md:**
- v1 Requirements grouped by category (checkboxes, REQ-IDs)
- Future Requirements (deferred)
- Out of Scope (explicit exclusions with reasoning)
- Traceability section (empty, filled by roadmap)

**REQ-ID format:** `[CATEGORY]-[NUMBER]` (AUTH-01, NOTIF-02). Continue numbering from existing.

**Requirement quality criteria:**

Good requirements are:
- **Specific and testable:** "User can reset password via email link" (not "Handle password reset")
- **User-centric:** "User can X" (not "System does Y")
- **Atomic:** One capability per requirement (not "User can login and manage profile")
- **Independent:** Minimal dependencies on other requirements

Present FULL requirements list for confirmation:

```
## Milestone v[X.Y] Requirements

### [Category 1]
- [ ] **CAT1-01**: User can do X
- [ ] **CAT1-02**: User can do Y

### [Category 2]
- [ ] **CAT2-01**: User can do Z

Does this capture what you're building? (yes / adjust)
```

If "adjust": Return to scoping.


The explicit out-of-scope list is required. Continue the existing REQ sequence rather than restarting IDs at the new milestone. Preserve the complete requirements template and all actual examples/constraints. Read the requirements_path returned by init; commit that exact changed narrative path with engineer_run query commit when it forms a meaningful slice. Traceability ownership remains with runtime phase allocation.
</step>
<step name="create_milestone">
Run `engineer_run query milestone.create "${MILESTONE_NAME}" --goal "${MILESTONE_GOAL}"` after scope confirmation. Require the returned identity to agree with the approved name and goal. Never reset phase numbers, clear prior phases, or hand-write milestone markers in STATE/ROADMAP.
</step>
<step name="break_into_phases">
Break the agreed requirement set into coherent observable outcomes with explicit dependency boundaries. Run `engineer_run query phase.add "${PHASE_TITLE}" --goal "${PHASE_GOAL}" --requirements ...` for each actual phase; use runtime-allocated numbers/directories and supported dependency options. Preserve continuous numbering across milestones. Reconcile every requirement ID with the resulting traceability; report uncovered IDs rather than silently dropping them. Do not create plans or ask a roadmapper to rewrite the roadmap.
</step>
<step name="update_state">
Use the actual first allocated phase with state.begin-phase and record the milestone evolution through state.add-roadmap-evolution. Narrative project context may reflect the approved new goal; runtime-owned Key Decisions and tables use their verbs. Do not pre-close pending captured items or edit their phase linkage by hand.
</step>
<step name="git_commit">
Commit the complete changed PROJECT, REQUIREMENTS, ROADMAP and STATE records and new directories with exact paths through engineer_run query commit. Inspect runtime readback for allocated IDs and requirement coverage. Keep existing completed phase evidence intact.
</step>
<step name="completion">
Report milestone name/goal, explicit exclusions, allocated phase numbers/goals, requirement mapping, research evidence and pending questions. End after the concrete records and commits. No plans were created and implementation awaits an explicit instruction for the selected phase.
</step>
</process>
<anti_patterns>
Never reset numbering, clear or archive old phases implicitly, create plans during milestone definition, write roadmap structures by hand, retag pending items as resolved, or imply phase implementation authority.
</anti_patterns>
<success_criteria>
The actual goal and full requirements are confirmed, explicit exclusions exist, runtime-created milestone/phases preserve continuous numbering and prior evidence, state and traceability agree, and exact changed records are committed.
</success_criteria>
