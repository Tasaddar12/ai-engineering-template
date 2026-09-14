# Using the complete project templates here

Read the selected [full template](../templates/README.md), including its examples,
counterexamples, field explanations and consumer guidance. Generate the artifact
from its **File Template** or corresponding artifact block; do not copy the whole
instructional document into a phase result. Use the complete templates.

## Which layer runs

| Layer | Responsibility | Entry point |
|---|---|---|
| Complete project templates | Artifact structure and authoring guidance | `.ai/templates/` |
| Agent methods | Complete selected research, planning, execution and review instructions | [Agent catalog](../agents/README.md) and [host adaptation](agent-adaptation.md) |
| Local procedures | Apply those methods to this repository's host and delivery boundaries | [Commands](../commands/README.md) |
| Local execution adapter | Git isolation, worker processes, checked integration, recovery, verification, UAT and PR publication | [Python runtime](../runtime/README.md) |
| Project records | Actual decisions, plans, evidence and configuration | [Planning data](../../.planning/README.md) |

The selected full agent methods are available to read in `.ai/agents/`. Role files
do not register host commands or agent types. Use the existing local procedures
and the host mappings in agent adaptation. A reference to an upstream tool does
not make it installed. Never claim an unavailable CLI command ran when only a
Markdown file was read.

## Runtime behavior

The workflow's [upstream Git history](https://github.com/Tasaddar12/ai-engineering-template/commits/main/)
records its source alterations and reference repairs. These adaptations
preserve full instructions; they are not a license to shorten a template.

| Concern | Applied behavior | Reason |
|---|---|---|
| Project data | `.planning/` owns project identity, requirements, roadmap, state, phases, research maps, current specifications, decisions and project settings | User requested separation from reusable `.ai` machinery |
| PLAN | `NN-CC-PLAN.md` is the bounded component prompt within a phase | Keep each assignment attached to its phase |
| Execution metadata | Add the documented [runtime extensions](../runtime/TEMPLATE-CONTRACT.md) to the full artifact | Preserve recorded authorization, exact ownership, command arguments, documentation coverage and revision evidence |
| Configuration | `.planning/config.yaml` configures the Python runtime; no JSON configuration template is supplied | Upstream settings cannot silently configure a different runtime |
| Waves | Keep wave metadata and dependency planning guidance; the Python scheduler releases each component after its own integrated and checked prerequisites | Unrelated components need no global wave barrier |
| Source versus current behavior | Phase `NN-SPEC.md` uses upstream `spec.md`; `.planning/specs/SPEC-*.md` uses `CURRENT-SPEC.md` | Proposed requirements must not masquerade as verified current behavior |
| Checkpoints | Preserve checkpoint tasks and human observations; ask when a real decision or human-only check is needed | Existing authorization persists; repeated approval prompts are not progress |
| Verification | Tests, source inspection and observed outcomes support claims; text checks only prove textual conditions | A matching string does not establish connected behavior |
| Completion | Report only completed requirements and observed evidence; retain blocked and failed outcomes | Copying all planned IDs into a result must not claim unfinished work |
| Publication | Authorized draft progress pushes are allowed; final readiness requires current review and successful checks | The user can inspect slices without confusing a draft with verified completion |
| Merge | Python publication never merges. The coordinator automatically merges after verification and required checks under the shared delivery defaults, unless the user opts out | Publication and observed delivery remain distinct; cleanup requires separate authorization |
| Optional artifacts | The retained catalog supplies research, setup and continuation artifacts; create them when useful for authorized work | Supplying a template does not seed fictional work or require every artifact |
| Recovery | Existing interrupted attempts retain their original runtime and paths until explicitly reconciled | Moving planning data must not silently reinterpret running assignments |

## Handoff checklist

- Read the selected full template before authoring or checking its output.
- Fill concrete values; preserve locked decisions and canonical source paths.
- Keep examples as examples. Do not execute sample deletion, deployment or commit commands.
- Add only the adapter fields required by the operation, following the contract.
- Give the next agent the artifact, applicable methods, exact source revision and relevant dependency summaries.
- Check both the semantic outcome and executable readiness; either can fail independently.
- Record a newly discovered incompatibility in this project's affected phase.
  Correct the actual producer and consumer together; upstream history is attribution,
  not this project's change log or an instruction to maintain the source template.
