---
status: complete
acceptance: []
documentation:
  - .ai/gsd/README.md
  - .ai/gsd/TEMPLATE-CHANGES.md
---

# Complete GSD template and supporting-source import

## Changes

| Outcome | Evidence |
|---|---|
| Every upstream template preserved | 40 exact upstream filenames under `.ai/templates/`; full examples, counterexamples, guidance, compact variants, and JSON retained. |
| Supporting methods available locally | 64 agents, 72 command definitions, 131 reference/fixture files, 177 workflow/step files, and 3 context guides under `.ai/gsd/`. |
| Original content recoverable exactly | Per-file original/output hashes and reversible reference/conflict transformations in `.ai/gsd/PROVENANCE.json`. Tests reconstruct all 487 original upstream Git blobs. |
| Real references mapped | `.ai/gsd/REFERENCES.json` maps concrete imported methods to actual local files and runtime/source evidence to actual pinned upstream paths. |
| Full human-readable change record | `.ai/gsd/TEMPLATE-CHANGES.md` lists all 40 templates, every before/after adaptation, and the shared additive local note. Coordinator appends its full content to root `changes.log`. |
| Honest execution boundary | `.ai/gsd/README.md` maps lifecycle procedures and all templates to local producers/consumers; distinguishes available runtime from retained specialty definitions. |
| Repeatable import | `tools/import_gsd_templates.py` reads canonical pinned Git blobs, performs only enumerated adaptations, regenerates manifests/log, and checks without network or imported workflow execution. |
| Cross-platform reproducibility | Scoped `.gitattributes` fixes imported text to LF; checks normalize Windows checkout line endings to canonical Git bytes. |

Source: `open-gsd/gsd-core`, revision
`c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977`. Upstream MIT license retained at
`.ai/gsd/LICENSE`.

## Checks

Revision under verification: `e3c0aef` (the two implementation slices below).

| Command | Result |
|---|---|
| `python -m unittest discover -s tests -p test_gsd_templates.py` | PASS, 7 tests. |
| `python tools/import_gsd_templates.py --source C:/Users/killi/AppData/Local/Temp/gsd-template-source-20260913 --check` | PASS, 491 generated files, 0 differences. |

The checks verify exact 40-template inventory and casing, all 487 imported-file
counts/hashes, reversible losslessness, original MIT license, local method
existence, individually pinned source links, command-definition coverage, JSON
preservation, and detection of content truncation. They do not claim that the
upstream Node runtime or optional specialty features are installed.

## Deviations and changes.log handoff

Copy the complete generated `.ai/gsd/TEMPLATE-CHANGES.md` into `changes.log`.
Its detailed entries include these consequential decisions:

- Preserve upstream names; phase-prompt.md produces phase-local PLAN.md.
- Replace only contradictory wave-scheduling sentences with advisory waves and
  actual dependency/resource/capacity scheduling. All surrounding guidance stays.
- SUMMARY completion IDs report only actually completed, verified requirements;
  incomplete assigned IDs remain gaps rather than fabricated accomplishments.
- Copilot instructions resolve real local procedures/roles and continue authorized
  work, instead of invoking uninstalled host components or asking permission after
  every completed step.
- Correct the registry's absent artifacts.cjs build-output reference to its actual
  pinned `src/artifacts.cts` source. STATE schema, generator, and ADR references
  also resolve to real pinned source files.
- Preserve upstream config.json exactly; explicitly separate it from the active
  `.planning/config.yaml` runtime settings.
- Append a clearly separated local boundary note; do not silently delete upstream
  vocabulary, examples, optional mechanisms, or substantive instructional content.
- Preserve the upstream verifier few-shot examples involving context-bridge.md and
  commands/gsd/misc.md as illustrations. The referenced files do not exist at the
  pin; these are not active missing methods and no fictitious stubs were created.
- Add a scoped LF attribute policy for imported text and canonical-byte checking.
- Require importer mutations to run in an immediate-child assigned worktree;
  read-only `--check` works in any checkout.

## Remaining / integration boundary

- Parent owns `.ai/references/gsd-adaptation.md`, active commands/roles/skills,
  runtime changes, root changes.log, and overall integrated verification.
- Runtime worker owns `.ai/runtime/TEMPLATE-CONTRACT.md`; guide worker owns
  local-only ADR.md/CURRENT-SPEC.md. This worker did not overwrite those paths.
- Retaining all supporting definitions is the requested source/method import.
  Upstream installers, Node engine, hooks, and specialty execution features are
  not installed by this component. Their concrete source references and execution
  boundaries are documented; broader feature integration is the next user stage.
- Coordinator must rerun integrated navigation/runtime checks and independently
  review before the authorized merge. No workers publish or merge.

## Commits

1. `2969562` — Import complete pinned GSD templates and supporting authoring library.
2. `e3c0aef` — Verify lossless GSD import and document every template adaptation.
3. This summary commit records the bounded result for coordinator integration.
