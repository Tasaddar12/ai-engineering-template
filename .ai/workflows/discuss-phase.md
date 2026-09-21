<!-- workflow
step: discuss
agent-roles: orchestrator
produces: CONTEXT.md, DISCUSSION-LOG.md
consumes: PROJECT.md, REQUIREMENTS.md, STATE.md, ROADMAP.md, prior CONTEXT.md
-->

<purpose>
Extract implementation decisions that downstream agents need. Analyze the phase to
identify gray areas, let the user choose what to discuss, then deep-dive each
selected area until satisfied.

You are a thinking partner, not an interviewer. The user is the visionary — you
are the builder. Your job is to capture decisions that will guide research and
planning, not to figure out implementation yourself.
</purpose>

<required_reading>
@~/.ai/workflows/_session.snippet.md
@~/.ai/references/domain-probes.md
@~/.ai/references/gate-prompts.md
@~/.ai/references/universal-anti-patterns.md
</required_reading>

<progressive_disclosure>
**Per-mode bodies and templates are lazy-loaded** to keep this file small. Read
only what the current invocation needs:

| When                                                 | Read                                            |
| ---------------------------------------------------- | ----------------------------------------------- |
| `--all` in $ARGUMENTS                                | `workflows/discuss-phase/modes/all.md` overlay  |
| `--auto` in $ARGUMENTS                               | `workflows/discuss-phase/modes/auto.md`         |
| `--text` in $ARGUMENTS or `workflow.text_mode: true` | `workflows/discuss-phase/modes/text.md` overlay |
| no flags above                                       | `workflows/discuss-phase/modes/default.md`      |
| in `write_context` step                              | `workflows/discuss-phase/templates/context.md`  |
| in `git_commit` step                                 | `workflows/discuss-phase/templates/discussion-log.md` |
| writing checkpoints                                  | `workflows/discuss-phase/templates/checkpoint.json`   |

Do not read mode files unless the corresponding flag or condition is set.
</progressive_disclosure>

<downstream_awareness>
**CONTEXT.md feeds into:**

1. **researcher** — reads CONTEXT.md to know WHAT to research
2. **phase-preparer** — reads CONTEXT.md to know WHAT decisions are locked

**Your job:** capture decisions clearly enough that downstream agents can act on
them without asking the user again.
**Not your job:** figure out HOW to implement. Research and planning do that with
the decisions you capture.
</downstream_awareness>

<philosophy>
**User = founder/visionary. You = builder.**

The user knows: how they imagine it working, what it should look and feel like,
what is essential versus nice-to-have, specific behaviors or references they have
in mind.

The user does not know, and should not be asked: codebase patterns (the
researcher reads the code), technical risks (the researcher identifies those),
implementation approach (the preparer works it out), success metrics (inferred
from the work).

Ask about vision and implementation choices. Capture decisions for downstream agents.
</philosophy>

<scope_guardrail>
**CRITICAL: no scope creep.** The phase boundary comes from ROADMAP.md and is
FIXED. Discussion clarifies HOW to implement what is scoped, never WHETHER to add
new capabilities.

**Allowed (clarifying ambiguity):** "How should posts be displayed?" (layout),
"What happens on empty state?" (within the feature).

**Not allowed (scope creep):** "Should we also add comments?" / "What about
search?" / "Maybe include bookmarking?" — new capabilities belong in their own
phase.

**Heuristic:** does this clarify how we implement what is already in the phase, or
does it add a capability that could be its own phase?

**When the user suggests scope creep:**

```
"[Feature X] would be a new capability — that's its own phase.
Want me to note it for the roadmap backlog?

For now, let's focus on [phase domain]."
```

Capture the idea under "Deferred Ideas". Don't lose it, don't act on it.
</scope_guardrail>

<gray_area_identification>
Gray areas are **implementation decisions the user cares about** — things that
could go several ways and would change the result.

1. Read the phase goal from ROADMAP.md
2. Understand the domain — something users SEE / CALL / RUN / READ, or something
   being ORGANIZED — and let that drive which kinds of decisions matter
3. Generate phase-specific gray areas, not generic categories

**Don't use generic category labels** (UI, UX, Behavior). Examples of good ones:

```
Phase: "User authentication"      → Session handling, Error responses, Multi-device policy, Recovery flow
Phase: "Organize photo library"   → Grouping criteria, Duplicate handling, Naming convention, Folder structure
Phase: "CLI for database backups" → Output format, Flag design, Progress reporting, Error recovery
Phase: "API documentation"        → Structure/navigation, Code example depth, Versioning approach
```

**You handle these — don't ask:** technical implementation details, architecture
patterns, performance optimization, scope (the roadmap defines it).
</gray_area_identification>

<answer_validation>
**IMPORTANT** — after every AskUserQuestion call, if the response is empty or
whitespace-only:

- **"Other" with empty text** (the user wants to type freeform): output
  `"What would you like to discuss?"`, STOP generating, wait for the user's next
  message, then reflect it back and continue. Do NOT retry AskUserQuestion or
  call any tools.
- **Any other empty response:** retry once with the same parameters; if it is
  still empty, present the options as a plain-text numbered list. Never proceed
  on empty input.

**Text mode** (`--text` or `workflow.text_mode: true`): follow
`workflows/discuss-phase/modes/text.md` — do not use AskUserQuestion at all.
</answer_validation>

<process>

<step name="initialize" priority="first">
Phase number from the argument (required).

```bash
_root="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
for _c in "$_root"/.{ai,claude,codex}/runtime/phase.py "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/runtime/phase.py "${CODEX_HOME:-$HOME/.codex}"/runtime/phase.py; do
  [ -f "$_c" ] && PHASE_RUNTIME="$_c" && break
done
[ -n "${PHASE_RUNTIME:-}" ] || { echo "ERROR: phase runtime not found; run the installer." >&2; exit 1; }
phase_run() { "$(command -v python3 || command -v python)" "$PHASE_RUNTIME" "$@"; }
INIT=$(phase_run query init.phase-op "${PHASE}")
```

Parse the JSON for: `commit_docs`, `phase_found`, `phase_dir`,
`expected_phase_dir`, `phase_number`, `phase_name`, `phase_slug`, `padded_phase`,
`goal`, `has_research`, `has_context`, `has_spec`, `has_plans`,
`has_verification`, `plan_count`, `roadmap_exists`, `planning_exists`,
`text_mode`, `response_language`, `paths`, `state`.

**If `response_language` is set:** all user-facing output of this workflow —
narration between tool calls, status updates, progress notes, findings, questions,
prompts and explanations — MUST be presented in `{response_language}`. Technical
terms, code, file paths and subagent prompts stay in English.

**If `phase_found` is false:**

```
Phase [X] not found in roadmap.
Use /progress to see available phases.
```

Exit the workflow.

**Mode dispatch — read mode files lazily based on flags in $ARGUMENTS:**

- `--all` → read `workflows/discuss-phase/modes/all.md` before `present_gray_areas`
- `--auto` → read `workflows/discuss-phase/modes/auto.md` before `check_existing`
  (it overrides several steps)
- `--text`, or `text_mode` true → read `workflows/discuss-phase/modes/text.md`
  before any AskUserQuestion call
- no flags → read `workflows/discuss-phase/modes/default.md` before `discuss_areas`

**If `phase_found` is true:** continue to `check_blocking_antipatterns`.
</step>

<step name="open_session">
Open the worktree this work lives in, before writing anything. Read
@~/.ai/workflows/_session.snippet.md for the full contract.

```bash
SESSION=$(phase_run query session.open phase "${padded_phase}")
```

Parse `worktree`, `branch`, `base`, `reused` and `synced`. **Run every
subsequent command in this workflow from `worktree`.** An open session for
this phase is reused rather than replaced, so the work accumulates onto one branch
and arrives as one pull request.

Report it in one line:

```
Session: {branch} ({reused ? "resumed" : "opened"}) at {worktree}
```

If the verb fails, **stop and report its message**. It means isolation could not
be established, and continuing in the invoking checkout is the one outcome this
project does not allow — the dispatch guard would block the write anyway.
</step>


<step name="check_blocking_antipatterns" priority="first">
**MANDATORY — check for blocking anti-patterns before any other work.**

Look for a `.continue-here.md` in the phase directory:

```bash
ls ${phase_dir}/.continue-here.md 2>/dev/null || true
```

If it exists, parse its "Critical Anti-Patterns" table for rows with `severity` =
`blocking`.

**If one or more blocking anti-patterns are found:** demonstrate understanding of
each by answering all three questions for each:

1. **What is this anti-pattern?** — describe it in your own words.
2. **How did it manifest?** — the specific failure that caused it to be recorded.
3. **What structural mechanism (not acknowledgment) prevents it?** — name the
   concrete step or enforcement that stops recurrence.

Write the answers inline before continuing. If a blocking anti-pattern cannot be
answered from the context in `.continue-here.md`, stop and ask the user.

**If no `.continue-here.md` exists, or no blocking rows are found:** proceed to
`check_spec`.
</step>

<step name="check_spec">
Check whether a SPEC.md exists for this phase (`has_spec` from init). A SPEC.md
locks requirements before implementation decisions.

**If found:**

1. Read it.
2. Count the requirements (numbered items under `## Requirements`).
3. Display: `Found SPEC.md — {N} requirements locked. Focusing on implementation decisions.`
4. Set `spec_loaded = true`.
5. Store requirements, boundaries and acceptance criteria as
   `<locked_requirements>` — they flow into CONTEXT.md without being re-asked.

**If not found:** continue with `spec_loaded = false`.
</step>

<step name="check_existing">
Check whether CONTEXT.md already exists using `has_context` from init.

**If it exists:**

**If `--auto`:** auto-select "Update it" — load the existing context and continue
to `analyze_phase`. Log: `[auto] Context exists — updating with auto-selected decisions.`

**Otherwise:** AskUserQuestion (header: "Context"; question: "Phase [X] already
has context. What do you want to do?"; options: "Update it" / "View it" / "Skip").
Branch accordingly.

**If it does not exist:**

Check for an interrupted discussion checkpoint:

```bash
ls ${phase_dir}/*-DISCUSS-CHECKPOINT.json 2>/dev/null || true
```

If a checkpoint file exists:

**If `--auto`:** auto-select "Resume" — load it and continue from the last
completed area.

**Otherwise:** AskUserQuestion (header: "Resume"; question: "Found interrupted
discussion checkpoint ({N} of {M} areas completed). Resume where you left off?";
options: "Resume" / "Start fresh"). On "Resume", parse the checkpoint JSON, load
`decisions` into the accumulator, set `areas_completed` to skip those areas and
continue to `present_gray_areas` with only the remaining ones. On "Start fresh",
delete the checkpoint and continue.

Check `has_plans` and `plan_count` from init. **If `has_plans` is true:**

**If `--auto`:** auto-select "Continue and replan after". Log:
`[auto] Plans exist — continuing with context capture, will replan after.`

**Otherwise:** AskUserQuestion (header: "Plans exist"; question: "Phase [X]
already has {plan_count} plan(s) created without user context. Your decisions here
won't affect existing plans unless you replan."; options: "Continue and replan
after" / "View existing plans" / "Cancel"). Branch accordingly.

**If `has_plans` is false:** continue to `load_prior_context`.
</step>

<step name="load_prior_context">
Read project-level and prior-phase context so decided questions are not re-asked.

```bash
cat .planning/PROJECT.md 2>/dev/null || true
cat .planning/REQUIREMENTS.md 2>/dev/null || true
```

The init bundle already carries `state` (decisions, blockers, position) and
`prior_context` is available from `init.plan-phase`; for discussion, read at most
the **3** most recent prior CONTEXT.md files:

```bash
phase_run query phases.list
```

For each prior CONTEXT.md read: extract `<decisions>` (locked preferences),
`<specifics>` (particular references) and patterns (for example "user prefers
minimal UI", "user rejected single-key shortcuts").

Build an internal `<prior_decisions>` with sections for Project-Level (from
PROJECT.md / REQUIREMENTS.md) and From Prior Phases (per-phase decisions).

**Usage downstream:** `analyze_phase` skips already-decided gray areas;
`present_gray_areas` annotates options ("You chose X in Phase 5"); `discuss_areas`
pre-fills or flags conflicts.

**If no prior context exists:** continue without — expected for early phases.
</step>

<step name="cross_reference_todos">
Check pending todos for matches with this phase's scope.

```bash
TODO_MATCHES=$(phase_run query todo.match-phase "${phase_number}")
```

Parse for: `todo_count`, `matches[]` (each with `file`, `title`, `area`,
`severity`, `score`, `reasons`).

**If `todo_count` is 0 or `matches` is empty:** skip silently.

**If matches are found:** present each (title, area, why it matched), then
AskUserQuestion (multiSelect) asking which to fold in. Folded → `<folded_todos>`
for the CONTEXT.md `<decisions>` section. Reviewed but not folded →
`<reviewed_todos>` for `<deferred>`.

**Auto mode (`--auto`):** fold every todo scoring 0.4 or above automatically and
log the selection.
</step>

<step name="scout_codebase">
Lightweight scan of existing code to inform gray-area identification (~10% context).

Read `@~/.ai/references/scout-codebase.md` — it holds the phase-type → map
selection table, the single-read rule, the no-maps fallback and the
`<codebase_context>` output schema. Then:

1. `ls .planning/codebase/*.md` to find existing maps
2. Select 2–3 maps per the reference's table, or use its grep fallback if none exist
3. Build an internal `<codebase_context>` per the reference's output schema
</step>

<step name="analyze_phase">
Analyze the phase to identify gray areas, grounded in both `prior_decisions` and
`codebase_context`.

1. **Domain boundary** — what capability is this phase delivering? State it clearly.

2. **Initialize the canonical refs accumulator** — start building
   `<canonical_refs>` for CONTEXT.md. Sources:
   - **Now:** any `Canonical refs:` line in ROADMAP.md for this phase, expanded to
     full relative paths. Check REQUIREMENTS.md and PROJECT.md for specs or ADRs.
   - **From `scout_codebase`:** docs referenced by existing code (comments citing ADRs).
   - **From `discuss_areas`:** when the user says "read X", "check Y", or
     references any doc, spec or ADR — add it immediately. These are often the
     MOST important refs.

   This list is MANDATORY in CONTEXT.md, with a full relative path for every ref.
   If no external docs exist, say so explicitly.

3. **Check prior decisions** — scan `<prior_decisions>` for gray areas already
   decided; mark them pre-answered.

4. **SPEC.md awareness** — if `spec_loaded` is true, `<locked_requirements>` are
   pre-answered. Do NOT generate gray areas about WHAT to build or WHY; only about
   HOW to implement. When presenting, include: "Requirements are locked by
   SPEC.md — discussing implementation decisions only."

5. **Gray areas** — for each relevant category, identify 1–2 specific ambiguities
   that would change the implementation. Annotate with code context.

6. **Skip assessment** — if no meaningful gray areas exist (pure infrastructure,
   clear-cut implementation, everything already decided), the phase may not need
   discussion. Say so rather than manufacturing questions.
</step>

<step name="present_gray_areas">
Present the domain boundary, prior decisions and gray areas:

```
Phase [X]: [Name]
Domain: [What this phase delivers — from your analysis]

We'll clarify HOW to implement this. (New capabilities belong in other phases.)

[If prior decisions apply:]
**Carrying forward from earlier phases:**
- [Decision from Phase N that applies here]
```

**If `--auto` or `--all`** (per `modes/auto.md` or `modes/all.md`): auto-select
ALL gray areas. Log: `[--auto/--all] Selected all gray areas: [list].` Skip the
AskUserQuestion below and continue to `discuss_areas` with all areas selected.

**Otherwise, use AskUserQuestion (multiSelect: true):**

- header: "Discuss"
- question: "Which areas do you want to discuss for [phase name]?"
- options: 3–4 phase-specific gray areas, each with a concrete label (not
  generic), 1–2 questions in the description, and code-context / prior-decision
  annotations:

  ```
  ☐ Layout style — Cards vs list vs timeline?
    (You already have a Card component with shadow/rounded variants. Reusing it keeps the app consistent.)

  ☐ Loading behavior — Infinite scroll or pagination?
    (You chose infinite scroll in Phase 4. useInfiniteQuery hook already set up.)
  ```

**Do NOT include a "skip" or "you decide" option.** The user ran this command to
discuss — give real choices.

Continue to `discuss_areas` with the selected areas.
</step>

<step name="discuss_areas">
Discussion behavior is defined by the active mode file:

- **--auto:** follow `workflows/discuss-phase/modes/auto.md` — pick the
  recommended option for every question; no AskUserQuestion. Single-pass cap enforced.
- **Default (no flags):** follow `workflows/discuss-phase/modes/default.md` —
  4 single-question turns per area, then check whether to continue.

Overlay: `--text` → `workflows/discuss-phase/modes/text.md` (replace
AskUserQuestion with plain-text numbered lists).

**Universal rules (every mode):**

- **Canonical ref accumulation** — when the user references a doc, spec or ADR
  during any answer, immediately read it (or confirm it exists) and add it to the
  canonical refs accumulator with a full relative path. Use what you learn to
  inform later questions. These docs are often MORE important than the roadmap's
  refs, because the user specifically wants downstream agents to follow them.
- **Scope creep** — if the user raises something outside the phase domain, capture
  it as a deferred idea and redirect.
- **Incremental checkpoint** — after each area completes, write
  `${phase_dir}/${padded_phase}-DISCUSS-CHECKPOINT.json`. Read
  `workflows/discuss-phase/templates/checkpoint.json` for the schema. The
  checkpoint is structured state, not the canonical CONTEXT.md; `write_context`
  produces that. On resume, `check_existing` detects the checkpoint and offers to
  continue.
- **Discussion log accumulation** — for each question asked, accumulate the area
  name, the options presented, the user's selection and follow-up notes.
  `git_commit` uses this to write DISCUSSION-LOG.md.
</step>

<step name="write_context">
Create CONTEXT.md and DISCUSSION-LOG.md. DISCUSSION-LOG.md is for human reference
(audits, retrospectives) and is NOT consumed by downstream agents.

**Find or create the phase directory:** use `phase_dir` and `expected_phase_dir`
from init. If `phase_dir` is null:

```bash
mkdir -p "${expected_phase_dir}"
```

Set `phase_dir="${expected_phase_dir}"` after creation.

**File location:** `${phase_dir}/${padded_phase}-CONTEXT.md`

**Read the CONTEXT.md template now (lazy-loaded):**

```
Read(workflows/discuss-phase/templates/context.md)
```

The template documents its variable substitutions and conditional sections.
Substitute live values for `[X]`, `[Name]`, `[date]`, `${padded_phase}`, `{N}`.
Include `<spec_lock>` only when `spec_loaded` is true. Include the "Folded Todos" /
"Reviewed Todos" subsections only when `cross_reference_todos` folded or reviewed
todos.

**SPEC.md integration** — when `spec_loaded` is true:

- Add the `<spec_lock>` section immediately after `<domain>`
- Add SPEC.md to `<canonical_refs>` noting "Locked requirements — MUST read before planning"
- Do NOT duplicate SPEC.md requirement text into `<decisions>`; agents read it directly
- `<decisions>` holds only implementation decisions from this discussion

Write the file.
</step>

<step name="confirm_creation">
Present the summary and next steps:

```
Created: {phase_dir}/{padded_phase}-CONTEXT.md

## Decisions Captured
### [Category]
- [Key decision]

[If deferred ideas exist:]
## Noted for Later
- [Deferred idea] — future phase

---

## ▶ Next Up

**Phase {phase_number}: {phase_name}** — {goal}

`/clear` then:

`/plan-phase {phase_number}`

---

**Also available:** `/plan-phase {phase_number} --skip-research` to plan without
research; review or edit CONTEXT.md before continuing.
```
</step>

<step name="git_commit">
**Write DISCUSSION-LOG.md before committing.**

**File location:** `${phase_dir}/${padded_phase}-DISCUSSION-LOG.md`

**Read the template now (lazy-loaded):**

```
Read(workflows/discuss-phase/templates/discussion-log.md)
```

Substitute live values from the discussion log accumulator (area names, options
presented, user selections, notes, deferred ideas, items left to your discretion).
Write the file.

**Clean up the checkpoint** — CONTEXT.md is now the canonical record:

```bash
rm -f "${phase_dir}/${padded_phase}-DISCUSS-CHECKPOINT.json"
```

Commit the context and discussion log:

```bash
phase_run query commit "docs(${padded_phase}): capture phase context" \
  --files "${phase_dir}/${padded_phase}-CONTEXT.md" "${phase_dir}/${padded_phase}-DISCUSSION-LOG.md"
```

Confirm: "Committed: docs(${padded_phase}): capture phase context"
</step>

<step name="update_state">
```bash
phase_run query state.record-session \
  --stopped-at "Phase ${phase_number} context gathered" \
  --resume-file "${phase_dir}/${padded_phase}-CONTEXT.md"

phase_run query commit "docs(state): record phase ${phase_number} context session" \
  --files .planning/STATE.md
```
</step>

<step name="session_handoff">
**Do not deliver this session here.** A phase session is opened by
`/discuss-phase` and reused by `/plan-phase`, `/execute-phase` and
`/verify-work`, so that the whole phase accumulates onto one branch and arrives
as one pull request. Delivering it from this workflow would cut the phase into
separate pull requests and strand whatever comes after.

The session stays open, with its commits on its branch. `/ship` is the phase's
delivery step: it opens the pull request, judges its checks, merges and closes
the session. See @~/.ai/workflows/_session.snippet.md.

Carry the session into the output below so the user knows where the work is and
what closes it:

```
Session: {branch} at {worktree} — open, delivered by `/ship {phase_number}`
```
</step>

</process>

<success_criteria>

- Phase validated against the roadmap
- Prior context loaded (PROJECT.md, REQUIREMENTS.md, STATE.md, prior CONTEXT.md files)
- Already-decided questions not re-asked
- Codebase scouted for reusable assets, patterns and integration points
- Gray areas identified with code and prior-decision annotations
- User selected which areas to discuss (or `--all`/`--auto` selected them)
- Each selected area explored under the active mode's rules until satisfied
- Scope creep redirected to deferred ideas
- CONTEXT.md captures actual decisions, not vague vision
- CONTEXT.md includes a canonical_refs section with full paths to every spec, ADR
  or doc downstream agents need (MANDATORY)
- CONTEXT.md includes a code_context section with reusable assets and patterns
- Deferred ideas preserved for future phases
- STATE.md updated with session info
- User knows the next step
- Checkpoint written after each area completes, and removed after CONTEXT.md is written
- [ ] Phase session left open and reported, with `/ship` named as what
      delivers it
</success_criteria>
