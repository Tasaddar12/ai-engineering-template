# Prohibition-Probe — Spec-Completeness Must-NOT Reference

Shared reference for the spec/requirements phase. Companion to
`@~/.claude/engineer/references/edge-probe.md`: `edge-probe` reaches the
**data/behavior-shape axis** (boundaries, adjacency, encoding, ordering) — the things a
feature must *do*. This reference reaches the orthogonal **must-NOT axis** (product, values,
safety, ethics) — the things a feature must *never silently become*. The edge-probe caught
0/8 of these in controlled testing because it is the wrong instrument: a shape taxonomy
cannot surface "the reminder must not shame the user." Walk each requirement through the
two-stage recall→precision protocol below and resolve each surfaced prohibition to exactly
one state.

This doc is written in generic `requirements → checks → verifier` terms with no
tool-specific vocabulary, so it is portable: copy it into any spec/requirements process.
A short mapping table at the end binds it to common host structures.

## Why front-of-pipeline

A goal-backward verifier only checks assertions that exist; an assertion only exists for a
requirement that was written down. The class of constraint this probe targets — the
*"must-NOT"* the author assumed but never wrote — is invisible to the verifier in exactly
the same way an omitted edge is, but with a sharper failure mode: a `✅ done` that means
"the code matches the words in the spec" can still ship a feature that does what the author
explicitly would *not* want. The manipulative-streak reminder, the loan model that proxies
on zip code, the audit log that stores raw SSN — each one passes a literal spec while
violating the intent. The fix is not a better verifier; it is **spec completeness**: surface
the omitted prohibition into an explicit, checkable acceptance criterion *before* any code
exists, after which the verifier reliably enforces it.

The technique is adversarial elicitation, not deterministic computation. Unlike the edge
taxonomy (a closed eight categories a classifier can apply), the recall stage is inherently
model-driven: it asks an open question and reads prose. There is **no deterministic recall engine** — the recall stage is an LLM prose pass. The Python runtime implements schema/projection and three-stage configured-check proof; those operations do not infer missing intent (ADR-550 Decision 7b). Building a deterministic
recall adapter would be the scope-creep the maintainer flags.

## Inputs

A list of requirements, each a `{ id, text }` record where `text` is a testable statement.
There is no shape override and no taxonomy classifier — the recall stage reads the prose
directly and the precision stage filters its raw output. The probe runs **after** the
edge-probe in the spec phase, over the same requirement list.

## Two-stage protocol (recall → precision)

The probe is a two-pass pipeline per requirement. Stage 1 maximizes recall (cast wide);
Stage 2 restores precision (drop the noise). Running them in this order — wide then narrow —
is what keeps the surfaced list both complete and short.

**Stage 1 — Recall (adversarial probe).** Ask the single adversarial question of each
requirement:

> *What could this feature silently become that the author would NOT want, but the spec
> does not forbid?*

This question is model-robust (17/17 holistic surfacing including smaller models in the N18
experiment). It deliberately over-produces: ~10 raw candidates per requirement, including
routine engineering items. That over-production is intentional — recall first.

**Stage 2 — Precision (one-pass classifier).** Filter the raw Stage-1 list in a single pass.
The rule is a drop/keep split:

- **DROP routine-engineering items** — anything that is a normal correctness or hygiene
  concern rather than an intent constraint: "must not mutate its input", "must not throw on
  empty list", "must return a primitive not an object", "must not leak a file handle". These
  belong to the edge-probe or to ordinary code review, not here.
- **KEEP values / safety / ethics items** — anything that, if violated, makes the feature do
  something the author would object to on product, fairness, privacy, transparency, or
  safety grounds: "must not use shaming framing", "must not proxy on protected attributes",
  "must not store raw PII in plaintext".

This collapses the raw ~10 to ~2–3 genuine prohibitions (GT 5/5, 0 false positives on the
N18 eight-spec battery). A requirement that yields zero kept prohibitions emits an empty
list — that is the correct precision outcome for a pure utility, not a failure.

## Canon-referral (do not mint canon items)

Some kept candidates are not bespoke at all — they are **canon** security/compliance
constraints that a dedicated tool already owns. Do NOT mint a prohibition for them. Instead
emit a one-line breadcrumb and stop:

- OWASP / prototype-pollution / path-traversal / injection → breadcrumb to `/secure-phase`
  and `eslint` (security plugins), not a minted prohibition.
- GDPR / data-retention / consent → breadcrumb to `/secure-phase`.
- Generic fairness/bias canon → breadcrumb to `/secure-phase`.

The breadcrumb reads like: *"prototype-pollution is canon — covered by /secure-phase +
eslint; not minted here."* This keeps the surfaced list to the ~2–3 **bespoke** items that
no other tool would catch — the manipulative-framing prohibition, the product-specific
fairness constraint — which is the whole value of the probe. Minting canon items both
duplicates other tooling and drowns the bespoke signal (ADR-550 Decision 6).

## Resolution states

Each surfaced prohibition carries two orthogonal axes — a resolution **lifecycle** and, when
resolved, a **verification** tier (ADR-550 Decision 7, the shared probe-core model; the
lifecycle is identical to the edge-probe, the verification tiers differ):

- **status** — `resolved | dismissed | unresolved` (IDENTICAL to the edge-probe):
  - **resolved** — the prohibition is addressed; *how* it is addressed is the verification tier.
  - **dismissed** — not a genuine prohibition for this feature, accompanied by a required,
    non-empty reason string. "N/A — this utility has no user-facing surface, no values
    constraint applies" is valid; silence is not. The reason string is the audit trail.
  - **unresolved** — carried forward and flagged; the author chose not to resolve it yet.
- **verification** (only when `status` is `resolved`; `null` otherwise) — `test | judgment`
  (this REPLACES the edge-probe's `explicit | backstop`):
  - **test** — the prohibition can be mechanically checked (a negative test, a lint rule, an
    assertion that the audit log contains no raw SSN). A checkable assertion exists.
  - **judgment** — the prohibition is real but cannot be reduced to a mechanical test (a
    human/LLM judgment that the framing is not manipulative). It records intent and routes
    to a judgment-based review rather than a green/red test.

  At verify time these tiers are routed differently (ADR-550 D4):
  - A **test**-tier prohibition is enforced + hard-gates via the deterministic
    configured project negative check with the actual violation/clean fixtures: it locates the wired
    mechanical check (a configured negative test OR a lint/AST rule run as
    `eslint --format json` and filtered by `ruleId`), **machine-proves it is fail-first** against a
    known violation, runs it for a genuine **non-vacuous** pass, and records the
    observed prohibition disposition. A passing, fail-first-proven wired check disposes **green**
    (satisfiable → can reach `passed`); a missing, un-provable, or genuinely-non-passing check
    **hard-gates** (flagged, never green → `gaps_found`) in BOTH interactive and autonomous modes —
    never a silent pass.

    **Machine-proven fail-first (#1279).** `failFirst` is now **machine-proven, not caller-attested**:
    before a clean pass greens, the producer independently runs the wired check against a KNOWN
    VIOLATION and confirms it goes RED (any other outcome — passes-on-violation, can't-prove, throws,
    times out, no violation source — hard-gates). The violation is sourced from a descriptor field:
    - **`violationFixture`** — an author-supplied path to a KNOWN-BAD subject. For `lint-rule`: a file
      whose content violates `rule`; the prover lints it and requires the rule id to appear in the
      JSON report (the rule must have teeth). For `test-command`: a subject the negative test exercises,
      expected to drive it RED.
    - **`GSD_PROHIB_SUBJECT`** — the test-command subject-injection convention: the producer spawns the
      negative test with `GSD_PROHIB_SUBJECT=<violationFixture>` in the child env; the test reads that
      env var to locate its subject-under-test and is expected to go red against the violating subject.
    - **lint-fixture authoring gotcha** — the violating fixture must actually trigger the rule. For the
      `local/no-source-grep` dogfood anchor specifically, use the a path-construction expression that actually violates the configured rule form
      (a standalone quoted dir token); a single string literal like a harmless path literal does NOT trigger the
      rule, so a mis-authored fixture makes the prover report "not proven" and hard-gate a legitimately
      wired check. (`no-source-grep` has no filename guard — every supported source file with the violating pattern must be exercised.)

    Both `ENGINEER_PROHIB_SUBJECT` and the compatibility `GSD_PROHIB_SUBJECT` are live subject-injection interfaces of the Python proof producer. The descriptor/fixture contract has active consumers; do not rename it as a zero-migration proposal. The producer supplies both variables to the configured check. They carry a path, never a secret value.
  - A **judgment**-tier prohibition routes to a never-silent / never-hard-halt soft gate
    (autonomous emits an `unverified-prohibition — human review recommended` flag).

Splitting these axes keeps the lifecycle enum free of a verification fact and lets the
prohibition adapter declare `test | judgment` without forking the shared lifecycle enum that
the edge-probe's `explicit | backstop` also uses.

## Required wired-check descriptor and both controls

For every resolved test-tier prohibition, establish the real configured negative check and supply a descriptor. Missing/partial descriptors remain representable planning gaps, but cannot green. Both known-bad and known-clean controls are REQUIRED; an always-failing check or one that fails merely because a subject variable is set is not a proof.

The Python runtime exposes `spec.prohibition-project INPUT.json` and `spec.prohibition-proof DESCRIPTOR.json --subject REALPATH`, with optional `--timeout 30`. The first projects already-selected intent into plan obligations; it does not discover prohibitions. The second executes only the configured argv, without a shell, and observes three stages: violation RED, clean GREEN and real GREEN. It requires fresh non-vacuous reports and actual assertion/rule evidence, not arbitrary process failure.

```json
{
  "kind": "test-command",
  "target": "tests/test_audit_privacy.py",
  "violationFixture": "tests/fixtures/audit-with-raw-ssn.json",
  "cleanFixture": "tests/fixtures/audit-clean.json",
  "argv": ["python", "{target}"],
  "reportFormat": "unittest"
}
```

Descriptor fields:

| Field | Contract |
|---|---|
| `kind` | `test-command` or `lint-rule`. |
| `target` | Existing actual project check path. |
| `rule` | Required exact rule ID for lint-rule. |
| `violationFixture` | Existing known-bad subject that must produce the intended RED. |
| `cleanFixture` | Existing known-clean subject that must produce GREEN. |
| `argv` | Actual configured executable and arguments; no shell string. |
| `reportFormat` | `unittest`, `junit` or `eslint-json`, matching actual output. |
| `reportFile` | Optional except required for JUnit; output must be freshly produced. |

All three subject paths must be distinct and the control bytes must differ from the real subject and from each other. This prevents a forged control that simply reuses the product output. Both subject environment variables identify the selected stage's subject. `argv` and `reportFile` may interpolate `{target}`, `{subject}` and `{stage}`; argv may use `{report}` when reportFile is configured. A lint argv MUST inject `{subject}` so the rule actually examines the stage subject, not the same real file three times.

The five flat plan keys remain supported aliases: `check_kind`, `check_target`, `check_rule`, `check_violation_fixture`, `check_clean_fixture`. Aliases and native fields cannot conflict. Preserve the actual Python projection/proof interface, not retired CJS function names. The flat keys record descriptor intent; argv/reporter configuration must still identify a real runnable check.

### Concrete violation, clean and real subjects

For the audit privacy prohibition, a known-bad fixture contains `{"event":"account-opened","ssn":"123-45-6789"}`. A separate known-clean fixture contains `{"event":"fixture-clean","customer_ref":"redacted-control"}`. The actual product output at `artifacts/audit.json` contains its own distinct event/customer-reference data. Never include a real person's identifier; this bad value is synthetic test data.

The existing project negative check must read its injected subject and assert the prohibition, for example:

```python
import json, os, re, unittest
from pathlib import Path

class AuditPrivacy(unittest.TestCase):
    def test_no_raw_ssn(self):
        subject = Path(os.environ["ENGINEER_PROHIB_SUBJECT"])
        event = json.loads(subject.read_text(encoding="utf-8"))
        self.assertNotRegex(json.dumps(event), r"\b\d{3}-\d{2}-\d{4}\b")

if __name__ == "__main__":
    unittest.main()
```

The violation run must fail this assertion, the clean run must execute and pass it, and the real run must execute and pass it. Syntax/import errors, zero tests, missing reports, stale reports and timeout never count as RED proof. If this check does not already exist, authoring it requires the ordinary owned implementation assignment; a prose example is not evidence it ran.

For lint-rule proof, use the project's actual semantic rule and an AST-relevant bad/clean pair. A path rule might reject computed `path.join(root, "..", "private", name)` while permitting `path.join(root, "public", name)`; the control must genuinely exercise that configured rule, not just contain a forbidden word in a comment or string. For `local/no-source-grep`, inspect the installed rule's actual AST/path-construction trigger, build the corresponding violating expression and a clean control, inject `{subject}`, and require the exact rule ID in the fresh ESLint JSON. Do not replace semantic proof with grep counts or assume every path literal triggers the rule.

### Fail-closed result consumption

A genuine successful three-stage proof returns `located: true`, `proved: true`, `valid: true`, `disposition: green` and actual `observations`. A missing check, conflicting descriptor, missing control, equal subjects, absent expected assertion/rule, zero tests, invalid report, timeout or actual real failure returns the explicit `unprovable-prohibition` failure (exit 2), `proved: false`, `valid: false`, `disposition: flagged`, its located state and reason/observations. Preserve that evidence; never promote it through a caller-supplied failFirst boolean. Run only when the user permits checks; deferred proof is pending and prevents a required test-tier obligation from passing.

## Output schema

The probe emits, per kept prohibition, an item of the form:

```
{ requirement_id, category, status, verification, resolution, reason, statement,
  check_kind?, check_target?, check_rule?, check_violation_fixture?, check_clean_fixture? }
```

where `statement` is the must-NOT sentence and `category` is the values/safety/ethics class
(`values`, `fairness`, `privacy`, `transparency`, `safety`, …). The optional **flat-scalar
`check_*` descriptor** (#1278) is present only on a resolved `test`-tier prohibition carrying a
wired check: `check_kind` (`test-command` | `lint-rule`), `check_target`, and `check_rule` (lint-rule
only). The Python `spec.prohibition-project` producer preserves these obligation fields;
`spec.prohibition-proof` consumes the actual configured descriptor and both controls as described
above. Projection alone does not prove execution or a passing prohibition. Plus a
coverage summary:

```
coverage: { applicable, resolved, unresolved, byVerification: { test, judgment } }
```

`applicable` is the number of kept prohibitions, `resolved` = closed (`resolved` +
`dismissed`) status items, `unresolved` is the remainder, and `byVerification` breaks the
`resolved`-status items down by tier (`{ test, judgment }`). This JSON is the stable contract
both the reference implementation and any third-party port emit.

## Generic mapping (requirements → checks → verifier)

| Host structure | "requirement" | a `resolved`/`test` prohibition becomes | a `resolved`/`judgment` prohibition becomes |
|----------------|---------------|------------------------------------------|----------------------------------------------|
| GSD SPEC | a SPEC Requirement | a SPEC acceptance criterion (marked prohibition) that `plan-phase` lifts into `must_haves.prohibitions` | a `must_haves.prohibitions` item routed to judgment review |
| Gherkin feature | a Scenario | a negative `Then` assertion / tagged negative scenario | a tagged scenario routed to manual review |
| OpenAPI operation | an operation | a contract test asserting the forbidden behavior never occurs | a documented constraint flagged for review |
| Docstring contract | a documented behavior | a negative assertion in the contract test | a documented must-NOT for reviewers |

The portable invariant: a `resolved`/`test` prohibition produces **a checkable negative the
verifier iterates over** (GSD: a `must_haves.prohibitions` item with a test); a
`resolved`/`judgment` prohibition produces a recorded intent routed to judgment review. An
`unresolved` prohibition is an explicit assumption the downstream planner must surface, not
silently drop.

## Worked example (streak-reminder)

A single requirement to send a daily habit reminder. The edge-probe sees a `stateful`
requirement and asks about idempotency; the prohibition-probe asks the adversarial question
and surfaces what the reminder must never *become*. Stage 1 over-produces ("must not spam",
"must not throw on a deleted habit", "must not use shaming framing"); Stage 2 drops the
routine-engineering items and keeps the one genuine values prohibition:

```json prohibition-probe:01-streak-reminder/expected.json
{
  "items": [
    {
      "requirement_id": "R1",
      "category": "values",
      "status": "resolved",
      "verification": "judgment",
      "resolution": null,
      "reason": null,
      "statement": "MUST NOT use shaming, guilt, or loss-aversion streak framing (e.g. \"Don't lose your streak!\") — the reminder must encourage without penalty framing"
    }
  ],
  "coverage": { "applicable": 1, "resolved": 1, "unresolved": 0, "byVerification": { "test": 0, "judgment": 1 } }
}
```

The kept prohibition is `judgment`-tier: "manipulative framing" cannot be reduced to a
mechanical test, so it records intent and routes to judgment review — but it is now an
explicit acceptance criterion the spec must clear, not an unwritten assumption.

## Worked example (clean-utility)

A pure utility requirement — "deduplicate a list of integers" — has no user-facing surface,
no values/safety/ethics dimension. Stage 1 still over-produces ("must not mutate the input",
"must not change order"), but every candidate is routine engineering that Stage 2 drops (and
the edge-probe already owns). The correct precision outcome is an empty prohibition list — a
zero, not a false positive:

```json prohibition-probe:02-clean-utility/expected.json
{
  "items": [],
  "coverage": { "applicable": 0, "resolved": 0, "unresolved": 0, "byVerification": { "test": 0, "judgment": 0 } }
}
```

This is the precision discipline that keeps the probe from crying wolf: a utility with no
intent surface produces zero prohibitions, so a non-empty list always carries signal.

## Worked example (multi-prohibition)

A loan-decision requirement is the high-stakes case: it surfaces several distinct
prohibitions across categories. Stage 1 produces a long list including canon items
(prototype-pollution, generic GDPR retention) that canon-referral breadcrumbs out; Stage 2
keeps the three bespoke values/safety items — a `fairness` constraint, a `privacy` constraint
(`test`-tier, mechanically checkable against the audit log), and a `transparency` constraint:

```json prohibition-probe:03-multi-prohibition/expected.json
{
  "items": [
    {
      "requirement_id": "R1",
      "category": "fairness",
      "status": "resolved",
      "verification": "judgment",
      "resolution": null,
      "reason": null,
      "statement": "MUST NOT use protected attributes (race, gender, age, national origin) or their proxies (zip code, name) in the loan decision or rate"
    },
    {
      "requirement_id": "R1",
      "category": "privacy",
      "status": "resolved",
      "verification": "test",
      "resolution": null,
      "reason": null,
      "statement": "MUST NOT store raw PII / financial secrets (SSN, full account or card numbers) in plaintext in the audit log"
    },
    {
      "requirement_id": "R1",
      "category": "transparency",
      "status": "resolved",
      "verification": "judgment",
      "resolution": null,
      "reason": null,
      "statement": "MUST NOT mislead or omit the true rate/APR/terms in the explanation; an adverse decision must state the real principal reason (adverse-action)"
    }
  ],
  "coverage": { "applicable": 3, "resolved": 3, "unresolved": 0, "byVerification": { "test": 1, "judgment": 2 } }
}
```

The `privacy` row is `test`-tier — "no raw SSN in the audit log" is a mechanical assertion —
while `fairness` and `transparency` are `judgment`-tier. The byVerification rollup
`{ test: 1, judgment: 2 }` is the count-preserved breakdown of the three `resolved`-status
items. Each worked-example block above is kept byte-for-byte (parsed-JSON) identical to its
fixture under `engineer/references/prohibition-probe-fixtures/` by
`prohibition-probe fixture comparison`, so the doc and the reference data cannot
silently drift.

## Python runtime boundary

The Python implementation is `engineer/bin/lib/probes.py`: `prohibition_project(args)` and `prohibition_proof(args)` own the actual projection and proof operations. `spec.section` and `spec.edge-probe` remain the section/shape interfaces. Model-driven recall and precision stay separate from deterministic projection and observed proof. Preserve all complete worked JSON examples above and the six edge examples in edge-probe.md; do not replace them with a summary. Fixture consistency is evidence only after the actual authorized comparison runs.
