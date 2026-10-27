<!-- workflow: discuss-phase; produces: CONTEXT.md, DISCUSSION-LOG.md -->
<purpose>
Extract implementation decisions that downstream agents need. Analyze the phase to identify gray areas, let the user choose what to discuss, then deep-dive each selected area until satisfied.

You are a thinking partner, not an interviewer. The user is the visionary — you are the builder. Your job is to capture decisions that will guide research and planning, not to figure out implementation yourself.
</purpose>

<authority>
Discuss every phase before planning. Record only actual questions, presented options, evidence, replies and explicitly delegated decisions. Discussion completion never grants implementation permission. A recommendation, mode flag, recorded plan or readiness claim cannot authorize execution.
</authority>


<required_reading>
@~/.claude/engineer/references/domain-probes.md
@~/.claude/engineer/references/gate-prompts.md
@~/.claude/engineer/references/universal-anti-patterns.md
</required_reading>

<progressive_disclosure>
Load shared steps in this file. Load `engineer/workflows/discuss-phase/modes/all.md` for `--all`, `modes/auto.md` for `--auto`, `modes/text.md` before questions when `--text` or configured text mode is active, and `modes/default.md` for the ordinary discussion loop. Load context, checkpoint and discussion-log templates when their artifacts are written. Do not load unrelated mode files.
</progressive_disclosure>

<downstream_awareness>
**CONTEXT.md feeds into:**

1. **phase-researcher** — Reads CONTEXT.md to know WHAT to research
2. **planner** — Reads CONTEXT.md to know WHAT decisions are locked

**Your job:** Capture decisions clearly enough that downstream agents can act on them without asking the user again.
**Not your job:** Figure out HOW to implement. That's what research and planning do with the decisions you capture.
</downstream_awareness>

<philosophy>
**User = founder/visionary. Claude = builder.**

The user knows: how they imagine it working, what it should look/feel like, what's essential vs nice-to-have, specific behaviors or references they have in mind.

The user doesn't know (and shouldn't be asked): codebase patterns (researcher reads the code), technical risks (researcher identifies these), implementation approach (planner figures this out), success metrics (inferred from the work).

Ask about vision and implementation choices. Capture decisions for downstream agents.
</philosophy>

<scope_guardrail>
**CRITICAL: No scope creep.** The phase boundary comes from ROADMAP.md and is FIXED. Discussion clarifies HOW to implement what's scoped, never WHETHER to add new capabilities.

**Allowed (clarifying ambiguity):** "How should posts be displayed?" (layout), "What happens on empty state?" (within the feature).

**Not allowed (scope creep):** "Should we also add comments?" / "What about search/filtering?" / "Maybe include bookmarking?" — those are new capabilities and belong in their own phase.

**Heuristic:** Does this clarify how we implement what's already in the phase, or does it add a new capability that could be its own phase?

**When user suggests scope creep:**
```
"[Feature X] would be a new capability — that's its own phase.
Want me to note it for the roadmap backlog?

For now, let's focus on [phase domain]."
```

Capture the idea in a "Deferred Ideas" section. Don't lose it, don't act on it.
</scope_guardrail>

<gray_area_identification>
Gray areas are **implementation decisions the user cares about** — things that could go multiple ways and would change the result.

1. Read the phase goal from ROADMAP.md
2. Understand the domain — something users SEE / CALL / RUN / READ / something being ORGANIZED — and let that drive what kinds of decisions matter
3. Generate phase-specific gray areas (not generic categories)

**Don't use generic category labels** (UI, UX, Behavior). Generate specific gray areas. Examples:

```
Phase: "User authentication"     → Session handling, Error responses, Multi-device policy, Recovery flow
Phase: "Organize photo library"  → Grouping criteria, Duplicate handling, Naming convention, Folder structure
Phase: "CLI for database backups"→ Output format, Flag design, Progress reporting, Error recovery
Phase: "API documentation"       → Structure/navigation, Code examples depth, Versioning approach, Interactive elements
```

**Claude handles these (don't ask):** technical implementation details, architecture patterns, performance optimization, scope (roadmap defines this).
</gray_area_identification>

<answer_validation>
**IMPORTANT: Answer validation** — After every AskUserQuestion call, if the response is empty/whitespace-only:

- **"Other" with empty text** (the user wants to type freeform): output `"What would you like to discuss?"`, STOP generating, wait for the user's next message, then reflect it back and continue. Do NOT retry AskUserQuestion or call any tools.
- **Any other empty response:** retry once with the same parameters; if still empty, present options as a plain-text numbered list. Never proceed with empty input.

**Text mode** (`--text` or `workflow.text_mode: true`): follow `engineer/workflows/discuss-phase/modes/text.md` — do not use AskUserQuestion at all.
</answer_validation>

<process>

<step name="initialize">
Require a phase identifier. Parse only `--all`, `--auto` and `--text`; reject unsupported options without silently changing their meaning. Read and execute `engineer/workflows/_runtime-launcher.snippet.sh`, then run `engineer_run query phase.locate "${PHASE_NUMBER}"`. Stop on a missing or inconsistent phase and report the missing record with `/progress` as the inspection route. Use the locator's quoted `worktree` path; never guess a directory from the phase name. Run `engineer_run query init.phase-op "${PHASE_NUMBER}"` there. Read `phase_found`, actual `phase_dir`, `padded_phase`, `goal`, `text_mode`, `artifact_files`, grouped `artifacts`, existing *_path fields and `state`. Apply response_language to prose only. If `--auto` is present, load its mode before `check_existing`; `--all` selects all areas; text mode changes rendering, not authority.
</step>

<step name="check_blocking_antipatterns" priority="first">
**MANDATORY — Check for blocking anti-patterns before any other work.**

Look for a `.continue-here.md` in the current phase directory:

```bash
ls ${phase_dir}/.continue-here.md 2>/dev/null || true
```

If `.continue-here.md` exists, parse its "Critical Anti-Patterns" table for rows with `severity` = `blocking`.

**If one or more `blocking` anti-patterns are found:** the agent must demonstrate understanding of each by answering all three questions for each one:
1. **What is this anti-pattern?** — Describe it in your own words.
2. **How did it manifest?** — Explain the specific failure that caused it to be recorded.
3. **What structural mechanism (not acknowledgment) prevents it?** — Name the concrete step or enforcement mechanism that stops recurrence.

Write these answers inline before continuing. If a blocking anti-pattern cannot be answered from the context in `.continue-here.md`, stop and ask the user for clarification.

**If no `.continue-here.md` exists, or no `blocking` rows are found:** Proceed directly to `open_session`.
</step>

<step name="open_session">
Run `engineer_run query session.status` and inspect the locator's session lineage. Reuse the matching open phase session. Adopt an already named clean isolated checkout with `engineer_run query session.adopt phase "${PHASE_NUMBER}"` only when it is the intended session and ownership is established; otherwise run `engineer_run query session.open phase "${PHASE_NUMBER}"`. Never infer adoption from the current branch alone. Stop on a failed result. Read the returned worktree, branch, base and status; `cd "${worktree}"`, then re-run `engineer_run query init.phase-op "${PHASE_NUMBER}"` in that checkout. Report the session branch/path in one line. Leave the session open; do not deliver it here. Continue to `check_spec`.
</step>

<step name="check_spec">
Derive ordinary SPEC presence from actual artifact_files ending -SPEC.md and exclude -UI-SPEC.md. Use a computed SPEC entry only when the bundle actually emits it. Do not assume a spec_path field or confuse a UI artifact with the requirements spec. When present, read that exact SPEC in full, count its numbered requirements, and preserve its boundaries, constraints and acceptance as locked requirements. Display the requirement count and discuss implementation decisions only. `*-UI-SPEC.md` is a separate UI contract. When absent, proceed without inventing locked requirements.
</step>

<step name="check_existing">
Check if CONTEXT.md already exists using `has_context` from init.

```bash
ls ${phase_dir}/*-CONTEXT.md 2>/dev/null || true
```

**If exists:**

**If `--auto`:** Auto-select "Update it" — load existing context and continue to `analyze_phase`. Log: `[auto] Context exists — updating with auto-selected decisions.`

**Otherwise:** AskUserQuestion (header: "Context"; question: "Phase [X] already has context. What do you want to do?"; options: "Update it" / "View it" / "Skip"). Branch accordingly.

**If doesn't exist:**

Check for an interrupted discussion checkpoint:
```bash
ls ${phase_dir}/*-DISCUSS-CHECKPOINT.json 2>/dev/null || true
```

If a checkpoint file exists:

**If `--auto`:** Auto-select "Resume" — load checkpoint and continue from last completed area.

**Otherwise:** AskUserQuestion (header: "Resume"; question: "Found interrupted discussion checkpoint ({N} areas completed out of {M}). Resume from where you left off?"; options: "Resume" / "Start fresh"). On "Resume", parse the checkpoint JSON, load `decisions` into the internal accumulator, set `areas_completed` to skip those areas, continue to `present_gray_areas` with only the remaining areas. On "Start fresh", delete the checkpoint and continue.

Check `has_plans` and `plan_count` from init. **If `has_plans` is true:**

**If `--auto`:** Auto-select "Continue and replan after". Log: `[auto] Plans exist — continuing with context capture, will replan after.`

**Otherwise:** AskUserQuestion (header: "Plans exist"; question: "Phase [X] already has {plan_count} plan(s) created without user context. Your decisions here won't affect existing plans unless you replan."; options: "Continue and replan after" / "View existing plans" / "Cancel"). Branch accordingly.

**If `has_plans` is false:** Continue to `load_prior_context`.
</step>

<step name="load_prior_context">
Read PROJECT.md and REQUIREMENTS.md and use INIT `state` for current position and decisions. Resolve prior phases from `engineer_run query roadmap.analyze`; read at most the three most recent prior CONTEXT files. Do not invent a separate decisions index. Extract actual locked preferences, specific references and established patterns. Build `<prior_decisions>` with Project-Level and From Prior Phases sections. Use it to avoid re-asking settled questions, annotate choices with the earlier decision, and flag real conflicts. If prior context is absent, continue without it.
</step>

<step name="cross_reference_todos">
Run `engineer_run query todo.match-phase "${PHASE_NUMBER}"` and inspect actual explicitly assigned matches. Preserve exact file names, titles, areas and canonical issue relationships. If the runtime returns no matches, skip without inventing relevance scores. Present each actual match and ask which to fold; preserve Folded Todos filenames in CONTEXT decisions and Reviewed Todos in deferred context. In --auto mode, only explicit phase assignments or a genuinely emitted numeric score at least 0.4 may be folded automatically; log the actual evidence and selection. A missing score is not zero and not an inferred match. Keep every folded item pending until guarded post-merge reconciliation.
</step>

<step name="scout_codebase">
Lightweight scan of existing code to inform gray area identification (~10% context).

Read `@~/.claude/engineer/references/scout-codebase.md` — it contains the phase-type→map selection table, single-read rule, no-maps fallback, and `<codebase_context>` output schema. Then execute:
1. `ls .planning/codebase/*.md` to find existing maps
2. Select 2–3 maps via the reference's table; or grep fallback if none exist
3. Build internal `<codebase_context>` per the reference's output schema
</step>

<step name="analyze_phase">
Analyze the phase to identify gray areas. Use both `prior_decisions` and `codebase_context` to ground the analysis.

1. **Domain boundary** — What capability is this phase delivering? State it clearly.

1b. **Initialize canonical refs accumulator** — Start building `<canonical_refs>` for CONTEXT.md. Sources:
   - **Now:** Copy `Canonical refs:` from ROADMAP.md for this phase. Expand each to a full relative path. Check REQUIREMENTS.md and PROJECT.md for specs/ADRs referenced.
   - **`scout_codebase`:** If existing code references docs (e.g., comments citing ADRs), add those.
   - **`discuss_areas`:** When the user says "read X", "check Y", or references any doc/spec/ADR — add it immediately. These are often the MOST important refs.

   This list is MANDATORY in CONTEXT.md. Every ref must have a full relative path. If no external docs exist, note that explicitly.

2. **Check prior decisions** — Scan `<prior_decisions>` for already-decided gray areas; mark them pre-answered.

2b. **SPEC.md awareness** — If `spec_loaded = true`: `<locked_requirements>` are pre-answered (Goal, Boundaries, Constraints, Acceptance Criteria). Do NOT generate gray areas about WHAT to build or WHY. Only generate gray areas about HOW to implement. When presenting, include: "Requirements are locked by SPEC.md — discussing implementation decisions only."

3. **Gray areas** — For each relevant category, identify 1-2 specific ambiguities that would change implementation. Annotate with code context where relevant.

4. **Settled-area assessment** — If the phase has no meaningful undecided gray areas, record the existing evidence and actual confirmation rather than fabricate a question sequence. Every phase still needs a genuine discussion record before planning.

</step>

<step name="present_gray_areas">
Present the domain boundary, prior decisions, and gray areas to the user.

```
Phase [X]: [Name]
Domain: [What this phase delivers — from your analysis]

We'll clarify HOW to implement this. (New capabilities belong in other phases.)

[If prior decisions apply:]
**Carrying forward from earlier phases:**
- [Decision from Phase N that applies here]
```

**If `--auto` or `--all`** (per `modes/auto.md` or `modes/all.md`): Auto-select ALL gray areas. Log: `[--auto/--all] Selected all gray areas: [list area names].` Skip the AskUserQuestion below and continue directly to `discuss_areas` with all areas selected.

**Otherwise, use AskUserQuestion (multiSelect: true):**
- header: "Discuss"
- question: "Which areas do you want to discuss for [phase name]?"
- options: 3-4 phase-specific gray areas, each with a concrete label (not generic), 1-2 questions in description, and code-context / prior-decision annotations:
  ```
  ☐ Layout style — Cards vs list vs timeline?
    (You already have a Card component with shadow/rounded variants. Reusing it keeps the app consistent.)

  ☐ Loading behavior — Infinite scroll or pagination?
    (You chose infinite scroll in Phase 4. useInfiniteQuery hook already set up.)
  ```

**Do NOT include a "skip" or "you decide" option.** User ran this command to discuss — give real choices.

Continue to `discuss_areas` with the selected areas.
</step>

<step name="discuss_areas">
Use `engineer/workflows/discuss-phase/modes/default.md` for four focused single-question turns per area followed by the continue/next-area choice. `--auto` selects and logs recommended options in one pass; it never simulates a human reply. Apply `modes/text.md` only as the question-rendering overlay when needed.

All modes preserve the universal rules below.

**Universal rules (apply to every mode):**

- **Canonical ref accumulation** — when the user references a doc/spec/ADR during any answer, immediately Read it (or confirm it exists) and add it to the canonical refs accumulator with full relative path. Use what you learned to inform subsequent questions. These docs are often MORE important than ROADMAP.md refs because the user specifically wants downstream agents to follow them.
- **Scope creep** — if user mentions something outside the phase domain, capture as deferred idea and redirect.
- **Incremental checkpoint** — after each area completes, write `${phase_dir}/${padded_phase}-DISCUSS-CHECKPOINT.json`. Read `engineer/workflows/discuss-phase/templates/checkpoint.json` for the schema. The checkpoint is structured state, not the canonical CONTEXT.md (`write_context` produces the canonical output). On session resume, the parent's `check_existing` step detects the checkpoint and offers to resume.
- **Discussion log accumulation** — for each question asked, accumulate area name, options presented, user's selection, follow-up notes. Used by `git_commit` to write DISCUSSION-LOG.md.
</step>

<step name="write_context">
Create CONTEXT.md and DISCUSSION-LOG.md.

DISCUSSION-LOG.md is required evidence of the actual discussion. Record every actual question, options, evidence, reply, follow-up and delegated choice. Never manufacture a user answer or a research result. Downstream phase-researcher and planner use CONTEXT.md; the log preserves the audit trail.

**Resolve the actual phase directory:** Use phase_dir from the successful locator and phase packet. Require it to exist and belong to this phase/session. A missing directory is a blocker to resolve through phase management, not a guessed mkdir operation.

**File location:** `${phase_dir}/${padded_phase}-CONTEXT.md`

**Read the CONTEXT.md template now (lazy-loaded):**
```
Read(engineer/workflows/discuss-phase/templates/context.md)
```

The template documents variable substitutions and conditional sections. Substitute live values for `[X]`, `[Name]`, `[date]`, `${padded_phase}`, `{N}`. Include `<spec_lock>` only when `spec_loaded = true`. Include "Folded Todos" / "Reviewed Todos" subsections only when the `cross_reference_todos` step folded or reviewed todos.

**SPEC.md integration** — If `spec_loaded = true`:
- Add the `<spec_lock>` section immediately after `<domain>`.
- Add the SPEC.md file to `<canonical_refs>` with note "Locked requirements — MUST read before planning".
- Do NOT duplicate requirements text from SPEC.md into `<decisions>` — agents read SPEC.md directly.
- The `<decisions>` section contains only implementation decisions from this discussion.

Write the file.
</step>

<step name="confirm_creation">
Show the created CONTEXT and DISCUSSION-LOG paths, the decisions captured by area, explicitly delegated discretion and deferred ideas. Keep unrelated ideas out of the phase scope and do not create new todos from them. End with: "Planning and implementation await your instruction." Do not launch another workflow from discussion completion.
</step>

<step name="record_decisions">
Record decisions that outlive this phase through `engineer_run query state.add-decision "${DECISION}" --rationale "${RATIONALE}" --outcome "Accepted"`. Keep a small set of consequential decisions; discussion details stay in CONTEXT. Before recommending a technology, run an authorized targeted spike or check and record what actually ran, its outcome and limitations. If that execution is deferred, leave the choice unvalidated and state the pending evidence rather than calling it accepted on technical grounds. Do not rerun a check the user explicitly postponed.
</step>

<step name="git_commit">
Read `engineer/workflows/discuss-phase/templates/discussion-log.md` in full and write the real accumulator to `${phase_dir}/${padded_phase}-DISCUSSION-LOG.md`. Require it before committing. Preserve the full context template, actual decisions, canonical references, folded pending items and deferred ideas. Remove an obsolete checkpoint only after its contents are accounted for in the canonical context/log. Commit the exact CONTEXT, DISCUSSION-LOG, PROJECT Key Decisions and STATE paths with `engineer_run query commit "docs(${padded_phase}): record phase discussion" --files ...`; do not stage unrelated work.
</step>

<step name="update_state">
Run `engineer_run query state.record-session --stopped-at "Phase ${PHASE_NUMBER} discussion complete" --resume-file "${phase_dir}/${padded_phase}-CONTEXT.md" --status "Discussion complete"`. Commit the resulting record change if it was not already included in the discussion slice. Keep the session open. Stop after reporting the discussion result; planning and implementation each require their own instruction.
</step>

</process>

<success_criteria>
- Every phase was actually discussed, with locked requirements and prior decisions respected.
- CONTEXT includes canonical references and concrete code context; DISCUSSION-LOG contains only real interactions and explicitly delegated decisions.
- Consequential Key Decisions have actual validation evidence or a clearly pending limitation.
- The phase session was joined, records were committed, and the session stays open.
- Discussion did not grant or begin implementation.
</success_criteria>
