---
id: PLAN-003
kind: plans
title: Flat framework layout, explicit workflows and delivery to main
status: in-progress
tasks:
- TASK-064
- TASK-065
- TASK-066
- TASK-067
- TASK-068
- TASK-069
- TASK-070
- TASK-071
- TASK-072
- TASK-073
- TASK-074
- TASK-075
- TASK-076
- TASK-077
- TASK-078
- TASK-079
- TASK-080
- TASK-081
- TASK-082
- TASK-083
- TASK-084
- TASK-085
- TASK-086
- TASK-087
- TASK-088
- TASK-089
- TASK-090
- TASK-091
- TASK-092
features:
- FEATURE-008
- FEATURE-009
- FEATURE-010
- FEATURE-011
- FEATURE-012
- FEATURE-013
- FEATURE-014
- FEATURE-015
- FEATURE-016
- FEATURE-017
execution_authorized: true
validation_deferred_by_user: true
delivery_target: main
obsolete_content_cleanup_authorized: true
implementation_models:
  subagents: gpt-5.6-sol/xhigh
  reviewers: gpt-6-astra/xhigh
---
# PLAN-003 — Implement and deliver the framework

The user explicitly directs implementation of all remaining features, deletion of obsolete data, and delivery to main. Their latest instruction supersedes prior preservation, migration, test-suite, compatibility-probe and validation gates for this implementation pass. Do not run tests or environment verification. Fix straightforward bugs during implementation and record unresolved bugs for later. Do not retain old plans, runs, reviews or rejected source as compatibility inputs. Existing Git history is not rewritten.

## Current delivery

Use the existing managed implementation checkout, with bounded parallel workstreams on dedicated branches where useful. Keep authors on their assigned branch and merge the finished implementation to main. Record testing as deferred, never as passed. No new planning or review loop is required before implementation continues. Main already contains the prior Plan-003 planning delivery through PR #1.

## Required behavior

- Every authored Python module is directly in src while the installed import namespace remains ai_engineering.
- Reusable defaults live at root agents, templates, workflows, constraints and framework.yaml; installation copies them into a target project's .ai.
- Planning intent and implementation permission are separate. Coordinator records current plan/action/revision/scope authority; dispatch and replay enforce it. Feature drafts and phase-preserving hard-block metadata are supported.
- Constraints are focused coding, commands, permissions and limits documents. Commands use the central runner and cannot widen their assigned policy.
- Agent Markdown files contain inline provider, model and reasoning settings. Implementation uses GPT-5.6 Sol/xhigh; critical review uses GPT-6 Astra/xhigh.
- Fixed managed worktree ownership, provider confinement, workflow routing, validation and repair interfaces, PR-to-main delivery and exact branch/worktree cleanup are implemented.
- A usable initializer and CLI expose the installed workflows and resumable coordinator operations.
- Delete obsolete code, framework history, stale copies and branches. Do not implement legacy data migrations merely to preserve abandoned data.

## Work references

- [FEATURE-008](../../features/in-progress/FEATURE-008.md): TASK-064, TASK-065
- [FEATURE-009](../../features/in-progress/FEATURE-009.md): TASK-066, TASK-067, TASK-068
- [FEATURE-010](../../features/in-progress/FEATURE-010.md): TASK-069, TASK-070, TASK-071
- [FEATURE-011](../../features/in-progress/FEATURE-011.md): TASK-072, TASK-073, TASK-074
- [FEATURE-012](../../features/in-progress/FEATURE-012.md): TASK-075, TASK-076, TASK-077
- [FEATURE-013](../../features/in-progress/FEATURE-013.md): TASK-078, TASK-079, TASK-080
- [FEATURE-014](../../features/in-progress/FEATURE-014.md): TASK-081, TASK-082, TASK-083
- [FEATURE-015](../../features/in-progress/FEATURE-015.md): TASK-084, TASK-085, TASK-086
- [FEATURE-016](../../features/in-progress/FEATURE-016.md): TASK-087, TASK-088, TASK-089
- [FEATURE-017](../../features/in-progress/FEATURE-017.md): TASK-090, TASK-091, TASK-092

## Parallel implementation contract

All workers remain in the assigned plan-003-intent checkout and branch, with disjoint source ownership. No worker runs tests, lint, type checks, packaging verification or compatibility probes. No worker commits, changes Git state, installs dependencies or edits canonical .ai. Scratch belongs only to its named .ai/local subdirectory.

Core worker owns src/artifacts.py, state.py, planning_intent.py, planning.py, handoffs.py, review.py, errors.py and orchestrator.py. It removes legacy migration machinery and implements forward-only planning, execution, resumption, bugfix and recovery coordination. Public orchestrator functions are status(root), create_plan(root,title,scope), revise_plan(root,plan_id,**changes), implement_plan(root,plan_id,*,validate=False,deliver=True,resume=False), and implement_bug(root,bug_id,*,validate=False,deliver=True). Return structured dictionaries for workflow outcomes; preserve existing ArtifactStore and StateStore APIs.

Runtime worker owns src/agents.py, config.py, constraints.py, runner.py, git.py, delivery.py, cleanup.py, containment_linux.py and containment_windows.py, plus root constraints/. Preserve existing agents.dispatch and Git APIs. Add delivery.deliver(root,worktree,branch,*,base='main',repository=None,review=None,run_tests=False) and cleanup.retire_worktree(root,worktree,branch,merged_revision,*,base='main',remote=True). load_config keeps framework, constraints, models and project/commands names for callers; constraints comes from the four focused files and project/commands exposes the named commands. Models are read from inline agent Markdown, not a global models file. Root constraints/commands.yaml contains named commands alongside rules. Provider failures remain explicit; implement actual command/Codex confinement paths rather than claiming an attestation is confinement.

Packaging worker owns src/__init__.py, __main__.py, cli.py, project.py, templates.py, workflows.py and optional build_backend.py, plus root agents/, templates/ and workflows/. It adds project.initialize(root,**options), workflows.route(root,name,subject=None,**options), installable flat packaging and the ai/python-module CLI. CLI delegates core operations to the public orchestrator functions above and delivery/cleanup operations to runtime helpers. Agent Markdown preserves role/permission/template schema and includes provider, model, reasoning and capability inline. All roles use gpt-5.6-sol/xhigh except critical_review gpt-6-astra/xhigh. Root file edits (pyproject.toml, framework.yaml, MANIFEST.in if needed, README) are emitted as exact files in .ai/local/packaging/root-proposals for the coordinator to apply promptly.

The coordinator owns root operating/docs files, Git and canonical .ai, applies root proposals, removes obsolete project copies and records known unresolved defects. Integration adjustments return to the owner of the affected source file. Avoid placeholders: implement the usable workflows now, with unverified edge cases recorded for later.

Runtime implementation reference: `.ai/local/runtime/codex-reference.yaml` contains the already-used Codex CLI recipe and known GitHub authentication constraints. It is a code reference, not a request to run any probes.
