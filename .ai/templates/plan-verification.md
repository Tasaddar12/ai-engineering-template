---
tier: log
authority: agent
title: Plan verification
---
> Log: preserve evidence; append corrections.

# Plan verification

Subject / revision / base: {{ exact_subject }}

Evaluator, time, environment and authority: {{ evaluation_context }}

## Current contract and observed behavior

| Criterion / invariant | Check | Observed result | Outcome | Evidence |
| --- | --- | --- | --- | --- |
| {{ spec_criterion }} | {{ command }} | {{ actual }} | {{ result }} | {{ ref }} |

Use PASS, FAIL or NOT_RUN per check; N/A requires a scope-based reason.
Include approved outcomes; predicted steps alone do not define correctness.

## Contract changes reconciliation

For each create/amend/retire/decision promise, show the actual record and
whether it was delivered or explicitly reconciled. For FIX, link before/after
proof and demonstrate that required behavior was not silently changed.

## Review, defects and record drift

Link review with its independence disclosed, confirmed FIX and suspected INTAKE evidence.
Check current tense, duplication and unsupported claims as well as code.

## Result and limits

Overall: {{ verified_or_defects_found_or_cannot_verify }}

Missing required evidence cannot yield verified. State inspection boundaries and
the exact next action. Verification supplies no repair or merge authority.

<!-- Returned evidence report. Grade behavior against current contracts,
not plan checkbox completion. Historical records receive appended evidence. -->
