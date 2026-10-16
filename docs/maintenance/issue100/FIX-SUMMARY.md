---
phase: issue100-maintenance
plan: pr89-corrections
subsystem: workflow
tags: [parallel-status, security-tracking, issue-audit, instruction-contracts]
issue_refs:
  - https://github.com/Tasaddar12/ai-engineering-template/issues/100
  - https://github.com/Tasaddar12/ai-engineering-template/issues/87
requires: []
provides:
  - Deterministic phase checklist lookup and stable provider-verified body headings
  - Verifier-owned issue-link audit with explicit fresh dispatch in ship
  - Actual host wait intervals and confirmed-stop-before-reassignment rules
affects: [planning, execution, verification, shipping]
actuals:
  tasks: 2
  commits: 3
plan_head_before: d48d10d9fa9fb33dc05ad8552329aceee4e7d5cc
tech-stack:
  added: []
  patterns: [canonical procedures with concise workflow seams]
key-files:
  created: [docs/maintenance/issue100/FIX-SUMMARY.md]
  modified: [.ai/RULES.md, AGENTS.md, .ai/references/git-workflow.md, .ai/references/parallel-status.md, .ai/runtime/TEMPLATE-CONTRACT.md, .ai/templates/issue.md, .ai/agents/code-reviewer.md, .ai/agents/verifier.md, .ai/workflows/execute-phase.md, .ai/workflows/verify-work.md, .ai/workflows/ship.md, tests/test_parallel_status_contract.py, tests/test_threat_tracking_contract.py]
key-decisions: []
patterns-established: [provider-verified immutable checklist headings, observed host lifecycle]
requirements-completed: []
acceptance: [ISSUE87-6, ISSUE87-7]
documentation: [.ai/references/git-workflow.md, .ai/references/parallel-status.md, .ai/runtime/TEMPLATE-CONTRACT.md, .ai/templates/issue.md, .ai/RULES.md, AGENTS.md, .ai/agents/code-reviewer.md, .ai/agents/verifier.md, .ai/workflows/execute-phase.md, .ai/workflows/verify-work.md, .ai/workflows/ship.md]
coverage:
  - id: D1
    description: Checklist identity, routing, assessment links and independent audit dispatch
    verification:
      - kind: unit
        ref: tests/test_threat_tracking_contract.py
        status: pass
    human_judgment: false
  - id: D2
    description: Host observations, changed-row updates and confirmed worker stop
    verification:
      - kind: unit
        ref: tests/test_parallel_status_contract.py
        status: pass
    human_judgment: false
duration: unavailable (start timestamp was not captured)
completed: 2026-10-16
status: complete
---

# Issue 100: PR 89 correction summary

Deterministic security checklist routing, stable body-heading links, verifier-owned
audits and actual host observations correct the confirmed PR 89 findings.

## Authority and scope

The delegated user instruction was: "Go ahead and fix the findings for PR 89."
This continues the existing issue87 maintenance plan without adopting-project
`.planning` records. The coordinator supplied the later item-2 addendum from
[issue100](https://github.com/Tasaddar12/ai-engineering-template/issues/100#issuecomment-6221536882):
use stable `###` headings in the checklist issue body, heading-anchor URLs, no
comment link label, and explain that renaming a heading breaks its link. This
supersedes the earlier comment-entry request; no comment-entry requirement ships.

Related PR: [PR89](https://github.com/Tasaddar12/ai-engineering-template/pull/89).
Base: `worker-pr89-issue100` at `d48d10d9fa9fb33dc05ad8552329aceee4e7d5cc`.
Context usage: unavailable.

## Changes

- Exact phase-checklist title/label lookup precedes semantic risk search. All new
  planned risks, including accepted/deferred, use the checklist by default; existing canonical matches and
  closed unresolved reopening-authority blockers keep their identities.
- Each risk has a stable body `###` heading and provider-verified anchor URL.
  Renames require reference repair/readback. Checklist tracking links owning PLAN
  assessment and mitigation; six-column registers remain in their PLANs. Standalone
  issues retain assessment, remediation and secure-check fields without requiring a PLAN.
- Canonical audit duties and evidence remain in git-workflow. verify-work assigns
  them to a fresh non-author verifier. Optional code review supplements that audit.
  Ship explicitly dispatches a verifier for missing/stale audit evidence, supplies
  current source/head/body/link/readback inputs, joins it and rechecks publication.
  The existing current-audit/provider-readback merge gate remains in force.
- One interval means one actual bounded host wait call/return. Blocking hosts
  show dispatch/join tables without invented observations. Intermediate updates
  show changed rows. Timeout alone does not establish exit or authorize termination;
  reassignment requires confirmed stop and preservation/continuation checks.
- Both contract modules use real sections, steps, schemas, short semantic cues
  and negative mutations. Embedded original paragraphs and long prose snapshots
  were removed while preserving disclosure, identity, lifecycle and audit coverage.

## Checks

Interpreter: `D:\Codex\2026-10-16\task-7\python-runtime\python.exe`.
Tested source: assigned base plus this committed owned correction diff; the
summary was written after these source checks. All tests were ordinary local
unittests; no benchmarks or native security probes were run.

| Command suffix after `python -m unittest discover -s tests -p` | Result |
|---|---|
| `test_parallel_status_contract.py` | 5 tests, OK |
| `test_threat_tracking_contract.py` | 16 tests, OK |
| `test_issue_format.py` | 17 tests, OK |
| `test_workflow_links.py` | 4 tests, OK |
| `test_agent_sources.py` | 16 tests, OK |
| `test_phase_issues.py` | 38 tests, OK, skipped=1 |

The initial phase-issues run failed all 38 fixtures at `git init` because Git
could not write `.git/config` in the sandbox's default temporary directory.
The ordinary rerun with `TEMP` and `TMP` set to the explicitly writable
`C:\Users\killi\AppData\Local\Temp` passed (114.270s, one platform skip).
`git diff --check` passed with no whitespace errors.

## Deviations and threat outcomes

The item-2 heading addendum was incorporated before final checks. No product
trust boundary, endpoint, authentication path or dependency was added, and no new
threat was identified in this documentation/contract-test scope. Existing risk
identity, safe disclosure, provider fallback and closure authority remain required.
No other owned scope was expanded. No PR97/99 action, provider implementation,
push, external write, merge or cleanup was performed by this worker.

## Remaining and coordinator reconciliation

Local correction work is complete. Renewed independent review, integrated-revision
verification and full exact-tip Ubuntu/Windows CI remain Pending with the
coordinator; local passes do not claim those results. The coordinator also owns
the separate PR76 composition check and its provider-file conflict evidence.
There is no remaining implementation blocker or requested human decision.
Integrate this owned commit, record the final revision and update PR89/issue100
evidence without inventing adopting-project state or closing issues.

## Self-Check: PASSED

All 14 changed paths are within the supplied ownership, the six focused suites
ran with the results above, and no `.planning` file was created or edited.
The exact commit hash is returned to the coordinator after the local commit;
Git records this summary and its source changes together.

## Joined-review repair

Repair base: `99e2aa673692b9ac3e97971539640249ba5fdd16`, following the
coordinator's joined independent review. The same correction plan and ownership
continue; no adopting-project records or additional product scope were introduced.

| Finding | Disposition and evidence |
|---|---|
| CR-01 BLOCKER | RULES Interruption and recovery now distinguishes a host wait timeout from actual exit and requires host-confirmed stop before dirty-file inspection or reassignment. It links the canonical stop rule and continuation procedure, preserving dirty work, limits and independent work. Recovery-section mutations cover this seam. |
| CR-02 BLOCKER | The generic Security risk block again includes severity/rationale/uncertainty, mitigation or safe next action, requested remediation and an observable secure check. Standalone issues require no PLAN. Only checklist containers/entries substitute PLAN assessment/mitigation/verification links. Mutations independently require the standalone fields and scoped substitutions. |
| CR-03 BLOCKER | Mandatory execute-phase aggregation now links the canonical default for every new planned risk instead of saying checklist use is optional. Matching canonical trackers and distinct unplanned standalone tracking remain explicit. Step-scoped mutations reject optional/default loss. |
| DV-01 | Canonical routing, the runtime contract, issue guidance and execution now cover ALL new planned risks, including accepted/deferred risks. Existing canonical issue identities retain precedence. Negative scope mutations cover both canonical routing and the runtime seam. |

The latest item-2 `###` body-heading anchor addendum is preserved unchanged in
behavior: verified provider anchors, stable headings, rename repair/readback and
no comment-link label. No combined or duplicate PLAN register was introduced.

The new real-contract checks failed before these repairs: parallel reported the
missing recovery stop gate, and threat routing reported the standalone/template,
execution-default and planned-scope gaps. After correction:

| Focused suite | Repair result |
|---|---|
| `test_parallel_status_contract.py` | 6 tests, OK |
| `test_threat_tracking_contract.py` | 18 tests, OK |
| `test_workflow_links.py` | 4 tests, OK |
| `test_issue_format.py` | 17 tests, OK |

Commands used the same interpreter and `-m unittest discover -s tests -p` prefix
recorded above. Phase-issues were not repeated for this instruction-only repair;
their earlier result is historical evidence, not a claim about the new revision.
The revised test helper scopes mutations to the exact recovery section,
aggregate step or runtime section. `git diff --check` passed.

Worker implementation commits: `c24930d21f33b6256d68cbc61da828e671b9af7a`
plus this repair commit (returned to the coordinator after commit). The total
three-commit range from the immutable original base includes the coordinator's
`99e2aa6` maintenance-context commit. Renewed independent review and current-tip
Ubuntu/Windows CI remain Pending; the coordinator owns that evidence and PR76
composition. No implementation blocker remains.
