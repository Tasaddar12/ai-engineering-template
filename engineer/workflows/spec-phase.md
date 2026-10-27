<purpose>
Clarify WHAT a phase delivers through a Socratic interview loop with quantitative ambiguity scoring.
Produces a SPEC.md with falsifiable requirements that discuss-phase treats as locked decisions.

This workflow handles "what" and "why" — discuss-phase handles "how".
</purpose>

<ambiguity_model>
Score each dimension 0.0 (completely unclear) to 1.0 (crystal clear):

| Dimension         | Weight | Minimum | What it measures                                  |
|-------------------|--------|---------|---------------------------------------------------|
| Goal Clarity      | 35%    | 0.75    | Is the outcome specific and measurable?           |
| Boundary Clarity  | 25%    | 0.70    | What's in scope vs out of scope?                  |
| Constraint Clarity| 20%    | 0.65    | Performance, compatibility, data requirements?    |
| Acceptance Criteria| 20%   | 0.70    | How do we know it's done?                         |

**Ambiguity score** = 1.0 − (0.35×goal + 0.25×boundary + 0.20×constraint + 0.20×acceptance)

**Gate:** ambiguity ≤ 0.20 AND all dimensions ≥ their minimums → ready to write SPEC.md.

A score of 0.20 means 80% weighted clarity — enough precision that the planner won't silently make wrong assumptions.
</ambiguity_model>

<interview_perspectives>
Rotate through these perspectives — each naturally surfaces different blindspots:

**Researcher (rounds 1–2):** Ground the discussion in current reality.
- "What exists in the codebase today related to this phase?"
- "What's the delta between today and the target state?"
- "What triggers this work — what's broken or missing?"

**Simplifier (round 2):** Surface minimum viable scope.
- "What's the simplest version that solves the core problem?"
- "If you had to cut 50%, what's the irreducible core?"
- "What would make this phase a success even without the nice-to-haves?"

**Boundary Keeper (round 3):** Lock the perimeter.
- "What explicitly will NOT be done in this phase?"
- "What adjacent problems is it tempting to solve but shouldn't?"
- "What does 'done' look like — what's the final deliverable?"

**Failure Analyst (round 4):** Find the edge cases that invalidate requirements.
- "What's the worst thing that could go wrong if we get the requirements wrong?"
- "What does a broken version of this look like?"
- "What would cause a verifier to reject the output?"

**Seed Closer (rounds 5–6):** Lock remaining undecided territory.
- "We have [dimension] at [score] — what would make it completely clear?"
- "The remaining ambiguity is in [area] — can we make a decision now?"
- "Is there anything you'd regret not specifying before planning starts?"
</interview_perspectives>

<process>

## Step 1: Initialize

Read and execute engineer/workflows/_runtime-launcher.snippet.sh. Parse phase/--auto/--text as data; reject unknown flags. Resolve the actual phase first:

```bash
engineer_run query phase.locate "${PHASE}"
```

Require found=true; retain its actual isolated worktree/branch/session and enter it before initialization. Reuse a matching owned phase session; otherwise use `engineer_run query session.open phase "${PHASE}"`, or `session.adopt phase N` only for an established owned isolated checkout. Enter the returned worktree and re-initialize:

```bash
INIT=$(engineer_run query init.phase-op "${PHASE}")
```

Require phase_found=true. No overflow-file protocol or workspace flag is supported. Keep root/branch/base/session identity and actual user authority. Spec authoring authorizes requirements clarification, never discussion completion, phase planning/implementation or another phase. A --auto flag selects defensible defaults within existing intent; it cannot invent a human answer, override locked acceptance or grant execution permission. Record consequential decisions through state.add-decision with actual authority; unresolved conflicts remain visible.

Parse JSON for: `phase_found`, `phase_dir`, `phase_number`, `phase_name`, `phase_slug`, `padded_phase`, `state_path`, `requirements_path`, `roadmap_path`, `planning_dir`, `has_spec`, `spec_path`, `response_language`, `commit_docs`.

**If `response_language` is set:** All user-facing text in this workflow — narration between tool calls, status updates, progress notes, findings, questions, and report prose — MUST be in `{response_language}`. Technical terms, code, and file paths stay in English.

**If `phase_found` is false:**
```
Phase [X] not found in roadmap.
Use /progress to see available phases.
```
Exit.

**Check for existing SPEC.md:** use `has_spec` and `spec_path` from init (one shared definition of the phase SPEC: a plain `*-SPEC.md`, never `*-AI-SPEC.md` or `*-UI-SPEC.md`). Do not glob for it.

If `has_spec` is true:

**If `--auto`:** Auto-select "Skip" — leave the existing SPEC.md unchanged and exit with the same
message the interactive "Skip" prints. Log: `[auto] SPEC.md exists — reusing as-is.` An unattended
run reuses an existing artifact rather than regenerating it (#4776): "Update it" re-scores and
rewrites the spec, discarding answers a person already recorded in it, and nobody is present to
notice.

**Otherwise:** Use AskUserQuestion:
- header: "Spec"
- question: "Phase [X] already has a SPEC.md. What do you want to do?"
- options:
  - "Update it" — Revise and re-score
  - "View it" — Show current spec
  - "Skip" — Exit (use existing spec as-is)

If "View": Display SPEC.md, then offer Update/Skip.
If "Skip": Exit with message: "Existing SPEC.md unchanged; discuss-phase consumes it when invoked."
If "Update": Load existing SPEC.md, continue to Step 3.

## Step 2: Scout Codebase

**Read these files before any questions:**
- `{requirements_path}` — Project requirements
- `{state_path}` — Decisions already made, current phase, blockers
- ROADMAP.md phase entry — Phase description, goals, canonical refs

**Grep the codebase** for code/files relevant to this phase goal. Look for:
- Existing implementations of similar functionality
- Integration points where new code will connect
- Test coverage gaps relevant to the phase
- Prior phase artifacts (SUMMARY.md, VERIFICATION.md) that inform current state

**Synthesize current state** — the grounded baseline for the interview:
- What exists today related to this phase
- The gap between current state and the phase goal
- The primary deliverable: what file/behavior/capability does NOT exist yet?

Confirm your current state synthesis internally. Do not present it to the user yet — you'll use it to ask precise, grounded questions.

## Step 3: First Ambiguity Assessment

Before questioning begins, score the phase's current ambiguity based only on what ROADMAP.md and REQUIREMENTS.md say:

```
Goal Clarity:       [score 0.0–1.0]
Boundary Clarity:   [score 0.0–1.0]
Constraint Clarity: [score 0.0–1.0]
Acceptance Criteria:[score 0.0–1.0]

Ambiguity: [score] ([calculate])
```

**If `--auto` and initial ambiguity already ≤ 0.20 with all minimums met:** Skip interview — derive SPEC.md directly from roadmap + requirements. Log: `[auto] Phase requirements are already sufficiently clear — generating SPEC.md from existing context.` Jump to Step 5.5.

**Otherwise:** Continue to Step 4.

## Step 4: Socratic Interview Loop

**Max 6 rounds.** Each round: 2–3 questions max. End round after user responds.

**Round selection by perspective:**
- Round 1: Researcher
- Round 2: Researcher + Simplifier
- Round 3: Boundary Keeper
- Round 4: Failure Analyst
- Rounds 5–6: Seed Closer (focus on lowest-scoring dimensions)

**After each round:**
1. Update all 4 dimension scores from the user's answers
2. Calculate new ambiguity score
3. Display the updated scoring:

```
After round [N]:
  Goal Clarity:       [score] (min 0.75) [✓ or ↑ needed]
  Boundary Clarity:   [score] (min 0.70) [✓ or ↑ needed]
  Constraint Clarity: [score] (min 0.65) [✓ or ↑ needed]
  Acceptance Criteria:[score] (min 0.70) [✓ or ↑ needed]
  Ambiguity: [score] (gate: ≤ 0.20)
```

**Gate check after each round:**

If gate passes (ambiguity ≤ 0.20 AND all minimums met):

**If `--auto`:** Jump to Step 5.5.

**Otherwise:** AskUserQuestion:
- header: "Spec Gate Passed"
- question: "Ambiguity is [score] — requirements are clear enough to write SPEC.md. Proceed?"
- options:
  - "Yes — write SPEC.md" → Jump to Step 5.5
  - "One more round" → Continue interview
  - "Done talking — write it" → Jump to Step 5.5

**If max rounds reached (6) and gate not passed:**

**If `--auto`:** Write SPEC.md anyway — flag unresolved dimensions. Log: `[auto] Max rounds reached. Writing SPEC.md with [N] dimensions below minimum. Planner will need to treat these as assumptions.`

**Otherwise:** AskUserQuestion:
- header: "Max Rounds"
- question: "After 6 rounds, ambiguity is [score]. [List dimensions still below minimum.] What would you like to do?"
- options:
  - "Write SPEC.md anyway — flag gaps" → Write SPEC.md, mark unresolved dimensions in Ambiguity Report
  - "Keep talking" → Continue (no round limit from here)
  - "Abandon" → Exit without writing

**If `--auto` mode throughout:** Replace all AskUserQuestion calls above with the active Claude or Codex host's defensible recommended choice. Log decisions inline. Apply the same logic as `--auto` in discuss-phase.

**Text mode (`workflow.text_mode: true` or `--text` flag):** Use plain-text numbered lists instead of AskUserQuestion TUI menus.

## Step 5: (covered inline — ambiguity scoring is per-round)

## Step 5.5: Edge-Completeness Probe

Run AFTER the ambiguity gate passes (you probe edges of clear requirements, not vague
ones). Reference: @engineer/references/edge-probe.md.

**Non-English projects — `text_en` carries the classifier-facing translation; the SPEC is
not.** The shape cues the classifier matches are **English** word-boundary patterns, so
requirement prose written in another language matches nothing, classifies to zero shapes, and
lands every row in `unclassified` (#1110) — the taxonomy contributes nothing and `--auto`
leaves it all `unresolved`. When this project has `response_language` set, add an optional
`text_en` key to each `$REQS_JSON` entry: a faithful **English** translation of that
requirement's `text`. `text_en` is **engine input, never user-facing output**, so the
`response_language` rule at the top of this workflow does not govern it — but `text` itself is
NOT translated: write it as the requirement's own text, exactly as it appears in the SPEC.
The SPEC keeps the original language — only `text_en` is translated, and requirement
`id`s are never translated or renumbered (coverage rows join back on `id`, and any Acceptance
Criteria you write from the resolved edges go into the SPEC in `response_language`). Populate
`text_en` for **every** requirement, not only the ones that look edge-relevant: the
`$APPLICABLE = 0` warning below fires only when *all* requirements are unclassified, so a
partly-classified spec slips through with no signal at all. (#4656) The warning now ALSO
fires on the all-unclassified case itself: `coverage.unclassified` counts the soft-signal
rows, and the guard below fires when `$UNCLASSIFIED = $APPLICABLE` — the case where the
classifier learned nothing about ANY requirement. When `response_language` is unset
(an English-language project), omit `text_en` — `text` is already English and the engine
falls back to it automatically (`text_en ?? text`).
If a requirement still classifies to zero shapes with `text_en` populated, it carries no cue in
any language (the recorded recall gap — ADR-857 §98 / ADR-550 D7b, not a translation failure);
author an explicit `shapes` array on that requirement instead of relying on the prose
classifier.

**Runtime coverage compute — canonical Python verb:**

Write the Requirements gathered in THIS spec session to a temporary JSON file, one `{id,text,text_en?,shapes?}` per actual requirement. Preserve the exact SPEC text and IDs; translate only text_en. The following heredoc is an authoring example: replace every placeholder before execution. Use portable suffixless mktemp then append .json; do not build/install a second engine or run an adopting project's build scripts.

```bash
REQS_JSON=$(mktemp "${TMPDIR:-/tmp}/edge-probe-reqs-XXXXXX") || exit 1
mv "$REQS_JSON" "${REQS_JSON}.json" || exit 1
REQS_JSON="${REQS_JSON}.json"
cat > "$REQS_JSON" <<'JSON'
[
  {"id":"R1","text":"<replace: actual SPEC requirement text>"}
]
JSON
if ! python -I -c 'import json,sys; a=json.load(open(sys.argv[1],encoding="utf-8")); assert isinstance(a,list) and a; assert all(isinstance(r,dict) and isinstance(r.get("id"),str) and r["id"].strip() and isinstance(r.get("text"),str) and r["text"].strip() and "<replace:" not in r["text"] for r in a)' "$REQS_JSON"; then
  rm -f "$REQS_JSON"
  printf '%s\n' 'ERROR: populate all real SPEC requirements before the edge probe; empty/invalid/placeholder input cannot pass.' >&2
  exit 1
fi
if ! COVERAGE=$(engineer_run query spec.edge-probe "$REQS_JSON"); then
  rm -f "$REQS_JSON"
  printf '%s\n' 'ERROR: edge probe failed; correct the input/runtime contract and rerun. Never proceed with empty coverage.' >&2
  exit 1
fi
rm -f "$REQS_JSON"
if ! printf '%s' "$COVERAGE" | python -I -c 'import json,sys; r=json.load(sys.stdin); assert isinstance(r,dict) and isinstance(r.get("items"),list) and isinstance(r.get("coverage"),dict); c=r["coverage"]; assert all(isinstance(c.get(k),int) and c[k]>=0 for k in ("applicable","resolved","unresolved","unclassified")); assert isinstance(c.get("byVerification"),dict) and all(isinstance(c["byVerification"].get(k),int) for k in ("explicit","backstop"))'; then
  printf '%s\n' 'ERROR: malformed edge coverage report; refusing prose-only fallthrough.' >&2
  exit 1
fi
printf '%s\n' '### Edge-probe coverage report (deterministic proposals — FLOOR for resolution):'
printf '%s\n' "$COVERAGE"
printf '%s\n' '### (end edge-probe coverage report)'
APPLICABLE=$(printf '%s' "$COVERAGE" | python -I -c 'import json,sys; print(json.load(sys.stdin)["coverage"]["applicable"])') || exit 1
UNCLASSIFIED=$(printf '%s' "$COVERAGE" | python -I -c 'import json,sys; print(json.load(sys.stdin)["coverage"]["unclassified"])') || exit 1
if [ "$APPLICABLE" = 0 ] || [ "$UNCLASSIFIED" = "$APPLICABLE" ]; then
  printf '%s\n' 'WARNING: zero real edge classifications; explicitly review wording/shapes before an empty Edge Coverage section.' >&2
fi
```

The engine's closed eight-category shape taxonomy and full row/coverage schema live in edge-probe.md. Invalid authored shapes/records fail closed; never ignore text_en or replace authored shapes with guessed prose cues. Unclassified rows are soft review signals; authored shapes:[] is an explicit opt-out. Validate and consume every returned row, not only coverage counts. Preserve full raw items[] in the visible context so resolution cannot silently drop deterministic proposals. The engine is a FLOOR, never a ceiling: union additional relevant categories found during the human/model pass. Persist actual resolutions with the documented `spec.edge-probe REQUIREMENTS.json --resolutions FILE` contract when computing the final report; retain dismissed reasons and unresolved rows. If a runtime contract is unavailable, report the exact dependency and keep coverage pending rather than fake a successful probe.

Honor an explicit user defer-all-checks/probes order: author the requirement/proposed-resolution input as pending and do not execute the verb or JSON checks until allowed. Do not label the deterministic probe complete or claim its report exists before execution. Continue independent authorized prose elicitation without silently substituting it for the required runtime floor.

If the guard above fired (`$APPLICABLE` is `0`, or every requirement is unclassified — `$UNCLASSIFIED = $APPLICABLE`, #4656), do NOT proceed silently: ask the author to confirm via AskUserQuestion
("The edge probe found no applicable edges for any requirement — is this genuinely an
edge-free spec, or should we revisit the requirement wording / authored shapes?"). Only write
an empty `## Edge Coverage` section after explicit confirmation.

For each Requirement gathered so far:
1. Start from the edge-probe rows RENDERED above — the deterministic `items[]` are the FLOOR:
   every proposed `(requirement_id, category)` MUST be resolved below (Specify / Dismiss-with-
   reason / Backstop / Defer), none silently dropped. Then raise any applicable category the
   engine MISSED — the rows are a floor, never a ceiling: the classifier has a measured recall
   gap on terse prose (ADR-857 §98 / ADR-550 D7b), e.g. a CSV-export requirement whose
   `encoding` edge the shape cue under-fires. Union the engine's rows with your own
   classification (relevance filter — see the taxonomy in the reference); do not narrow to them.
   Reuse any edges the Round-4 Failure Analyst already surfaced as pre-resolved.
2. For each raised category, propose a CONCRETE candidate edge (not "consider
   boundaries" — e.g. "R2 merges intervals; what about `[[1,2],[2,3]]` that only touch?").
3. Resolve each with the user (AskUserQuestion; text mode → numbered list):
   - **Specify it** → write a new pass/fail line into Acceptance Criteria AND mark the
     edge `resolved` with `verification: explicit`.
   - **Dismiss (reason)** → mark `dismissed` with a required non-empty reason.
   - **Backstop with a test** → mark `resolved` with `verification: backstop`; note
     "held-out edge test" for plan-phase.
   - **Defer** → leave `unresolved`.
   - An `unclassified` row (probe `unclassified — review manually`) means the requirement's
     prose matched no shape cue (#1110) — treat it like any other candidate (**Specify**,
     **Dismiss (reason)**, or **Defer**). A manual-review nudge, not a hard block.

**Soft gate (after resolving):**
- All applicable edges resolved → proceed to Step 5.6.
- Any `unresolved` → AskUserQuestion:
  - header: "Edge Coverage"
  - question: "[N] edge(s) are unresolved: [list]. What do you want to do?"
  - options: "Resolve now" (loop back) / "Write SPEC.md anyway — flag unresolved" /
    "Keep probing"
  - On "anyway": write SPEC.md with those rows marked `⚠ Edge unresolved — planner must
    treat as assumption`.

**`--auto` mode:** resolve over the **same rendered floor** (#3102) — every engine-proposed row
from Step 5.5's report (step 1) plus any category the classifier missed, never a narrower set.
For each: auto-`resolved` (verification: explicit) where a defensible acceptance criterion can be
written; otherwise auto-`resolved` (verification: backstop) (never auto-dismiss — a wrong
dismissal is the exact silent failure being eliminated). Log:
`[auto] edge coverage: E explicit, B backstop, U unresolved`.

**`unclassified` exception (#1110):** `--auto` leaves an `unclassified` candidate
**`unresolved`** (the soft gate surfaces it as a flagged planner assumption) — it never
auto-resolves it with `verification: backstop`. A missing shape is not evidence an edge exists, so minting a held-out
edge obligation on a requirement that may be genuinely edge-free would be a false claim and
risks a vacuous edge test. Leaving it `unresolved` keeps the zero-cue requirement visible
(never a silent drop) without fabricating an edge — which is exactly #1110's purpose: surface
it for review, do not auto-handle it.

Populate the `## Edge Coverage` section of SPEC.md from the resolved edges.

## Step 5.6: Prohibition-Completeness Probe (must-NOT)

Run AFTER Step 5.5 (you probe the must-NOT axis of clear requirements, over the same
requirement list). Reference: @engineer/references/prohibition-probe.md — the
portable two-stage protocol, the canon-referral rule, and the status×verification schema
live there (size-cap discipline; keep this step lean).

**D1 — no compiled engine (ADR-550 D7b).** Unlike Step 5.5, the prohibition probe has NO
separate executable recall engine and runs no executable recall invocation here. The recall stage is an LLM prose
pass: the closed eight-category edge taxonomy a classifier can apply does not exist for the
open values/safety/ethics must-NOT axis. Do NOT copy the Step 5.5 engine-resolution block.
Only the schema/projection layer is real code; the recall is prose.

For each Requirement gathered so far, run the two-stage recall→precision pass:

1. **Stage 1 — Recall (adversarial prose probe).** Ask the single adversarial question of the
   requirement: *"What could this feature silently become that the author would NOT want, but
   the spec does not forbid?"* Over-produce (~10 raw must-NOT candidates) — recall first.
2. **Stage 2 — Precision (one-pass classifier).** Filter the raw list in a single pass:
   **DROP routine-engineering** items (normal correctness/hygiene — "must not mutate input",
   "must not throw on empty" — owned by the edge probe or code review); **KEEP
   values / safety / ethics** items (manipulative framing, protected-attribute proxies, raw
   PII in plaintext). This collapses ~10 → ~2–3 genuine prohibitions.
3. **Canon-referral (ADR-550 D6, PROB-13).** A kept candidate that is canon security/compliance
   (OWASP / prototype-pollution / path-traversal / injection / GDPR / generic fairness) is
   NOT minted here — emit a one-line breadcrumb (*"prototype-pollution is canon — owned by
   /secure-phase + eslint; not minted here"*) and DROP it. Minting canon items duplicates
   /secure-phase and drowns the bespoke signal.
4. **Resolve each surfaced (non-canon) prohibition** (AskUserQuestion; text mode → numbered list):
   - **Keep it** → write a NEGATIVE acceptance criterion (a must-NOT line) into Acceptance
     Criteria AND mark the prohibition `resolved` with a verification tier: `test` (a
     mechanical negative test/lint/assertion exists) or `judgment` (real but not mechanically
     checkable — routes to judgment review).
     - **Capture the wired-check descriptor on `test`-tier (#1278, SOFT).** When a prohibition is
       resolved `verification: test`, ALSO capture the descriptor of the wired check so
       `verify-work` can LOCATE it deterministically (no verifier invention at verify time).
       Capture the flat scalars — persisted into SPEC and projected onto the
       `must_haves.prohibitions` item by the canonical prohibition projection:
       - `check_kind` — `test-command` | `lint-rule`.
       - `check_target` — the negative-test file path (for `test-command`), or the path to lint
         (for `lint-rule`).
       - `check_rule` — the actual configured lint rule id (e.g. `local/no-source-grep`); `lint-rule` only.
       - `check_violation_fixture` (#1279) — path to a KNOWN-BAD subject the wired check is run
         against to **machine-prove fail-first**; rides BOTH kinds. Capture it to let the item green
         end-to-end with zero hand-authoring at verify time; for `test-command` the negative test should
         read its subject from the `GSD_PROHIB_SUBJECT` env var so the prover can inject this fixture.
       - `check_clean_fixture` (#1346; **REQUIRED for `test-command` as of #1906**) — path to a
         KNOWN-CLEAN control subject. The `test-command` prover runs the check against it and requires
         GREEN — proving the violation's RED is caused by the subject's *content*, not by
         `GSD_PROHIB_SUBJECT` merely being set. For a `test-command` this is **mandatory**: omit it and
         the check is un-provable (fail-closed), never proven on the violation alone — so a deceptive
         content-independent test cannot pass. (`lint-rule` needs no clean fixture: its subject IS the
         linted file, no `GSD_PROHIB_SUBJECT` indirection.)
       This is a **SOFT capture (CHK-04): a `test`-tier prohibition WITHOUT a descriptor is still
       allowed** — if the author cannot yet name the wired check, leave the descriptor empty and
       proceed. It is NOT a hard authoring block; the item simply stays fail-closed/flagged
       downstream (an absent/partial descriptor — or one with no `check_violation_fixture` —
       → the canonical descriptor parser null/under-specified/fixture-less → producer fail-closed
       locate-or-unprovable, never green). Do NOT capture `failFirst` here — it is a
       verify-time caller attestation, not a spec-authored field (#1279).
   - **Dismiss (reason)** → mark `dismissed` with a REQUIRED non-empty reason (PROB-05). The
     reason string is the audit trail; silence is not a valid dismissal.
   - **Defer** → leave `unresolved`.

**Soft gate (after resolving) — PROB-06:**
- All applicable prohibitions resolved → proceed to Step 6.
- Any `unresolved` → AskUserQuestion:
  - header: "Prohibitions"
  - question: "[N] prohibition(s) are unresolved: [list]. What do you want to do?"
  - options: "Resolve now" (loop back) / "Write SPEC.md anyway — flag unresolved" /
    "Keep probing"
  - On "anyway": write SPEC.md with those rows marked `⚠ Prohibition unresolved — planner
    must treat as assumption`. This is a soft gate (write-anyway-with-flags), never a silent
    skip — the soft gate IS the control.

**`--auto` mode:** auto-`resolved` where a defensible negative acceptance criterion can be
written (test or judgment tier); otherwise leave `unresolved`. **`--auto` NEVER auto-dismisses
a prohibition** — a wrong dismissal is the exact silent failure this probe eliminates (PROB-06,
the load-bearing safety property). On a `test`-tier auto-resolution, capture the `check_kind` /
`check_target` / `check_rule` / `check_violation_fixture` / `check_clean_fixture` descriptor **only when a wired check is unambiguous**; otherwise
leave it empty — `--auto` NEVER fabricates a check path or fixture (a wrong locate is re-validated and
fails closed at the producer, but a fabricated path is still noise to avoid). Log:
`[auto] prohibitions: R resolved, U unresolved`.

**Text mode (PROB-09):** per Step 5's text-mode rule, replace the AskUserQuestion menus above
with plain-text numbered lists — there is NO hard AskUserQuestion dependency, so the probe
runs identically for non-Claude / text-mode hosts.

Populate the `## Prohibitions` section of SPEC.md from the resolved prohibitions (each
`resolved`/`test` row is a checkable negative acceptance criterion; `resolved`/`judgment`
rows route to judgment review; `⚠ UNRESOLVED` rows are flagged as assumptions). A
`resolved`/`test` row ALSO carries its captured `check_kind` / `check_target` / `check_rule` /
`check_violation_fixture` / `check_clean_fixture` descriptor when present (so the projection feeds `verify-work`'s deterministic locate + machine-proof + causation control, #1278 + #1279 + #1346);
a `test` row with no captured descriptor is still valid — it stays fail-closed/flagged
downstream rather than blocking authoring.

## Step 5.7: Downstream completeness and spec-less precedence

Read engineer/references/specless-probe-fallback.md in full when integrating a phase without SPEC or with an absent/empty Edge Coverage or Prohibitions section. It preserves the SAME complete Step 5.5/5.6 methods; only the requirement source changes to approved phase requirement IDs/text. Detect section supply independently with `engineer_run query spec.section SPEC.md edges` and `spec.section SPEC.md prohibitions`; an absent SPEC makes both absent without a file-read fallback that hides real errors. Empty sections cannot suppress fallback. Preserve every supplied nonempty section unchanged; run fallback only for its absent sibling. The default-on workflow.specless_probe_fallback policy and a genuinely empty requirement list produce visible, cited skip reasons rather than a silent drop or invented requirement.

Edges resolved explicit become PLAN acceptance/must_haves.truths strings; resolved backstop becomes a structured flat `{statement, verification: backstop}` marker requiring actual held-out/PBT evidence, never a parenthetical that a parser cannot see. Every unresolved/unclassified edge stays a flagged planner assumption. Kept prohibitions become the sibling must_haves.prohibitions list with statement/lifecycle/verification and only genuinely wired optional flat check_* fields. Fallback --auto writes NO invented descriptors, never auto-dismisses, and leaves those prohibitions flagged-unverified. Judgment tiers require real review; required human decisions remain human_needed. The same items feed requirement-level VALIDATION, with no-silent-drop equality between surfaced items and authored predicates/flagged assumptions. SPEC section presence does not prove its predicates were wired or checked.

The complete verification pipeline must locate each test-tier prohibition, machine-prove failure on the known violation (assertion/rule failure, never setup/error/timeout), require the known-clean causation control for test-command, and require a real nonvacuous clean production pass. Missing/partial descriptors and missing fixture/check evidence stay flagged and prevent passed; authoring can continue with these explicit obligations. No caller-attested failFirst flag, merely existing file, or report-format string grants a pass. Capture the actual check argv/configuration, target/rule/fixtures, revision and observed per-stage evidence. User-deferred checks remain pending and cannot be promoted during report-only inspection.

## Step 6: Generate SPEC.md

Use the SPEC.md template from @engineer/templates/spec.md.

- Populate the **Edge Coverage** section from Step 5.5 (resolved/dismissed/unresolved rows; resolved items carry `verification: explicit|backstop`).
- Populate the **Prohibitions** section from Step 5.6 (resolved/dismissed/unresolved rows with the test|judgment tier).

**Requirements for every requirement entry:**
- One specific, testable statement
- Current state (what exists now)
- Target state (what it should become)
- Acceptance criterion (how to verify it was met)

**Vague requirements are rejected:**
- ✗ "The system should be fast"
- ✗ "Improve user experience"
- ✓ "API endpoint responds in < 200ms at p95 under 100 concurrent requests"
- ✓ "CLI command exits with code 1 and prints to stderr on invalid input"

**Count requirements.** The display in discuss-phase reads: "Found SPEC.md — {N} requirements locked."

**Boundaries must be explicit lists:**
- "In scope" — what this phase produces
- "Out of scope" — what it explicitly does NOT do (with brief reasoning)

**Acceptance criteria must be pass/fail checkboxes** — no "should feel good" or "looks reasonable."

**If any dimensions are below minimum**, mark them in the Ambiguity Report with: `⚠ Below minimum — planner must treat as assumption`.

Write to: `{phase_dir}/{padded_phase}-SPEC.md`

## Step 7: Commit

Honor an explicit commit_docs:false before calling the verb: report SPEC authored/uncommitted and preserve the file. Otherwise commit the exact SPEC path using the required Why/Changes/Verification body from git-workflow.md (including any pending probes):

```bash
engineer_run query commit "spec(phase-${phase_number}): add SPEC.md for ${phase_name} — ${requirement_count} requirements (#2213)" --files "${phase_dir}/${padded_phase}-SPEC.md"
```

Inspect actual committed/hash or no-change output. The commit verb does not implement a commit_docs skip; the workflow owns that conditional. Do not claim an uncommitted file was committed. Follow authorized delivery and canonical draft tracking for this same session; never auto-chain another workflow or merge.

## Step 8: Wrap Up

Display:

```
SPEC.md written — {N} requirements locked.

  Phase {X}: {name}
  Ambiguity: {final_score} (gate: ≤ 0.20)

discuss-phase will load SPEC.md when invoked and focus on implementation decisions. No discussion, planning or implementation was started.
```

</process>

<critical_rules>
- Every requirement MUST have current state, target state, and acceptance criterion
- Boundaries section is MANDATORY — cannot be empty
- "In scope" and "Out of scope" must be explicit lists, not narrative prose
- Acceptance criteria must be pass/fail — no subjective criteria
- SPEC.md is NEVER written if the user selects "Abandon"
- Do NOT ask about HOW to implement — that is discuss-phase territory
- Scout the codebase BEFORE the first question — grounded questions only
- Max 2–3 questions per round — do not frontload all questions at once
- Step 5.5 edge probe runs after the ambiguity gate; dismissals require a reason; --auto never auto-dismisses
- Step 5.6 prohibition probe runs after the edge probe; dismissals require a reason; --auto never auto-dismisses a prohibition
</critical_rules>

<success_criteria>
- Codebase scouted and current state understood before questioning
- All 4 dimensions scored after every round
- Gate passed OR user explicitly chose to write despite gaps
- SPEC.md contains only falsifiable requirements
- Boundaries are explicit (in scope / out of scope with reasoning)
- Acceptance criteria are pass/fail checkboxes
- SPEC.md committed atomically (when commit_docs is true)
- Closing report states that discuss-phase consumes SPEC.md; no automatic workflow chain
- Edge-completeness probe run; Edge Coverage section populated; unresolved edges flagged as assumptions
- Prohibition-completeness probe run; Prohibitions section populated; unresolved prohibitions flagged as assumptions
</success_criteria>
