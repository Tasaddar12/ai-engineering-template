<purpose>
Generate a UI design contract (UI-SPEC.md) for frontend phases. Orchestrates ui-researcher and ui-checker with a revision loop. Inserts between discuss-phase and plan-phase in the lifecycle.

UI-SPEC.md locks spacing, typography, color, copywriting, and design system decisions before the planner creates tasks. This prevents design debt caused by ad-hoc styling decisions during execution.
</purpose>

<required_reading>
@~/.claude/engineer/references/ui-brand.md
</required_reading>

<available_agent_types>
Valid Engineer subagent types (use exact names — do not fall back to 'general-purpose'):
- ui-researcher — Researches UI/UX approaches
- ui-checker — Reviews UI implementation quality
</available_agent_types>

<process>

## 1. Initialize

```bash
IFS= read -rd '' ENGINEER_ARGS <<'ENGINEER_ARGS_END' || true
$ARGUMENTS
ENGINEER_ARGS_END
ENGINEER_ARGS=${ENGINEER_ARGS%$'\n'}
_engineer_identity_ok() {
  [ -f "$1" ] || return 1
  [ "$(sh "$1" query runtime-identity --pick packageName --raw 2>/dev/null)" = "engineer-runtime" ]
}
_engineer_select() {
  for _engineer_candidate do
    if _engineer_identity_ok "$_engineer_candidate"; then
      ENGINEER_RUN="$_engineer_candidate"
      return 0
    fi
  done
  return 1
}
if [ -n "${ENGINEER_RUN:-}" ]; then
  _engineer_identity_ok "$ENGINEER_RUN" || {
    printf '%s\n' "ERROR: ENGINEER_RUN does not identify engineer-runtime: $ENGINEER_RUN" >&2
    exit 1
  }
else
  _engineer_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
  _engineer_runtime_root=${RUNTIME_DIR:-$_engineer_root}
  _engineer_path_candidate=$(command -v engineer_run 2>/dev/null || true)
  _engineer_select \
    "$_engineer_root/engineer/bin/engineer_run" \
    "$_engineer_runtime_root/engineer/bin/engineer_run" \
    "$_engineer_root/.claude/engineer/bin/engineer_run" \
    "$_engineer_root/.codex/engineer/bin/engineer_run" \
    "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/engineer/bin/engineer_run" \
    "${CODEX_HOME:-$HOME/.codex}/engineer/bin/engineer_run" \
    "$_engineer_path_candidate" || {
    printf '%s\n' 'ERROR: No engineer-runtime launcher was found. Install the Claude or Codex workflow runtime or set ENGINEER_RUN.' >&2
    exit 1
  }
fi
export ENGINEER_RUN
engineer_run() {
  sh "$ENGINEER_RUN" "$@"
}
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  _engineer_path_escaped=$(printf '%s' "${ENGINEER_RUN%/*}" | sed 's/[\\`"$]/\\&/g')
  printf 'export PATH="%s:$PATH"\n' "$_engineer_path_escaped" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true
fi
INIT=$(engineer_run query init.plan-phase  "$PHASE")
AGENT_SKILLS_UI=$(engineer_run query agent-skills ui-researcher )
AGENT_SKILLS_UI_CHECKER=$(engineer_run query agent-skills ui-checker )
```

Parse JSON for: `phase_dir`, `phase_number`, `phase_name`, `phase_slug`, `padded_phase`, `has_context`, `has_research`, `commit_docs`, `response_language`.

**If `response_language` is set:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated.

**File paths:** `state_path`, `roadmap_path`, `requirements_path`, `context_path`, `research_path`.

Detect sketch findings:
```bash
SKETCH_FINDINGS_PATH=$(ls ./.claude/skills/sketch-findings-*/SKILL.md 2>/dev/null | head -1 || true)
```

Resolve UI agent models:

```bash
UI_RESEARCHER_MODEL=$(engineer_run query resolve-model ui-researcher --raw)
UI_CHECKER_MODEL=$(engineer_run query resolve-model ui-checker --raw)
```

Check config:

```bash
UI_ENABLED=$(engineer_run query config-get workflow.ui_phase --raw 2>/dev/null || echo "true")
```

**If `UI_ENABLED` is `false`:**
```
UI phase is disabled in config. Enable via /settings.
```
Exit workflow.

**If `planning_exists` is false:** Error — run `/new-project` first.

## 2. Parse and Validate Phase

Extract phase number from $ARGUMENTS. If not provided, detect next unplanned phase.

```bash
PHASE_INFO=$(engineer_run query roadmap.get-phase "${PHASE}")
```

**If `found` is false:** Error with available phases.

## 3. Check Prerequisites

**If `has_context` is false:**
```
No CONTEXT.md found for Phase {N}.
Recommended: run /discuss-phase {N} first to capture design preferences.
Continuing without user decisions — UI researcher will ask all questions.
```
Continue (non-blocking).

**If `has_research` is false:**
```
No RESEARCH.md found for Phase {N}.
Note: stack decisions (component library, styling approach) will be asked during UI research.
```
Continue (non-blocking).

**If `SKETCH_FINDINGS_PATH` is not empty:**
```
⚡ Sketch findings detected: {SKETCH_FINDINGS_PATH}
   Validated design decisions from /sketch will be loaded into the UI researcher.
   Pre-validated decisions (layout, palette, typography, spacing) should be treated as locked — not re-asked.
```

## 4. Check Existing UI-SPEC

```bash
UI_SPEC_FILE=$(ls "${PHASE_DIR}"/*-UI-SPEC.md 2>/dev/null | head -1)
```

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex) where `AskUserQuestion` is not available.
**If exists:**

**If `--auto`:** Auto-select "Skip" — keep the existing UI-SPEC untouched and proceed to step 7
(checker). Log: `[auto] UI-SPEC exists — reusing as-is, proceeding to verification.` Skip is the
auto choice because it is the only non-destructive one: "Update" re-runs the researcher, which
rewrites the whole contract and drops answers a person already recorded in it, and "View" exits
without verifying anything. A `--auto` run most often meets this file as an unverified draft from
a run that ended before its checker ran, which is exactly the state the checker should now see.

**Otherwise:** Use AskUserQuestion:
- header: "Existing UI-SPEC"
- question: "UI-SPEC.md already exists for Phase {N}. What would you like to do?"
- options:
  - "Update — re-run researcher with existing as baseline"
  - "View — display current UI-SPEC and exit"
  - "Skip — keep current UI-SPEC, proceed to verification"

If "View": display file contents, exit.
If "Skip": proceed to step 7 (checker).
If "Update": continue to step 5.

## 5. Spawn ui-researcher

Display:
```
### Engineer ► UI DESIGN CONTRACT — PHASE {N}

◆ Spawning UI researcher... (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)
```

Build prompt:

```markdown
Read ~/.claude/agents/ui-researcher.md for instructions.

<objective>
Create UI design contract for Phase {phase_number}: {phase_name}
Answer: "What visual and interaction contracts does this phase need?"
</objective>

<required_reading>
- {state_path} (Project State)
- {roadmap_path} (Roadmap)
- {requirements_path} (Requirements)
- {context_path} (USER DECISIONS from /discuss-phase)
- {research_path} (Technical Research — stack decisions)
- {SKETCH_FINDINGS_PATH} (Sketch Findings — validated design decisions, CSS patterns, visual direction from /sketch, if exists)
</required_reading>

${AGENT_SKILLS_UI}

<output>
Write to: {phase_dir}/{padded_phase}-UI-SPEC.md
Template: engineer/templates/UI-SPEC.md
</output>

<config>
commit_docs: {commit_docs}
phase_dir: {phase_dir}
padded_phase: {padded_phase}
</config>
```

Omit null file paths from `<required_reading>`.

<!-- model-omit-on-inherit -->

> **Model omission.** Omit the `model` parameter entirely when the value it would carry (`UI_RESEARCHER_MODEL`, `UI_CHECKER_MODEL`) is `"inherit"` or empty. An empty value 404s on runtimes without native tier aliases — the default on non-Claude runtimes. Omitting it inherits the orchestrator's model.

```
Agent(
  prompt=ui_research_prompt,
  subagent_type="ui-researcher",
  model="{UI_RESEARCHER_MODEL}",
  description="UI Design Contract Phase {N}"
)
```

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above, stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available.

## 6. Handle Researcher Return

**If `## UI-SPEC COMPLETE`:**
Display confirmation. Continue to step 7.

**If `## UI-SPEC BLOCKED`:**
Display blocker details and options. Exit workflow.

## 7. Spawn ui-checker

Display:
```
### Engineer ► VERIFYING UI-SPEC

◆ Spawning UI checker... (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)
```

Build prompt:

```markdown
Read ~/.claude/agents/ui-checker.md for instructions.

<objective>
Validate UI design contract for Phase {phase_number}: {phase_name}
Check all 7 dimensions. Return APPROVED or BLOCKED.
</objective>

<required_reading>
- {phase_dir}/{padded_phase}-UI-SPEC.md (UI Design Contract — PRIMARY INPUT)
- {context_path} (USER DECISIONS — check compliance)
- {research_path} (Technical Research — check stack alignment)
</required_reading>

${AGENT_SKILLS_UI_CHECKER}

<config>
ui_safety_gate: {ui_safety_gate config value}
</config>
```

```
Agent(
  prompt=ui_checker_prompt,
  subagent_type="ui-checker",
  model="{UI_CHECKER_MODEL}",
  description="Verify UI-SPEC Phase {N}"
)
```

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above, stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available.

## 8. Handle Checker Return

**If `## UI-SPEC VERIFIED`:**
Display dimension results. Proceed to step 9.5.

**If `## ISSUES FOUND`:**
Display blocking issues. Proceed to step 9.

## 9. Revision Loop (Max 2 Iterations)

Track `revision_count` (starts at 0).

**If `revision_count` < 2:**
- Re-spawn ui-researcher with revision context. `revision_count` is incremented on the
  researcher's RETURN, not here — a return of `## REVISION_CONFLICT` must not spend an
  iteration, and an increment made before dispatch cannot be withheld afterwards:

```markdown
<revision>
The UI checker found issues with the current UI-SPEC.md.

### Issues to Fix
{paste blocking issues from checker return}

`required_property` + evidence + severity BIND. `fix_hint` is ONE non-binding example route: a
smaller or different mechanism reaching the same property resolves the issue in full — say which
you used. Re-check the user's locked answers, capability guidance (CLAUDE.md, project skills) and
the constraints this UI-SPEC already encodes BEFORE editing; if a hint would contradict one, or
the property is unreachable without breaking one, return `## REVISION_CONFLICT` with the conflict
and the alternatives rather than applying or working around it — see your `## Revision Conflict`
section for its shape.

Read the existing UI-SPEC.md, resolve ONLY the listed issues, re-write the file.
Do NOT re-ask the user questions that are already answered.
</revision>
```

- **If the researcher returns `## REVISION_CONFLICT`:** do NOT increment `revision_count` and do
  NOT re-spawn the checker — a conflict is not resolvable by re-running the same loop. Present the
  conflict and its alternatives to the user and ask which to take: adopt a named alternative /
  override the named constraint and apply the hint / amend the constraint itself. Every option
  resolves the conflict — accepting the spec with the BLOCK still open is NOT offered here, because
  the blocking `required_property` still fails; that choice belongs to the cap escalation below.
  Re-spawn the researcher with the chosen resolution and return to this step.

  **Bounded:** a conflict naming the SAME `required_property` twice in a row (no successful revision in between) is a stall, and so is
  the THIRD conflict return of this loop whatever property it names — alternating property names
  would otherwise never trip the repeat rule. Stop re-spawning and route it to the same cap
  escalation below, so declining to spend an iteration cannot make this path unbounded.
- **On any other return:** increment `revision_count`, then re-spawn checker (step 7)

**If `revision_count` >= 2:**
```
Max revision iterations reached. Remaining issues:

{list remaining issues}

Options:
1. Force approve — proceed with current UI-SPEC (FLAGs become accepted)
2. Edit manually — open UI-SPEC.md in editor, re-run /ui-phase
3. Abandon — exit without approving
```

Use AskUserQuestion for the choice.

**On "Force approve":** proceed to step 9.5 (the UI-consideration probe still runs on the accepted UI-SPEC, so state coverage is recorded even when quality FLAGs were accepted), then step 10. **On "Edit manually" / "Abandon":** exit without running the probe.

## 9.5. UI-Consideration Probe (post-verification)

Run AFTER the checker approves the UI-SPEC (VERIFIED, or force-approved at step 9) — never inline
during authoring, so a revision-loop researcher rewrite (step 9) cannot clobber the section and the
`## UI Considerations` block is committed with the FINAL UI-SPEC. This is the visual analog of
spec-phase Step 5.5's edge probe, retargeted to the UI element/state axis. Reference:
@~/.claude/engineer/references/ui-consideration-probe.md.

**Skip conditions:** if `--auto` and the UI-SPEC already carries a resolved `## UI Considerations`
section (re-run), the write-back is idempotent (it REPLACES that section, never appends). If the
runtime is non-Claude and the probe engine cannot be resolved, the shim FAILS LOUD (below) — it
never silently no-ops (a silent skip would drop the whole state-coverage axis).

**Non-English projects — `text_en` carries the classifier-facing translation; the UI-SPEC is
not.** The element cues the classifier matches are **English** word-boundary patterns, so
element prose written in another language matches nothing, classifies to zero kinds, and lands
every element in `unclassified` — the taxonomy contributes nothing and `--auto` leaves
it all `unresolved`. When this project has `response_language` set, add an optional `text_en`
key to each `$ELEMENTS_JSON` entry: a faithful **English** translation of that element's
`text`. `text_en` is **engine input, never user-facing output**, so the `response_language`
rule at the top of this workflow does not govern it — but `text` itself is NOT translated:
write it as the element's own wording, exactly as it appears in the UI-SPEC. The UI-SPEC keeps
the original language — only `text_en` is translated, and element `id`s are never translated
or renumbered (coverage rows join back on `id`). Populate `text_en` for **every** element, not
only the ones that look UI-relevant: the zero-applicable guard below fires when `$APPLICABLE`
is `0` and again on the all-unclassified case (`$UNCLASSIFIED = $APPLICABLE`), so a
partly-classified surface slips through both arms with no signal at all. When
`response_language` is unset (an English-language project), omit `text_en` —
`text` is already English and the engine falls back to it automatically (`text_en ?? text`).
If an element still classifies to zero kinds with `text_en` populated, it carries no cue in
any language (the recorded recall gap, not a translation failure);
author an explicit `elements` array on that element instead of relying on the prose classifier.


**Runtime coverage compute — invoke spec.ui-probe:**

```bash
# The Python runtime owns probe loading; no build step is needed.
# Element extraction (MANUAL BY DESIGN — not an oversight): the agent reads the researcher-authored
# UI-SPEC prose (the described surfaces — the Design System / Copywriting rows and any element the
# researcher named) and writes ONE object per UI element/surface: {"id","text","text_en"?} where
# text is the prose describing it. This mirrors spec-phase Step 5.5's edge-probe REQS_JSON step
# VERBATIM — a
# hand-populated heredoc guarded by the fail-loud <replace:> check below — the established, shipped
# pattern for feeding a probe from a prose spec. It is NOT mechanized on purpose: a UI-SPEC has no
# single machine-parseable "elements" column — surfaces are distributed across design-token tables
# (Design System / Typography / Color), the Copywriting section, and prose the researcher names, so a
# regex/table parse would fail-OPEN (miss a prose-named surface, or feed a design-token row as a bogus
# element). The agent-authored heredoc + fail-loud guard is the conservative choice, identical to the
# requirement-side edge-probe path (RR-04). If a future UI-SPEC gains a canonical element table,
# revisit to parse it. Populate the heredoc from the UI-SPEC; the guard below fails loud on a
# forgotten substitution (never a no-op). When `response_language` is set, ALSO add `text_en` — a
# faithful ENGLISH translation of `text` (see the Non-English projects note above); the element
# cues are English-only, so original-language `text` alone classifies to zero kinds. `text` itself
# stays the UI-SPEC's own wording and is never translated.
ELEMENTS_JSON=$(mktemp "${TMPDIR:-/tmp}/ui-probe-elements-XXXXXX") && mv "$ELEMENTS_JSON" "${ELEMENTS_JSON}.json" && ELEMENTS_JSON="${ELEMENTS_JSON}.json" || exit 1
cat > "$ELEMENTS_JSON" <<'JSON'
[
  { "id": "E1", "text": "<replace: element/surface description from the UI-SPEC prose>" }
]
JSON
if ! engineer_run query json.validate --schema elements --input "$ELEMENTS_JSON" 2>/dev/null; then
  rm -f "$ELEMENTS_JSON"
  echo "ERROR: ui-probe elements JSON is empty/invalid or still holds the <replace: …> placeholder — populate \$ELEMENTS_JSON from the UI-SPEC's described surfaces before this step runs." >&2
  exit 1
fi
# Invoke the compiled engine and CAPTURE its report. FATAL-INVOKE GUARD: use `if ! COVERAGE=$(…)`,
# NEVER an unchecked coverage command substitution — a bare capture swallows the engine's exit 2 (invalid shape /
# bad input) and falls through to prose re-derivation: fail-OPEN at the exact boundary the engine
# validation protects.
if ! COVERAGE=$(engineer_run query spec.ui-probe "$ELEMENTS_JSON"); then
  rm -f "$ELEMENTS_JSON"
  echo "ERROR: ui-consideration-probe engine failed (invalid shapes or bad input) — fix the element(s) and re-run; never proceed with empty coverage." >&2
  exit 1
fi
rm -f "$ELEMENTS_JSON"
# Malformed-report guard: exit 0 but garbage. The report must parse as { items[], coverage{} }.
if ! printf '%s' "$COVERAGE" | engineer_run query json.validate --schema coverage >/dev/null; then
  echo "ERROR: ui-consideration-probe produced an unparseable or malformed coverage report — refusing to proceed with the resolution loop." >&2
  exit 1
fi
# Zero-applicable guard: a report where NO category applied across ANY element is far more likely a
# classification miss (or malformed elements) than a genuinely state-free UI. Surface it loudly.
APPLICABLE=$(printf '%s' "$COVERAGE" | engineer_run query json.get --field coverage.applicable --default 0 --raw)
UNCLASSIFIED=$(printf '%s' "$COVERAGE" | engineer_run query json.get --field coverage.unclassified --default 0 --raw)
# All-unclassified reads as a non-zero applicable — widen the guard to fire there too.
if [ "$APPLICABLE" = "0" ] || [ "$UNCLASSIFIED" = "$APPLICABLE" ]; then
  echo "WARNING: ui-consideration-probe proposed ZERO applicable categories across all elements — likely a classification miss or malformed elements, not a genuinely state-free UI. Do NOT silently write an empty UI Considerations section." >&2
fi
```

If the guard above fired (`$APPLICABLE` is `0`, or every element is unclassified — `$UNCLASSIFIED = $APPLICABLE`), do NOT proceed silently: ask via AskUserQuestion ("The UI probe found no
applicable state considerations — is this genuinely a state-free surface, or should we revisit the
element descriptions?"). Only write an empty section after explicit confirmation.

**Propose-then-confirm (the partial-cue mitigation — load-bearing).** For each element, the engine
reports the DETECTED element kinds (`classifyElement` in the Python runtime). The prose classifier
is heuristic and LOSSY: a surface that is genuinely both a form and a list, but whose prose trips
only the form cue, under-covers — and because SOMETHING classified, no `unclassified` signal fires.
So SURFACE the detected kinds to the user (AskUserQuestion) and ask whether any real element kind
was missed. If the user ADDs a kind, re-run that element with an authored `elements` override
(the union of detected + added) so the missed categories are raised. A single tripped cue is a
SIGNAL, not proof the element is only that kind — the confirm step, not the heuristic, is what makes
coverage sound.

**Resolution loop** (mirror spec-phase 5.5): resolve each applicable consideration via
AskUserQuestion — **Specify** (→ `resolved`, verification: explicit; write a concrete truth) / **Dismiss (reason required)** /
**Backstop** (→ `resolved`, verification: backstop; a held-out/visual UI-state test) / **Defer** (→ `unresolved`). An `unclassified` row is
a manual-review nudge, not a hard block. Text mode (`workflow.text_mode` / `--text`) → numbered lists.

**Kind-confirmation under `--auto`.** The propose-then-confirm step above is an AskUserQuestion, so
under `--auto` it follows the spec-phase 5.5 convention (replace AskUserQuestion with Claude's
recommended choice): Claude re-reads each element's prose and authors the `elements` override (the
union of the detected kinds + any kind it identifies as missed) instead of prompting — so `--auto`
recall rests on Claude's kind-identification, not the heuristic cue-match alone. This matters because
`autoResolve` (below) is a RESOLUTION floor only: it resolves the *detected* categories and cannot
recover a kind that was never surfaced, so recall is fixed HERE, at kind-confirmation, before
resolution runs.

**`--auto` mode (two layers).** The adapter's `autoResolve` is the CODE floor: every applicable
consideration auto-resolves with `verification: backstop` (carrying the taxonomy question as its
resolution) and an `unclassified` candidate stays `unresolved` — it NEVER auto-`dismiss`es and never
auto-resolves an unclassified item with backstop. On top of that floor the workflow MAY
upgrade an item to `resolved` (verification: explicit) when a
defensible acceptance criterion can be written (the same judgment spec-phase 5.5 applies in prose).
An auto `--auto` run therefore leaves un-upgraded items as `resolved` (verification: backstop): at verify time each one
with no wired evidence routes to `insufficient_spec → human_needed` — never a silent pass.
That surfacing is the intended honest-verifier behavior, not over-flagging.

**Write-back.** Populate a `## UI Considerations` section in the UI-SPEC from the resolved
considerations, in the format the shipped plan-phase `## UI Considerations` lift rule reads:
`resolved` (explicit) → a truth string; `resolved` (backstop) → a flat scalar `{ statement, verification: backstop }`;
`unresolved` → an explicit `⚠ unresolved — planner must treat as assumption` row. Empty-state and
error-state COPY stays in `## Copywriting Contract` — the considerations section covers shape-rooted
STATE coverage and REFERENCES those rows rather than restating the copy (de-dup). IDEMPOTENT: if a
`## UI Considerations` section already exists, REPLACE it — never append a duplicate.

## 10. Present Final Status

Display:
```
### Engineer ► UI-SPEC READY ✓

**Phase {N}: {Name}** — UI design contract approved

Dimensions: 7/7 passed
{If any FLAGs: "Recommendations: {N} (non-blocking)"}

---

## ▶ Next Up — [${PROJECT_CODE}] ${PROJECT_TITLE}

{If CONTEXT.md exists for this phase:}
**Plan Phase {N}** — planner will use UI-SPEC.md as design context

`/clear` then: `/plan-phase {N}`

{If CONTEXT.md does NOT exist:}
**Discuss Phase {N}** — gather implementation context before planning

`/clear` then: `/discuss-phase {N}`

(or `/plan-phase {N}` to skip discussion)

---
```

## 11. Commit (if configured)

```bash
engineer_run query commit "docs(${padded_phase}): UI design contract" --files "${PHASE_DIR}/${PADDED_PHASE}-UI-SPEC.md"
```

## 12. Update State

```bash
engineer_run query state.record-session \
  --stopped-at "Phase ${PHASE} UI-SPEC approved" \
  --resume-file "${PHASE_DIR}/${PADDED_PHASE}-UI-SPEC.md"
```

</process>

<success_criteria>
- [ ] Config checked (exit if ui_phase disabled)
- [ ] Phase validated against roadmap
- [ ] Prerequisites checked (CONTEXT.md, RESEARCH.md — non-blocking warnings)
- [ ] Existing UI-SPEC handled (update/view/skip)
- [ ] ui-researcher spawned with correct context and file paths
- [ ] UI-SPEC.md created in correct location
- [ ] ui-checker spawned with UI-SPEC.md
- [ ] All 7 dimensions evaluated
- [ ] Revision loop if BLOCKED (max 2 iterations)
- [ ] Final status displayed with next steps
- [ ] UI-SPEC.md committed (if commit_docs enabled)
- [ ] State updated
</success_criteria>
