# Spec-less Probe Fallback — protocol

Lazy-loaded by `workflows/plan-phase.md` step 7.95 (the gate) and the `<specless_probe_fallback>`
planner block. When a phase SPEC did NOT supply `## Edge Coverage` / `## Prohibitions`, plan-phase
runs the same probe protocol the SPEC path uses and authors the predicates into PLAN.md `must_haves`
(the *else branch* of the `<downstream_consumer>` SPEC-conditional lift). This is
core workflow-body substrate — NOT the `PLAN_PRE_HOOKS_JSON contribution into planner` capability rail. Section absence is detected by the Python `spec.section` runtime verb in the gate; this file holds the
*run-the-probe* half so the capped plan-phase.md stays lean (/ budget).

## 0. Gate — toggle + per-section absence (run first, in the orchestrator)

Reads the default-ON toggle and computes `EDGE_ABSENT` / `PROHIB_ABSENT` via the Python `spec.section` runtime verb
helper; records a VISIBLE skip when disabled or when the phase has no requirement IDs (never a silent
skip, never a hard-fail). Sets `SPECLESS_FALLBACK`, `EDGE_ABSENT`, `PROHIB_ABSENT`, and
`SPECLESS_FALLBACK_DISABLED` for §A and the planner prompt.

```bash
# Toggle defaults ON: any value other than literal "false" enables.
SPECLESS_CFG=$(engineer_run query config-get workflow.specless_probe_fallback 2>/dev/null || echo "true")
SPECLESS_FALLBACK=true; [[ "$SPECLESS_CFG" == "false" ]] && SPECLESS_FALLBACK=false

# Per-section supply: `present` records a heading; `supplied` is true only when the section has at least one data row. Empty headings and header/separator-only tables must still run the fallback.
EDGE_SUPPLIED=$(engineer_run query spec.section "$SPEC_FILE" edges --pick supplied --raw 2>/dev/null) || exit 1
PROHIB_SUPPLIED=$(engineer_run query spec.section "$SPEC_FILE" prohibitions --pick supplied --raw 2>/dev/null) || exit 1
EDGE_ABSENT=1; [ "$EDGE_SUPPLIED" = "true" ] && EDGE_ABSENT=0
PROHIB_ABSENT=1; [ "$PROHIB_SUPPLIED" = "true" ] && PROHIB_ABSENT=0

# Disabled path - record the skip VISIBLY, never silently (RAIL-05 / PROH-4); the note rides into the
# planner prompt (Step 8) so the plan records that no probe predicates were generated.
SPECLESS_FALLBACK_DISABLED=""
if [[ "$SPECLESS_FALLBACK" != "true" ]]; then
  echo "WARNING: probe fallback disabled (workflow.specless_probe_fallback=false); skip recorded, not silent." >&2
  SPECLESS_FALLBACK_DISABLED="probe fallback disabled (workflow.specless_probe_fallback=false): no probe-derived predicates generated for SPEC-absent sections this run."
fi

# Nothing-to-probe guard: the fallback derives predicates from requirement TEXT, so zero requirement
# IDs => nothing to probe => skip VISIBLY (like the disabled path), NOT a hard-fail. Prevents a
# no-SPEC + no-requirements phase from aborting under the default-ON fallback. The orchestrator
# substitutes {phase_req_ids}; empty/whitespace/TBD => no requirements. (A still-literal token is
# non-empty, so an unsubstituted run correctly hits the reference's fail-loud guard instead.)
SPECLESS_REQ_IDS="{phase_req_ids}"
if [[ "$SPECLESS_FALLBACK" == "true" ]] && { [ -z "${SPECLESS_REQ_IDS// /}" ] || [ "${SPECLESS_REQ_IDS}" = "TBD" ]; }; then
  echo "info: spec-less probe fallback: phase has no requirement IDs - nothing to probe; skipping (visible skip)." >&2
  SPECLESS_FALLBACK=false
  SPECLESS_FALLBACK_DISABLED="spec-less probe fallback skipped: phase has no requirement IDs to probe (visible skip)."
fi
```

## A. Edge probe (deterministic) — run when `SPECLESS_FALLBACK=true` AND `EDGE_ABSENT=1`

Mirrors spec-phase Step 5.5 verbatim; the ONLY divergence (D-02) is sourcing `$REQS_JSON` from the
phase requirement IDs (`{phase_req_ids}`) instead of a SPEC interview. Leave `$COVERAGE` empty when
`EDGE_ABSENT=0` — a SPEC-supplied section is never re-run (section-level precedence).

```bash
# THE ONE DIVERGENCE (D-02): source requirements from THIS phase. Populate the array from
# {phase_req_ids}, pulling each requirement's text from REQUIREMENTS.md. The runtime validates
# the shape and returns the deterministic report; check the command status before consuming it.
REQS_JSON=$(mktemp "${TMPDIR:-/tmp}/edge-probe-reqs-XXXXXX.json") || exit 1
cat > "$REQS_JSON" <<'JSON'
[
  { "id": "R1", "text": "<replace: requirement text from REQUIREMENTS.md for each {phase_req_ids} id>" }
]
JSON
if ! python -c 'import json,sys; d=json.load(open(sys.argv[1], encoding="utf-8")); assert isinstance(d,list) and d and all(isinstance(r,dict) and isinstance(r.get("text"),str) and r["text"].strip() and "<replace:" not in r["text"] for r in d)' "$REQS_JSON"; then
  rm -f "$REQS_JSON"
  echo "ERROR: edge-probe requirements are empty, invalid, or still contain a placeholder." >&2
  exit 1
fi
if ! COVERAGE=$(engineer_run query spec.edge-probe "$REQS_JSON"); then
  rm -f "$REQS_JSON"
  echo "ERROR: spec.edge-probe rejected the requirements; fix the input and re-run." >&2
  exit 1
fi
rm -f "$REQS_JSON"
APPLICABLE=$(printf '%s' "$COVERAGE" | python -c 'import json,sys; print(json.load(sys.stdin)["coverage"]["applicable"])') || exit 1
if [ "$APPLICABLE" = "0" ]; then
  echo "WARNING: edge probe proposed zero applicable edges across phase requirements; confirm this is genuinely edge-free before writing an empty fallback section." >&2
fi
printf '%s\n' "$COVERAGE"
```

**Edge `--auto` resolution rules (reuse spec-phase 5.5 verbatim, D-06):** auto-`resolved`
(verification: explicit) where a defensible acceptance criterion can be written (→ a plain
`must_haves.truths` string); else auto-`resolved` (verification: backstop) → author it as a
**structured flat-scalar marker** `{ statement: <the check>,
verification: backstop }` in `must_haves.truths`, NOT a prose note (the verifier branches
deterministically on the `verification: backstop` field; a parenthetical is unparseable — the 
fragility; flat scalar `verification:` key, never a nested object). A `backstop` truth
the verifier cannot confirm with explicit evidence abstains → `human_needed` (reason
`insufficient_spec`), never a silent pass (`engineer/references/honest-verifier.md`). **Never
auto-dismiss** (a wrong dismissal is the exact silent failure this eliminates). An `unclassified` row
stays **`unresolved`** — never auto-resolved with backstop — and is surfaced to the planner as a flagged
assumption. Pass `$COVERAGE` (+ the gate's `$SPECLESS_FALLBACK_DISABLED` note) into the planner
prompt (Step 8). When `EDGE_ABSENT=0`, `$COVERAGE` is empty and this does not run.

## B. Prohibition recall (LLM prose pass) — run when `PROHIB_ABSENT=1`

There is NO compiled prohibition engine and NO `node` invocation — the planner runs
this in-prompt. Full two-stage protocol, canon-referral rule, and status×verification schema live in
`engineer/references/prohibition-probe.md` (do not inline it). Summary:

- **Stage 1 — Recall (adversarial).** Per requirement: *"What could this feature silently become that
  the author would NOT want, but the spec does not forbid?"* Over-produce (~10 raw must-NOT candidates).
- **Stage 2 — Precision.** DROP routine-engineering (normal correctness/hygiene — owned by the edge
  probe or code review); KEEP values / safety / ethics (~2–3 survive).
- **Canon-referral drop.** A kept candidate that is canon security/compliance (OWASP /
  prototype-pollution / path-traversal / injection / GDPR / generic fairness) is NOT minted — emit a
  one-line breadcrumb and DROP it.

**Fallback `--auto` divergence (D-06 / RAIL-04 / PROH-1):** author each kept prohibition as
**flagged-unverified with NO wired-check descriptor**. NEVER write `check_kind` / `check_target` /
`check_rule` / `check_violation_fixture` / `check_clean_fixture` — there is no human to wire/verify a
check, and a descriptor-less item is what keeps it fail-closed (it disposes
`{status:'unverified', flagged:true}` downstream via the reused `dispositionForProhibition`). **Never
auto-dismiss**; never fabricate a check path. Surface any `unresolved` prohibition as a flagged
assumption — never a silent drop.

## C. Authoring (the `<downstream_consumer>` else-branch)

Author the fallback report into `must_haves` with the SAME lift the SPEC path uses — only the source
changes (the fallback report, not the SPEC):

- **Edges →** every resolved (verification: explicit) edge's acceptance criterion → `must_haves.truths` as a plain string;
  every resolved (verification: backstop) edge → `must_haves.truths` as a structured `{ statement, verification: backstop }`
  marker (NOT prose;), which abstains → `human_needed` at verify time when unconfirmed
  ; every `unresolved`/`unclassified` row → an explicit flagged assumption (never a silent drop).
- **Prohibitions →** every kept prohibition → the `must_haves.prohibitions:` sibling block (NOT
  `truths`) via the single `projectProhibitions` serializer (Hyrum — no second
  serializer), authored **descriptor-less** (no `check_*` scalar) so each disposes flagged-unverified.
- **Section-level precedence:** a SPEC-supplied section is never re-run or overwritten — exactly one
  producer per section.
- **No-silent-drop equality:** for each section, (# probe-surfaced items) == (# authored into
  `must_haves` + # surfaced as flagged assumptions).
