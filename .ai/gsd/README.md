# Complete GSD authoring library

This library preserves **every template and all supporting agent, command,
reference, workflow, and context files** from
[GSD-Core revision c0b2a05](https://github.com/open-gsd/gsd-core/tree/c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977).
Read the selected full template when authoring or checking an artifact. Its
examples, counterexamples, rationale, field guidance, and consumer descriptions
are part of the instructions; do not replace them with a shorter local template.

## What is here

| Source directory | Local directory | Files |
|---|---|---:|
| `gsd-core/templates/` | [Templates](../templates/) | 40 |
| `agents/` | [Specialist definitions](agents/) | 64 |
| `commands/` | [Command definitions](commands/) | 72 |
| `gsd-core/references/` | [Methods and examples](references/) | 131 |
| `gsd-core/workflows/` | [Workflows and their step files](workflows/) | 177 |
| `gsd-core/contexts/` | [Context guides](contexts/) | 3 |

The counts include upstream compact variants and nested files. Both full and
compact variants are preserved exactly as provided; the presence of a compact
variant is not authorization to abridge another file. [LICENSE](LICENSE)
preserves the upstream MIT license and attribution.

## Read before execution

| Surface | Status and correct use |
|---|---|
| `.ai/templates/` | Active authoring sources; use the named upstream template and its local additive contract. |
| `.ai/commands/`, `.ai/agents/`, `.ai/runtime/phase.py` | Active local procedures, responsibilities, and execution tooling. |
| `.ai/gsd/commands/`, `agents/`, `workflows/` | Complete upstream supporting definitions. Read for methodology; they are not installed dispatchers. |
| `/gsd:*`, `/gsd-*`, upstream `Agent`, `Skill`, `AskUserQuestion` | Source host vocabulary. Resolve the capability through the local mapping below; do not claim these tools or commands are registered. |
| `gsd-tools.cjs`, GSD hooks, installer, state/schema generators | Upstream runtime examples, not installed or invoked by this import. Pinned implementation links are source evidence. |
| `.planning/config.yaml` | Active local execution settings: commands, routes, concurrency, and checks. |
| `.ai/templates/config.json` | Complete upstream GSD configuration template. Its settings are not accepted aliases for the local YAML runtime. |
| Upstream W019 registry, milestone locks, GSD state JSON, optional feature gates | Descriptions of upstream behavior. Local availability must be established from the local runtime and guides. |

Read [local adaptation decisions](../references/gsd-adaptation.md) and the
[local artifact contract](../runtime/TEMPLATE-CONTRACT.md) before producing
runtime inputs. Upstream bodies preserve their original recommendations and
host vocabulary; local rules resolve conflicts at the execution boundary.
Assigned worktrees, truthful evidence, authorization, resource ownership,
independent verification, and recovery remain required. The local runtime never
merges. A coordinator's separately authorized merge is outside that runtime.

## Lifecycle connections

Paths in imported prose, code blocks, and `@` includes are repository-relative
unless explicitly marked as upstream URLs. Concrete supporting method references
have been redirected to their complete local files.

| Intent / upstream capability | Active local procedure | Full supporting source |
|---|---|---|
| Start/adopt project; `new-project`, `map-codebase` | [onboard](../commands/onboard.md) | [new-project](workflows/new-project.md), [map-codebase](workflows/map-codebase.md) |
| Discuss exact outcomes; `discuss-phase` | [phase-discuss](../commands/phase-discuss.md) | [discuss-phase](workflows/discuss-phase.md) |
| Research and prepare; `plan-phase` | [phase-prepare](../commands/phase-prepare.md) | [planner](agents/gsd-planner.md), [plan-phase](workflows/plan-phase.md) |
| Check preparation; planner/checker revision loop | [phase-prepare](../commands/phase-prepare.md) | [plan checker](agents/gsd-plan-checker.md) |
| Execute independent plans; `execute-phase` | [phase-start](../commands/phase-start.md) | [execute-phase](workflows/execute-phase.md), [execute-plan](workflows/execute-plan.md) |
| Diagnose, pause, recover | [phase-resume](../commands/phase-resume.md) | [debug](workflows/debug.md), [pause-work](workflows/pause-work.md), [resume-project](workflows/resume-project.md) |
| Independent outcome assessment | [phase-verify](../commands/phase-verify.md) | [verifier](agents/gsd-verifier.md), [verify-work](workflows/verify-work.md) |
| Publish checked result | [phase-ship](../commands/phase-ship.md) | [ship](workflows/ship.md) |
| Inspect current progress | [phase-status](../commands/phase-status.md) | [progress](workflows/progress.md) |
| UI, security, AI/eval, milestone, profile, backlog and other specialty commands | Retained guidance; no automatic local route | [all command definitions](commands/gsd/), indexed in [REFERENCES.json](REFERENCES.json) |

The supporting source teaches the full upstream approach; the local procedure
defines the actual available invocation and controls. Reading an imported command
does not activate every flag or engine feature it describes. Future integrations
must implement and verify those features before advertising them as available.

## Template producers, outputs, and consumers

The upstream [artifact registry](../templates/README.md) remains complete. This
table connects every imported template to its local use, including optional
artifacts that do not have automated local producers yet.

| Template(s) under `.ai/templates/` | Output / consumer |
|---|---|
| `README.md` | Upstream artifact registry; source semantics and output vocabulary, not a local W019 validator. |
| `project.md` | `.planning/PROJECT.md`; onboarding writes, all roles read project intent. |
| `requirements.md`, `roadmap.md`, `state.md` | `.planning/REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`; coordinator and returning sessions. |
| `context.md`, `discussion-log.md` | Phase CONTEXT and optional DISCUSSION-LOG; preparer, checker, and workers. |
| `phase-prompt.md`, `planner-subagent-prompt.md` | Phase-local `NN-MM-PLAN.md` and planner assignment; checker and executor. Local ownership and execution fields are additive. |
| `summary.md`, `summary.compact.md`, `summary-standard.md`, `summary-minimal.md`, `summary-complex.md` | Component SUMMARY; coordinator integration, dependent workers, verifier, and future preparation. Use the full default unless a particular upstream variant is deliberately selected; all require local result fields when consumed by runtime. |
| `research.md` | Phase RESEARCH; preparer and checker. |
| `research-project/ARCHITECTURE.md`, `FEATURES.md`, `PITFALLS.md`, `STACK.md`, `SUMMARY.md` | `.planning/research/` topic findings and synthesis; project/phase preparation. |
| `codebase/architecture.md`, `codebase/stack.md` | `.planning/codebase/` maps; onboarding and later reconnaissance. |
| `VALIDATION.md`, `verification-report.md`, `UAT.md` | Phase validation strategy, independent verification, and user acceptance evidence. Runtime verdict fields are additive. |
| `continue-here.md` | Phase `.continue-here.md`; returning coordinator reconciles it against Git/process evidence. |
| `spec.md` | Phase-local `NN-SPEC.md` desired behavior under `.planning/phases/`; preparation input. Existing verified behavior uses local `CURRENT-SPEC.md` to avoid conflating intent and implementation. |
| `DEBUG.md` | `.planning/debug/` investigation record; explicit diagnosis work. |
| `UI-SPEC.md`, `SECURITY.md`, `AI-SPEC.md` | Phase specialty contracts; explicitly assigned design/security/AI preparation, retained source methods. |
| `user-setup.md`, `user-setup.compact.md` | Phase USER-SETUP; user actions and subsequent verification. Never populate secrets in committed records. |
| `milestone.md`, `milestone-archive.md`, `retrospective.md` | Optional `.planning/MILESTONES.md`, milestone archive, retrospective; explicit coordinator management, no new automatic milestone engine. |
| `dev-preferences.md`, `user-profile.md` | Optional developer preference/profile artifacts; retain source lifecycle and privacy boundaries, do not assume local runtime consumption. |
| `copilot-instructions.md` | Optional host instruction file; adapted capability lookup and authorization loop, not automatically installed. |
| `config.json` | Upstream configuration schema example only; active local execution uses `.planning/config.yaml`. |

Local-only [ADR](../templates/ADR.md) and
[current behavior specification](../templates/CURRENT-SPEC.md) templates provide
the same kind of authoring guidance without claiming upstream provenance.

## Provenance, changes, and checks

- [PROVENANCE.json](PROVENANCE.json) records every source/destination path,
  pinned source URL, original SHA-256, output SHA-256, reference edit and offset,
  explicit conflict correction, and appended local note.
- [REFERENCES.json](REFERENCES.json) inventories concrete source references,
  resolves local methods, links actual upstream implementation files, and
  separates project examples/unresolved source tokens. It also maps slash-command
  vocabulary to complete retained command definitions.
- The registry's missing `gsd-core/bin/lib/artifacts.cjs` build output is mapped
  to its real pinned `src/artifacts.cts` source. Template STATE schema/generator
  references point to actual pinned sources; those generators are not installed.
- The `context-bridge.md` and `commands/gsd/misc.md` references in the verifier
  few-shot examples are upstream illustrative artifacts, not available methods.
  Preserve their reasoning; never claim that the illustrated files exist locally.
- [TEMPLATE-CHANGES.md](TEMPLATE-CHANGES.md) lists every template's before/after
  reference and conflict correction in a human-readable form for `changes.log`.
- [changes.log](../../changes.log) records migration decisions across the entire
  repository, including scheduling, authorization, and truthful summary fixes.

Reproduce from a clone containing the pinned revision:

```text
python tools/import_gsd_templates.py --source PATH_TO_GSD_CLONE
python tools/import_gsd_templates.py --source PATH_TO_GSD_CLONE --check
python -m unittest discover -s tests -p test_gsd_templates.py
```

The importer reads canonical Git blobs, so platform checkout line endings do not
alter upstream hashes. It performs no network access and executes no imported
workflow. Regression checks reconstruct each exact upstream body by reversing
the recorded adaptations, detect missing/truncated files, and verify that mapped
supporting methods exist. To update the pin, review upstream changes, update the
explicit corrections and reference audit, regenerate, and rerun those checks.
