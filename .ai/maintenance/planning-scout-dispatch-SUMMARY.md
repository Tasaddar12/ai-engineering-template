---
status: complete
subsystem: workflow-template
tags: [planning, scout, evidence, dispatch]
plan_head_before: a9c2cb970cce93c3f0d7075d59377c3db0b3c123
requirements-completed: []
acceptance: []
documentation:
  - .ai/references/scout-dispatch.md
  - .ai/workflows/plan-phase.md
  - .ai/commands/plan-phase.md
  - .agents/skills/plan-phase/SKILL.md
  - .ai/agents/phase-preparer.md
  - .ai/agents/researcher.md
  - .ai/references/universal-anti-patterns.md
key-files:
  created: [.ai/maintenance/planning-scout-dispatch-SUMMARY.md]
  modified:
    - .ai/references/scout-dispatch.md
    - .ai/workflows/plan-phase.md
    - .ai/commands/plan-phase.md
    - .agents/skills/plan-phase/SKILL.md
    - .ai/agents/phase-preparer.md
    - .ai/agents/researcher.md
    - .ai/references/universal-anti-patterns.md
    - tests/test_efficiency_contracts.py
    - tests/test_agent_sources.py
completed: 2026-10-09
---

# Planning scout dispatch maintenance summary

Planning discovery and repeatable evidence extraction now require configured
exact scouts before owner searches, with reusable packets and capacity-safe
coordinator fallback.

## Assignment and base

- Root: `D:/Codex/2026-10-09/task-44/scout-routing`
- Branch: `fix/require-planning-scouts`
- Starting revision: `a9c2cb970cce93c3f0d7075d59377c3db0b3c123`
- Authorized template-maintenance work and its CR-01 correction; no adoption
  records or phase created.
- Context usage: unavailable. No estimate or provider-token actuals claimed.

## Accomplishments

- Shared reference defines unknown file/symbol/history/skill location searches,
  repository inventories and requested repeated extraction/classification/summary
  as mandatory scout work. Named-source reasoning, conflict confirmation,
  necessary verification and known runtime metadata queries remain owner reads.
  Matching question/revision/scope/input evidence is reused; compatible fields
  for one bounded scope are batched, with packet IDs/paths passed downstream.
- Plan workflow declares scout in its header, available roles and required reads;
  gates evidence before research/planning; passes bounded evidence contracts to
  researcher, preparer, checker and mapper, including revisions/continuations.
- Every planning-worker return handles scout_request before required-file,
  plan-count, coverage or verdict checks. Full capacity counts queued/open workers,
  stops scheduling, joins/retires completed roles and requires the requester to
  return/release capacity before coordinator dispatch. Saved paths/commits/progress
  resume via actual host continuation or fresh assignment without duplicate writers.
- Scout requests do not consume context-partial, research-incomplete or revision
  counters. SCOUT UNAVAILABLE reports missing fields and dependent steps;
  required repository evidence cannot become an ASSUMED precondition or dependent
  completion after ordinary research partial limits.
- Replaced preparer SUMMARY/symbol/map/skill discovery and researcher capability,
  skill, dependency and test-infrastructure inventory instructions. Preserved the
  preparer's selective named-source discovery confirmation. Command and skill
  remain identical; scout joins the exact-role anti-pattern allowlist.
- Canonical role files remain the installer source. No hand-maintained generated
  host copy, runtime change, capability setting or model/effort change was needed.

## Initial slice checks

These checks ran against the initial owned slice before commit `952a8e6`:

| Command/check | Result |
|---|---|
| `python -m unittest discover -s tests -p test_agent_sources.py` | PASS: 14 tests |
| `python -m unittest discover -s tests -p test_efficiency_contracts.py` | PASS: 11 tests |
| `python -m unittest discover -s tests -p test_workflow_links.py` | PASS: 3 tests |
| `test_install.InstallerTests.test_native_agent_models_and_direct_roles_install_without_hooks` | PASS: Codex and Claude role/rendered-source parity |
| `test_install.InstallerTests.test_host_profiles_install_complete_selected_workflow` | PASS: Codex and Claude installed host profiles |
| `git diff --check` | PASS |

The two existing installer tests ran together (2 tests, 25.024 seconds) using:

```powershell
python -c "import sys, unittest; sys.path.insert(0, 'tests'); suite = unittest.defaultTestLoader.loadTestsFromNames(['test_install.InstallerTests.test_native_agent_models_and_direct_roles_install_without_hooks', 'test_install.InstallerTests.test_host_profiles_install_complete_selected_workflow']); result = unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(not result.wasSuccessful())"
```

The new static contracts cover concrete discovery boundaries, evidence-gate and
return-check ordering, saved-progress/capacity/resume/unavailable obligations,
batching and named-file exceptions. They do not enforce future agent behavior.

## CR-01 identity/currentness correction

Independent code review of `952a8e6cb6cf2faccd19f4aaa7ac1269d430f0c1` found one
accepted blocker: worker identity/revision placeholders had no explicit capture
procedure, and continuations reused evidence without reconciling author commits
or dirty input currentness. No other defects were reported in that frozen review.
This corrective slice starts from that exact revision and changes only the shared
reference, planning workflow, focused efficiency regression and this summary.

- The coordinator captures actual absolute checkout, branch, observed HEAD and
  relevant dirty/input content identifiers before every evidence/worker dispatch,
  follow-up, revision, continuation and resume, using existing native Git/host
  metadata and hashing. It binds concrete prompt values, retains a unique logical
  assignment ID/exact role and per-call continuation lineage, and preserves the
  original parent ownership, snapshot and allowed-progress context.
- Author commits/progress trigger snapshot refresh before the next dispatch.
  Packet question/revision/scope/input tuples include dirty content identity;
  stale evidence retains its original labels. Only required uncovered/stale
  fields go to bounded compatible scout requests. Relevant inputs remain frozen
  through join, where HEAD and content identities are rechecked.
- Nested requester progress reports its actual snapshot and saved owned
  commits/inputs. The coordinator validates permitted changes against the
  original parent assignment, allows verified owned committed progress instead
  of demanding stale initial HEAD, validates request evidence at its snapshot,
  preserves edits and refreshes the tuple before resume.
- No runtime API/schema, settings, model, capability or generated host role was
  added. The new identifiers and snapshot fields are prompt handoff context only.

Correction checks:

| Command/check | Result |
|---|---|
| `python -m unittest discover -s tests -p test_efficiency_contracts.py` | PASS: 12 tests |
| `python -m unittest discover -s tests -p test_workflow_links.py` | PASS: 3 tests |
| `python -m unittest discover -s tests -p test_agent_sources.py` | PASS: 14 tests |
| `test_install.InstallerTests.test_native_agent_models_and_direct_roles_install_without_hooks` | PASS: 1 test, both hosts, 16.985 seconds |
| `git diff --check` | PASS |

The focused static regression checks capture/binding before each worker call,
evidence-gate dispatch and continuation/revision/resume refresh, retained lineage,
dirty identities, verified owned progress and preservation of stale packet labels.
It verifies the authored contract, not future agent compliance. The installer
check used the same unittest-loader command as the initial checks, with only the
role-parity test selected. Full-suite runs and benchmarks remain excluded.
Fresh independent review of the correction remains coordinator-owned.

## Deviations and remaining work

- No scope deviation or implementation blocker. No known implementation stubs.
- Benchmarks and full-suite runs were excluded from this assignment.
- Independent review and publication remain coordinator-owned; this worker does
  not merge, switch/create branches, push or publish.
- No shared planning-state reconciliation is needed: adopting project identity,
  phase position, roadmap, requirements and decisions remain unfilled.
- Initial author changes and summary were committed together as `952a8e6`.
  The correction and updated summary form a second meaningful slice; its actual
  hash is returned after Git confirms it. CR-01 correction awaits independent
  re-review and coordinator publication.

## Self-Check: PASSED

All 10 owned deliverable paths exist and resolve within the assigned root.
The root and branch matched the assignment; the correction starts at `952a8e6`.
Author checks and diff validation passed. Final commit identity,
deletion check and clean status are verified after committing and returned with
the actual Git hash.
