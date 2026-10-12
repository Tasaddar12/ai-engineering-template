---
maintenance: actionable-uat
status: complete
acceptance: []
requirements-completed: []
documentation:
  - .ai/templates/issue.md
  - .ai/templates/UAT.md
  - .ai/workflows/verify-work.md
  - .ai/references/methods/verify-mvp-mode.md
  - .ai/agents/verifier.md
plan_head_before: 320574f9b3f07628789058e2aaccc7b6a7fc677d
---

# Actionable human acceptance scripts

**Concrete human actions and expected visible results now share one canonical UAT contract, with build preparation and provenance assigned to the maintainer.**

## Scope and identity

Standalone authorized template maintenance, preserving the unfilled adoption
skeleton. No phase, quick task, project identity or shared planning state was
created or updated.

- Worker root: D:/Codex/2026-10-12/task-15/uat-worker.
- Worker branch: codex/actionable-uat-worker.
- Starting revision: 320574f9b3f07628789058e2aaccc7b6a7fc677d, including PR #70's typed issue variants.
- Tasks: 3/3 (concrete template shape; aligned generation/ownership; checks and summary).
- Context usage: unavailable.

## Changes

- `.ai/templates/UAT.md` owns the exact entry URL/supplied launcher, short
  observable checklist, numbered real control/key actions, safe fixture values,
  expected visible results, PASS/FAIL/BLOCKED replies and actual human decision.
  AI/maintainer prepares builds, access, data, packages, provenance, evidence and
  bundles. A separate maintainer-owned record carries technical details without
  requiring the human to read or compare them. Examples are explicitly fictional;
  copied bodies contain visible prompts and no hidden HTML comments.
  For multiple tests, index guidance gives a numbered run order with descriptive
  linked names and one reporting location. Prepared Windows launchers require
  exact Win+R/paste-full-path/Enter actions; the maintainer selects the build.
- `.ai/templates/issue.md` preserves all five typed variants. The UAT variant
  uses that concrete script shape and a separate maintainer record reference;
  it retains the canonical headings/order and step/result table, with brief
  factual Context, terse Impact/scope and visible behavior checklist prompts.
  relevant bug reproduction now names the entry point and specific actions,
  inputs and expected results.
- `.ai/workflows/verify-work.md` prepares human scripts from the canonical
  template before reporting human blockers, including human checks retained in
  a gaps-found result. Its single issue-author ownership rule assigns one named
  author, explicit issue URL/number and owned draft per issue, prohibits concurrent
  edits and leaves review/publication with the authorized coordinator.
- `.ai/references/methods/verify-mvp-mode.md` separates the human walk-through
  from maintainer technical/coverage checks and links the same contract.
- `.ai/agents/verifier.md` minimally links direct human-check generation to the
  canonical script and keeps the verifier read-only.
- This summary records the bounded source change and worker evidence.

## Runtime evidence

Inspection of `.ai/runtime/phase.py:833` and
`.ai/runtime/lib/verification.py:23` confirms `verification.status` reads the
VERIFICATION report metadata, not UAT progress. The runtime exposes status,
report-path resolution and configured checks; it has no UAT result-recording or
case-selection verbs. The UAT guide now directs the coordinator to read/update
the session document and removes unsupported `--case`/`--note` instructions.
No runtime feature or command was added.

## Checks

Author checks use Python 3.13.14 on the assigned base plus the owned working-tree
changes. These are repository integration checks, not product human acceptance.

- `python -m unittest discover -s tests -p test_workflow_links.py -v`: PASS, 3 tests.
- `python -m unittest discover -s tests -p test_agent_sources.py -v`: PASS, 16 tests.
- `python -m unittest discover -s tests -p test_install.py -v`: PASS, 37 tests, 1 host symlink skip. This suite used its copied source fixture from before the final usability/layout clarification; it is not final-source template evidence.
- `python -m unittest discover -s tests -p test_todo_issues.py -v`: PASS, 31 tests, 1 skipped because symlink creation is unavailable on this Windows host.
- `git diff --check`: PASS; exact scoped diff and empty staged index inspected.
- Author inspection: five typed variants preserved; copied UAT body has no hidden
  HTML comments; unavailable/unverified actions stay blocked; human acceptance
  stays pending until actual feedback/decision. Runtime flags checked against
  the implementation above.
- Three focused existing installer tests (host profiles, installed guidance links,
  native role exports) passed; their fixture preceded the final canonical-layout
  restoration.
- `python C:/Users/killi/AppData/Local/Temp/actionable-uat-export-check.py D:/Codex/2026-10-12/task-15/uat-worker`: PASS. The transient author check reused the existing InstallerTests fixture on final source, compared the UAT issue's headings/order, table/result schema and Human acceptance fields with the assigned base, confirmed the other three untouched typed variant bodies remain identical, and checked that actual Codex and Claude exports preserve the final issue/session bodies and include their verification consumers. This is explicit author/export validation, not a publication gate.
- The final-source workflow-link rerun passed all 3 tests after the layout clarification.

Publication does not automatically enforce these template shapes: the TODO runtime
checks body safety, freshness and readback, not headings/order/tables. Direct issue
editing also requires author/coordinator shape review. No structural publication
validator or runtime enforcement was implemented or claimed.

## Commits and handoff

The single contract slice and required summary are committed together; its exact
hash is returned in the worker completion response and available in Git history.
The coordinator owns independent review, integration, push and the requested
draft PR. No worker push, publication, branch change, merge or benchmark.

## Decisions and deviations

The authorized maintenance assignment governs the summary location and bypasses
adopting-project lifecycle initialization. A minimal verifier wording change was
necessary because its direct generation format previously allowed vague actions
and said no separate file was created. No other scope changes.

## Known placeholders

Bracketed content in these reusable templates is intentionally unfilled, with
visible expected field shapes. Fictional example URLs, fixtures and source paths
are instructional only. They are not execution evidence or stubs in an adopting
product. No new endpoint, credential store or other security surface was added.

## Remaining and reconciliation

Coordinator independent review and draft publication remain. No product UAT was
run: this repository is the unfilled workflow template, with no adopting UI to
test. Future authors must check scripts against each actual delivered interface
and record missing entry points/functions as BLOCKED.

No shared position, progress, roadmap, requirements, project decisions or todos
need reconciliation. The coordinator may record this committed maintenance
result and its checks in the draft PR; human decisions remain with actual
reviewers. This assignment grants no cross-repository issue-edit authority.

## Self-Check: PASSED

All six owned files exist. The base and worker identity were verified before
writes. The source diff contains only the five assigned contract paths, with this
required summary added. Final commit and post-commit path/deletion checks are
reported in the completion response.
