<purpose>
Generate a UI design contract (UI-SPEC.md) for frontend phases. Orchestrates ui-researcher and ui-checker with a revision loop. Inserts between discuss-phase and plan-phase in the lifecycle.

UI-SPEC.md locks spacing, typography, color, copywriting, and design system decisions before the planner creates tasks. This prevents design debt caused by ad-hoc styling decisions during execution.
</purpose>


<required_reading>
@~/.claude/engineer/templates/UI-SPEC.md
@agents/ui-researcher.md
@agents/ui-checker.md
</required_reading>


<available_agent_types>
Valid engineer subagent types (use exact names — do not fall back to 'general-purpose'):
- ui-researcher — Researches UI/UX approaches
- ui-checker — Reviews UI implementation quality
</available_agent_types>


<process>


## 1. Initialize and locate the phase

Read `engineer/RULES.md`, `engineer/references/worker-handoff.md`,
`engineer/references/git-workflow.md` and the complete `engineer/templates/UI-SPEC.md`.
Execute `engineer/workflows/_runtime-launcher.snippet.sh`. Parse the phase from
`$ARGUMENTS`, or resolve the next genuinely unplanned roadmap phase from current
records; do not use an adopting template example as a phase. Run
`engineer_run query phase.locate "${PHASE_NUMBER}"`, require a consistent found
result, quote and enter its worktree, then run
`engineer_run query init.plan-phase "${PHASE_NUMBER}"`. Read actual `phase_dir`,
`padded_phase`, `context_path`, `research_path`, `ui_spec_path`, `artifact_files`,
`models`, `efforts` and `text_mode`; never invent a paths map.

Apply response_language to user-facing prose; technical paths and packet keys stay
in English. Read `workflow.ui_phase` through config-get with default `auto`.
`false` disables this track; `auto` enables it only for actual UI scope in the
ROADMAP/locked CONTEXT and observed product source. An explicit enabled setting
requests assessment, never permission to invent screens in CLI/backend phases.
Document a cited no-UI result and return without a UI-SPEC or browser when there is
no actual UI scope. Missing records require onboarding; do not fill this template's
adopting identity during maintenance.


## 2. Open the phase session

Inspect `session.status` and locator lineage. Reuse the matching session; adopt a
named clean isolated checkout with `engineer_run query session.adopt phase N`
only when ownership is established, otherwise use `session.open phase N`. Quote
and enter its returned worktree, verify root/branch, re-run init.plan-phase there,
and retain the source revision and session identity. No direct primary-checkout
writes. This workflow prepares design only: discussion, UI approval and `--auto`
never grant phase implementation authority or chain into execute-phase.


## 3. Read decisions and prerequisites

Read complete PROJECT, STATE, ROADMAP, REQUIREMENTS, CONTEXT, existing UI-SPEC,
relevant product UI sources and RESEARCH when present. A genuine discussion and
locked CONTEXT decisions are required before dependent planning. If absent, return
the concrete missing decision/discussion dependency; do not continue as though it
were approved. Missing RESEARCH is informational when the actual design stack is
already established. Preserve existing design-system choices and approved outcomes.
No routine confirmation is needed for answered questions or safe choices within
recorded Agent Discretion. Route genuinely missing consequential choices through
the coordinator; continue independent inventory.

Resolve model and effort for each exact `ui-researcher` and `ui-checker` dispatch
with `engineer_run query resolve-model ROLE --raw` and `resolve-effort ROLE --raw`.
Pass both actual values inline, omitting each inherited field. Use the host's
native Claude/Codex dispatch and available question tools; tool names in examples
are capabilities, not proof that a host registered them.


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

**Otherwise:** Reuse and check the current contract by default. Only an explicit update request authorizes regenerating existing answers. For a user-requested view/update choice, use the available host question tool:
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

The researcher is an **artifact-only isolated writer**. Capture the integrated
input revision. For orchestrator-created isolation use
`engineer_run query worktree.create UI_TAG --phase N --base REV --artifact-role ui-researcher --files ACTUAL_NN_UI_SPEC_PATH`.
For host-created isolation register its actual branch/path/base with
`worktree.record-agent UI_TAG --phase N --branch BRANCH --path PATH --base REV --artifact-role ui-researcher --files ACTUAL_NN_UI_SPEC_PATH`.
Replace every metavariable with actual values. Give the worker the resulting
absolute root, branch, base, exact owned UI-SPEC path, complete inputs and limits.
It writes and commits only that artifact, no SUMMARY, product code, package install,
shared status or design-system initialization. Wait for confirmed completion; then
integrate with `engineer_run query worktree.merge-artifacts --phase N` and inspect
its actual artifacts/merged/preserved results before dispatching the checker.
A partial or dirty worker is not integrated as complete. Revision workers use the
same exact artifact-only lifecycle from the new integrated revision.


Display:
```

### ENGINEER ► UI DESIGN CONTRACT — PHASE {N}

◆ Spawning UI researcher... (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)
```

Build prompt:

```markdown
Read the resolved source or installed `agents/ui-researcher.md` in full.

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

</required_reading>


Read only assigned/applicable skills by their descriptions.

<output>
Write to: {phase_dir}/{padded_phase}-UI-SPEC.md
Template: engineer/templates/UI-SPEC.md
</output>

<config>
source_revision: {full captured source revision}
session: {actual phase session}
check_order: {actual user validation limits}
phase_dir: {phase_dir}
padded_phase: {padded_phase}
</config>
```

Omit null file paths from `<required_reading>`.

<!-- #2517 model-omit-on-inherit -->

> **Model omission (#2517).** Omit the `model` parameter entirely when the value it would carry (`UI_RESEARCHER_MODEL`, `UI_CHECKER_MODEL`) is `"inherit"` or empty. An empty value 404s on runtimes without native tier aliases — the default on non-Claude runtimes. Omitting it inherits the orchestrator's model. See @~/.claude/engineer/references/agent-adaptation.md#supported-hosts.

```
Agent(
  prompt=ui_research_prompt,
  subagent_type="ui-researcher",
  model="{UI_RESEARCHER_MODEL}",
  effort="{UI_RESEARCHER_EFFORT}",
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

Capture the integrated specification revision and exact content digest. Supply
root/branch/base, phase/session/caller, full authority/check-order packet, complete
UI-SPEC and acceptance/CONTEXT, source inputs and their digests. The checker is
read-only, returns all seven dimensions with cited evidence and uncovered scope,
and never writes approval or dispatches children. A missing/truncated dimension
or wrong revision is missing evidence, not approval. Join all assigned results
before coordinator writes. Require the canonical status and preserve BLOCKs.


Display:
```

### ENGINEER ► VERIFYING UI-SPEC

◆ Spawning UI checker... (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)
```

Build prompt:

```markdown
Read the resolved source or installed `agents/ui-checker.md` in full.

<objective>
Validate UI design contract for Phase {phase_number}: {phase_name}
Check all 7 dimensions. Return APPROVED or BLOCKED.
</objective>

<required_reading>
- {phase_dir}/{padded_phase}-UI-SPEC.md (UI Design Contract — PRIMARY INPUT)
- {context_path} (USER DECISIONS — check compliance)
- {research_path} (Technical Research — check stack alignment)
</required_reading>


Read only assigned/applicable skills by their descriptions.

<config>
ui_safety_gate: {ui_safety_gate config value}
</config>
```

```
Agent(
  prompt=ui_checker_prompt,
  subagent_type="ui-checker",
  model="{UI_CHECKER_MODEL}",
  effort="{UI_CHECKER_EFFORT}",
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
you used. Re-check the user's locked answers, capability guidance (AGENTS.md, project skills) and
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

**If `revision_count` >= 2 or the repeated-conflict cap fires:** retain BLOCKED
and the exact required properties, conflicts and alternatives. Stop only dependent
planning. Do not offer force approval, waive a BLOCK, relitigate a locked answer
or add a routine proceed/ignore prompt. A genuine user decision changing the
contract must be recorded in CONTEXT before a fresh bounded revision.


## 9.5. UI-Consideration Probe (post-verification)

Run AFTER the checker approves the UI-SPEC (VERIFIED) — never inline
during authoring, so a revision-loop researcher rewrite (step 9) cannot clobber the section and the
`## UI Considerations` block is committed with the FINAL UI-SPEC. This is the visual analog of
spec-phase Step 5.5's edge probe, retargeted to the UI element/state axis. Reference:
`engineer/references/ui-consideration-probe.md`.

Existing resolved UI Considerations may be reused only for unchanged surfaces and
input decisions. Write-back replaces the section, never appends a duplicate. A
faithful agent-judged table supplies this axis where the runtime lacks a UI probe;
missing automation never silently skips state coverage.
**Non-English projects — `text_en` carries the classifier-facing translation; the UI-SPEC is
not.** The element cues the classifier matches are **English** word-boundary patterns, so
element prose written in another language matches nothing, classifies to zero kinds, and lands
every element in `unclassified` (#1110) — the taxonomy contributes nothing and `--auto` leaves
it all `unresolved`. When this project has `response_language` set, add an optional `text_en`
key to each `$ELEMENTS_JSON` entry: a faithful **English** translation of that element's
`text`. `text_en` is **engine input, never user-facing output**, so the `response_language`
rule at the top of this workflow does not govern it — but `text` itself is NOT translated:
write it as the element's own wording, exactly as it appears in the UI-SPEC. The UI-SPEC keeps
the original language — only `text_en` is translated, and element `id`s are never translated
or renumbered (coverage rows join back on `id`). Populate `text_en` for **every** element, not
only the ones that look UI-relevant: the zero-applicable guard below fires when `$APPLICABLE`
is `0` and again on the all-unclassified case (`$UNCLASSIFIED = $APPLICABLE`, #4656), so a
partly-classified surface slips through both arms with no signal at all. When
`response_language` is unset (an English-language project), omit `text_en` —
`text` is already English and the engine falls back to it automatically (`text_en ?? text`).
If an element still classifies to zero kinds with `text_en` populated, it carries no cue in
any language (the recorded recall gap — ADR-857 §98 / ADR-550 D7b, not a translation failure);
author an explicit `elements` array on that element instead of relying on the prose classifier.
(#4657)

**Coverage compute — explicit element table, never a fabricated executable.**
Read the whole final contract, including surfaces named in prose, Copywriting,
Design System and component sections. Author one stable `{id,text,text_en?,elements?}`
entry per actual surface; a regex of token tables cannot recover this inventory.
Reject empty/placeholder input. Load the COMPLETE
`engineer/references/ui-consideration-probe.md`, including all eight categories,
applicability sets and exact questions. Use a documented existing Python runtime
verb only if its actual interface supports this axis. Otherwise compute an
agent-judged table from that full reference, explicitly recording that provenance;
do not reference a missing compiled module, install Node or run a build.

For each element record proposed kinds (`form`, `list-collection`, `nav`, `media`,
`interactive-control`, `static-content`) and EVERY applicable category: empty,
loading, error, populated, partial, overflow, zero-one-many, long-text. No kind
match raises one `unclassified` unresolved item; explicit `elements: []` requires
an explained applicability decision. Preserve stable IDs, original-language text
and faithful text_en where relevant. If all elements are unclassified or zero
categories apply, re-inspect the actual surfaces; record evidence for any genuinely
state-free surface or the precise unresolved gap. Never silently write an empty
coverage section or manufacture a no-UI result.

**Propose-then-confirm (the partial-cue mitigation — load-bearing).** For each element, the coverage table
reports the proposed element kinds. The prose classifier
is heuristic and LOSSY: a surface that is genuinely both a form and a list, but whose prose trips
only the form cue, under-covers — and because SOMETHING classified, no `unclassified` signal fires.
Review the detected kinds against every locked decision and actual surface; ask only for a genuinely missing consequential user decision, through the coordinator. If the user ADDs a kind, re-run that element with an authored `elements` override
(the union of detected + added) so the missed categories are raised. A single tripped cue is a
SIGNAL, not proof the element is only that kind — the confirm step, not the heuristic, is what makes
coverage sound.

**Resolution loop** (mirror spec-phase 5.5): resolve each applicable consideration from locked acceptance and delegated discretion; route only unresolved consequential decisions through the coordinator — **Specify** (→ `resolved`, verification: explicit; write a concrete truth) / **Dismiss (reason required)** /
**Backstop** (→ `resolved`, verification: backstop; a held-out/visual UI-state test) / **Defer** (→ `unresolved`). An `unclassified` row is
a manual-review nudge, not a hard block. Text mode (`workflow.text_mode` / `--text`) → numbered lists.

**Kind-confirmation under `--auto`.** Within locked decisions and delegated
discretion, the agent re-reads each surface and authors the union of proposed and
missed kinds without a routine prompt. Recall depends on this explicit review,
not a single heuristic cue. The resolution floor covers detected categories only;
it cannot recover a kind that never entered the table.

**`--auto` mode (two layers).** The agent-judged table applies this resolution floor: every applicable
consideration auto-resolves with `verification: backstop` (carrying the taxonomy question as its
resolution) and an `unclassified` candidate stays `unresolved` — it NEVER auto-`dismiss`es and never
auto-resolves an unclassified item with backstop (#1110). On top of that floor the workflow MAY
upgrade an item to `resolved` (verification: explicit) when a
defensible acceptance criterion can be written (the same judgment spec-phase 5.5 applies in prose).
An auto `--auto` run therefore leaves un-upgraded items as `resolved` (verification: backstop): at verify time each one
with no wired evidence routes to `insufficient_spec → human_needed` — never a silent pass (#1154).
That surfacing is the intended honest-verifier behavior, not over-flagging.

**Write-back.** Populate a `## UI Considerations` section in the UI-SPEC from the resolved
considerations, in the format the shipped plan-phase `## UI Considerations` lift rule reads:
`resolved` (explicit) → a truth string; `resolved` (backstop) → a flat scalar `{ statement, verification: backstop }`;
`unresolved` → an explicit `⚠ unresolved — planner must treat as assumption` row. Empty-state and
error-state COPY stays in `## Copywriting Contract` — the considerations section covers shape-rooted
STATE coverage and REFERENCES those rows rather than restating the copy (de-dup). IDEMPOTENT: if a
`## UI Considerations` section already exists, REPLACE it — never append a duplicate.


## 9.6. Record durable decisions before final review

Before capturing the final checker revision, record actual design-system choices
that outlive this phase with `engineer_run query state.add-decision`, including
actual rationale and decision provenance. Record session progress with the actual
stopped-at/resume-file through state.record-session. Do not invent human approval
or re-add an unchanged already recorded choice. Commit the coordinator-owned
records before final review; their mutation after review invalidates currentness.

## 10. Final checker and coordinator approval

The consideration section and COMPLETE body, including Checker Sign-Off, are part
of the contract. Finish them, integrate and commit the candidate contract BEFORE
capturing the final checker's reviewed_revision. If a preliminary checker suggests
sign-off changes, apply and commit those before a fresh final read-only checker.
Only after ALL artifact writers/checkers stop does the coordinator persist its
actual complete evidence in frontmatter, set status: approved and reviewed_at.
Never change contract body or other metadata under an approval-only exception.

The existing `check.ui-plan-gate N` verb consumes this `ui_checker` frontmatter
mapping (replace every value from actual evidence; never manufacture a dispatch):

```yaml
ui_checker:
  role: ui-checker
  verdict: APPROVED
  ui_safety_gate: true # actual resolved policy; absent config defaults true
  phase: "01" # actual canonical phase number, including decimal identity
  spec_path: .planning/phases/01-example/01-UI-SPEC.md # actual relative path
  context_path: .planning/phases/01-example/01-CONTEXT.md # actual relative path
  reviewed_revision: <actual full captured Git SHA>
  spec_digest: <actual canonical contract SHA-256>
  context_digest: <actual CONTEXT text SHA-256>
  roadmap_digest: <actual ROADMAP text SHA-256>
  checker_id: <actual independent checker dispatch identity>
  author_id: <actual researcher dispatch identity, distinct from checker>
  session: <actual phase-session identity>
  reviewed_at: <actual review timestamp>
  unexamined: [] # only when every assigned dimension/input was examined
  dimensions:
    - dimension: 1
      verdict: PASS # PASS or FLAG, never BLOCK under APPROVED
      evidence: <actual cited contract observation>
    # Include EXACTLY one actual evidenced record for EACH dimension 1 through 7.
    # Only dimension 6 may be DISABLED, and only under actual ui_safety_gate: false.
```

For spec_digest, parse frontmatter and body with the runtime's safe subset. Hash
UTF-8 `json.dumps({"metadata": filtered_metadata, "body": complete_body},
sort_keys=True, ensure_ascii=False, separators=(",", ":"))`, excluding ONLY
frontmatter status, approved, reviewed_at and ui_checker. Hash CONTEXT/ROADMAP
UTF-8 decoded text with LF newlines, as core.read does. All other metadata and the
complete contract body bind. These fields preserve machine-checkable source
identity; genuine reviewer identity and design decisions still require their
actual dispatch/CONTEXT evidence, not self-authored assertions.

Commit only that exact spec's approval metadata. Run
`engineer_run query check.ui-plan-gate N` only when checks are permitted, before
planner dispatch. The gate rejects missing/mismatched input evidence, incomplete
or blocking dimensions, dirty inputs, nonancestor revisions, merges and EVERY
intervening commit changing anything except that exact spec's approval metadata.
A changed-and-restored contract/source still invalidates approval. Observe its
actual blocked/required/reason; pending gate execution remains pending. Record a
concrete runtime-version limitation instead of claiming absent protections. No
status/checkbox alone proves design approval or human implementation authority.

## 11. Preserve the checked planning boundary

The exact approval-only commit and permitted gate execution occurred in Step 10.
Do not mutate shared records or the contract after that gate and before returning
to the caller's planner boundary. A necessary change is committed and followed by
a fresh final checker and gate; never reuse stale approval. Follow actual user
delivery/check-order overrides and canonical git-workflow. No routine maintenance
SUMMARY is required when the assignment excludes it.

## 12. Present final status

Report the actual contract path, reviewed revision, seven dimension outcomes,
nonblocking FLAGs, state coverage and remaining dependencies. Say whether planning
has usable design evidence. Design completion never authorizes implementation.
No command chaining, forced acceptance or routine stop prompt.

</process>
<success_criteria>
- Actual phase/session/scope and recorded discussion decisions loaded.
- No-UI scope returned honestly without invented product surfaces.
- Exact isolated artifact-only writer integrated through merge-artifacts.
- Complete retained UI template, inventory, accessibility, interaction and state methods applied.
- All seven read-only checker dimensions joined against the final content.
- Coordinator alone records evidence-based approval and durable choices.
- Required gate/check execution remains pending until permitted.
- Closing status preserves actual authority and every unresolved dependency.
</success_criteria>
