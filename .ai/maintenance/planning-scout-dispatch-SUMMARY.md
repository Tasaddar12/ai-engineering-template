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
- One authorized template-maintenance slice; no adoption records or phase created.
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

## Checks

All checks ran against the owned slice before its commit:

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

## Deviations and remaining work

- No scope deviation or implementation blocker. No known implementation stubs.
- Benchmarks and full-suite runs were excluded from this assignment.
- Independent review and publication remain coordinator-owned; this worker does
  not merge, switch/create branches, push or publish.
- No shared planning-state reconciliation is needed: adopting project identity,
  phase position, roadmap, requirements and decisions remain unfilled.
- Author changes and this summary are committed together as one meaningful slice;
  the actual hash is returned to the coordinator after Git confirms it.

## Self-Check: PASSED

All 10 owned deliverable paths exist and resolve within the assigned root.
The root, branch and starting revision matched the assignment immediately before
staging. Author checks and diff validation passed. Final commit identity,
deletion check and clean status are verified after committing and returned with
the actual Git hash.
