# Using the complete GSD templates here

Read the selected [full template](../templates/README.md), including its examples,
counterexamples, field explanations and consumer guidance. Generate the artifact
from its **File Template** or corresponding artifact block; do not copy the whole
instructional document into a phase result. Do not choose a compact variant unless
the assignment or user calls for it. All supplied variants remain available.

## Which layer runs

| Layer | Responsibility | Entry point |
|---|---|---|
| Complete GSD templates | Artifact structure and authoring guidance | `.ai/templates/` |
| GSD supporting methods | Full referenced research, planning, execution and review instructions | [Source library](../gsd/README.md) |
| Local procedures | Apply those methods to this repository's host and delivery boundaries | [Commands](../commands/README.md) |
| Local execution adapter | Git isolation, worker processes, checked integration, recovery, verification, UAT and PR publication | [Python runtime](../runtime/README.md) |
| Project records | Actual decisions, plans, evidence and configuration | [Planning data](../../.planning/README.md) |

The support library is available to read. Its host-specific command names and
agent types do not register themselves in Codex. A `/gsd:...` reference identifies
its backing workflow; use the mapped local procedure where supplied. Additional
specialty workflows require an explicit assignment and the appropriate host
capabilities. Never pretend a GSD CLI command ran when only a Markdown file was read.

## Compatibility decisions

Every template alteration and source-reference repair is recorded in
[changes.log](../../changes.log) and the import provenance. These adaptations
preserve full instructions; they are not a license to shorten a template.

| Concern | Applied behavior | Reason |
|---|---|---|
| Project data | `.planning/` owns project identity, requirements, roadmap, state, phases, research maps, current specifications, decisions and project settings | User requested separation from reusable `.ai` machinery |
| PLAN | `NN-CC-PLAN.md` is the bounded component prompt within a phase | Follow upstream naming without resurrecting a standalone PLAN lifecycle |
| Execution metadata | Add the documented [runtime extensions](../runtime/TEMPLATE-CONTRACT.md) to the full artifact | Preserve recorded authorization, exact ownership, command arguments, documentation coverage and revision evidence |
| Configuration | `.planning/config.yaml` configures the Python runtime; imported `config.json` describes GSD's separate configuration | The two runtimes do not implement identical settings |
| Waves | Keep wave metadata and dependency planning guidance; the Python scheduler releases each component after its own integrated and checked prerequisites | Unrelated components need no global wave barrier |
| Source versus current behavior | Phase `NN-SPEC.md` uses upstream `spec.md`; `.planning/specs/SPEC-*.md` uses `CURRENT-SPEC.md` | Proposed requirements must not masquerade as verified current behavior |
| Checkpoints | Preserve checkpoint tasks and human observations; ask when a real decision or human-only check is needed | Existing authorization persists; repeated approval prompts are not progress |
| Verification | Tests, source inspection and observed outcomes support claims; text checks only prove textual conditions | A matching string does not establish connected behavior |
| Completion | Report only completed requirements and observed evidence; retain blocked and failed outcomes | Copying all planned IDs into a result must not claim unfinished work |
| Publication | Authorized draft progress pushes are allowed; final readiness requires current review and successful checks | The user can inspect slices without confusing a draft with verified completion |
| Merge | Python publication never merges. The coordinator may merge only within the user's explicit delivery boundary after verification | Retain the existing separation between publication and delivery |
| Milestones and specialty artifacts | Full templates remain available; create them when needed for the authorized project | Supplying a template does not seed fictional work or require every artifact |
| Recovery | Existing interrupted attempts retain their original runtime and paths until explicitly reconciled | Moving planning data must not silently reinterpret running assignments |

## Handoff checklist

- Read the selected full template before authoring or checking its output.
- Fill concrete values; preserve locked decisions and canonical source paths.
- Keep examples as examples. Do not execute sample deletion, deployment or commit commands.
- Add only the adapter fields required by the operation, following the contract.
- Give the next agent the artifact, applicable methods, exact source revision and relevant dependency summaries.
- Check both the semantic outcome and executable readiness; either can fail independently.
- Record a newly discovered incompatibility in the affected phase and `changes.log`
  for template maintenance. Correct the actual producer and consumer together.
