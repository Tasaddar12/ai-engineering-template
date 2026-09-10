---
tier: contract
authority: agent
title: Review a proposal or result
links: [AMD-002]
---
> Contract: follow these steps within the approved scope.

# Review a proposal or result

## Purpose

Challenge unsupported premises and concrete defects independently of
implementation.

## Inputs

A stable subject, current contracts, approved outcome, review type and
authorized checks.

## Gates

Use [review-ready](../gates/review-ready.md); additional execution follows [action-approved](../gates/action-approved.md).

## Steps

1. For a proposal, use plan-checker. For implementation, use a reviewer
   independent of the implementor and preferably in a fresh context when
   authorized and available. Otherwise disclose a separate self-review pass;
   it cannot satisfy a mandatory external-review requirement.
2. Prepare the review packet: PLAN/FIX, PROJECT, RULES, truth-map, current
   specs, accepted ADRs, user documentation, surrounding code and relevant
   tests.
3. For cold review, exclude research briefs, earlier round logs and
   implementor/scribe reports. Use the filtered diff below; do not follow links
   into excluded evidence.
4. Inspect contracts and outcomes before code, then the entire relevant diff and
   commit slices. Check invariants and stale-document workaround signatures.
5. Run agreed checks and return actionable findings: path/location, concrete
   failure, expected outcome, severity and evidence. Say CANNOT_VERIFY when
   required evidence is missing.
6. The coordinator records the report. Bug-reviewer can inspect earlier evidence
   to triage recurrence; the cold reviewer cannot.
7. Recheck affected evidence after changes. Report degraded independence if a
   fresh context was unavailable instead of claiming cold review.

## Output and handoff

Use review.md. The packet's diff command is:

```text
git diff <base>...HEAD -- . ':(exclude).ai/research/' ':(exclude).ai/state/orchestration/'
```

Supply the actual base and inspect pending changes separately when reviewing an
uncommitted draft. Exclusions concern review-process artifacts, not product
files.
The coordinator separately validates any excluded operating documents changed
by the work so exclusion never becomes an unreviewed-change loophole.

## Stop conditions

Do not alter the reviewed result or approve to end a loop. Minor preferences do
not block; missing required evidence does.
