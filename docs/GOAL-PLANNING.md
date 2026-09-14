<!-- generated-by: doc-writer -->
# From goals to verified phases

A goal describes a result you want for the project. The workflow turns that result
into requirements, bounded phases and component plans, then checks the implemented
behavior against the original acceptance. A goal does not register a new runtime
object or command. Its context lives in the project's existing planning records.

Start with the copy-ready [first-goal and ordered-goals prompts](ONBOARDING-PROMPTS.md).
If project purpose and baseline are still unclear, use the onboarding prompts first.
You can discuss several goals at once while preparing only the next useful phase.

## Give the agent a useful starting point

Describe who needs the outcome, the problem they face, and one concrete example
of success. Add constraints, exclusions, relevant reference paths and any decisions
already made. Unknowns can remain explicit. The agent should inspect what it can
and ask about choices that require your intent.

For several goals, give your preferred order and explain why it matters. Priority,
technical dependency and an unresolved decision are different reasons for waiting.
One goal may span several phases; closely related goals may share one phase when
they form a coherent outcome. Neither the number of goals nor a template's sample
phase count dictates the implementation plan.

State the task's boundary: discussion only, committed preparation, implementation,
PR publication, or delivery including an authorized merge. A planning request
authorizes the requested records, not automatic implementation of everything
mentioned. Earlier explicit authorization remains valid within its scope.

## Build the context in order

| Step | Work to do | Durable result and readiness evidence |
|---|---|---|
| Inspect the starting point | Read actual project intent, relevant source, guides, tests, recent history and existing phase records | Canonical source references and an observed baseline; useful codebase maps when needed |
| Define the outcome | Resolve included behavior, exclusions, users, compatibility and material choices | Checkable requirements; confirmed decisions and explicit questions |
| Choose phase boundaries | Group coherent outcomes and identify what each phase needs from earlier work | ROADMAP order and phase mapping, with reasons for dependencies |
| Capture phase context | Record the exact goal, acceptance, decisions, references and authorization | Complete `NN-CONTEXT.md`; phase `NN-SPEC.md` when detailed desired behavior needs one |
| Resolve technical uncertainty | Inspect or research only what affects the selected scope | Relevant evidence and decisions linked from CONTEXT; unresolved dependent work remains blocked |
| Prepare and check components | Specify bounded tasks, interfaces, ownership, dependencies, checks and documentation | Complete `NN-CC-PLAN.md` files, independent preparation findings for substantial scope, and structural readiness results |
| Implement and verify | Execute authorized prepared work, integrate checked commits, correct gaps and verify behavior | Committed changes and SUMMARY files, current independent VERIFICATION, and passing required UAT |
| Continue to the next goal | Compare the next proposed scope with what was actually implemented and delivered | Updated context and prerequisites; a freshly assessed next phase |

These steps use the existing [phase procedures](../.ai/commands/README.md) and
[runtime contract](../.ai/runtime/TEMPLATE-CONTRACT.md). Preparation can revisit
discussion when inspection reveals a real missing choice. That should block its
dependent scope while independent work continues.

## Keep each fact in its owner

| Record | What belongs there |
|---|---|
| `.planning/PROJECT.md` | Project purpose, users, core value, boundaries and enduring context |
| `.planning/REQUIREMENTS.md` | Identified desired outcomes and traceability to phases |
| `.planning/ROADMAP.md` | Goal-to-phase mapping, phase order, dependencies and navigation |
| Phase `NN-CONTEXT.md` | Exact acceptance, decisions, canonical references, open questions and actual authorization |
| Phase `NN-SPEC.md`, when useful | Detailed desired behavior, boundaries and falsifiable criteria, referenced by CONTEXT |
| Phase `NN-CC-PLAN.md` | One component's executable assignment and acceptance coverage |
| Phase SUMMARY / VERIFICATION / UAT | Observed results and evidence at the relevant revision |
| `.planning/STATE.md` | Compact continuation context grounded in current records and observations |
| `.planning/specs/` | Verified current behavior; proposed future behavior stays in its phase |

Follow the [truth map](../.ai/truth-map.md) and complete authoring templates.
Reference existing decisions and specifications rather than copying their full
contents into every phase. A transcript preserves a discussion; CONTEXT records
what was actually decided. A new conversation should load that context before
asking the same questions again.

## Write acceptance that can decide whether the goal worked

Describe an action or input, its conditions, and the observable result. Include
relevant failure paths and compatibility requirements. Give criteria stable IDs
and connect them to implementation, checks and documentation ownership.

For example, **if the agreed goal is exporting existing records**, "add export"
does not establish enough detail. Useful questions include which records are
included, the output format, ordering, empty results, invalid input and failure
behavior. Record the answers as acceptance; do not choose product behavior just
to fill the example. Check the complete path from the existing records through
the export entry point to the resulting output.

The presence of an export module does not prove that users can export. Likewise,
a successful worker exit or a passing parser check does not prove acceptance.
The independent verifier assesses connected behavior at the integrated revision.
Human-only criteria require actual observations, not an agent's prediction.

## Order several goals without planning too far ahead

At the project level, establish enough detail to understand each goal's value,
boundary, likely phase outcomes, shared constraints and real prerequisites.
Maintain an explicit mapping in ROADMAP and requirement traceability. Detail the
next useful scope; future component tasks can remain undecided until their source
and interfaces are known.

Consider an illustrative sequence: record entries, export entries, then schedule
exports. Export consumes a defined record interface; scheduling consumes a working
export capability. Those are real dependencies if the intended behavior requires
them. A separate visual adjustment may be lower priority without depending on
either capability. Agree shared contracts before trying to parallelize their
implementations. Do not turn every earlier item into a dependency of every later
item merely because it appears first in the list.

Within a phase, component `depends_on` identifies other component IDs. The runtime
starts a dependent component after its own prerequisites are integrated and
checked. Overlapping paths and exclusive resources serialize work separately;
wave labels do not create a global scheduling barrier.

Across phases, CONTEXT `depends_on` names prerequisite phase directories. The
runtime requires their verified behavior to be delivered to the configured remote
base branch. An open PR or verified local commit alone does not satisfy that
requirement. When the delivery boundary stops at an open PR, report the dependent
phase's remaining prerequisite; do not merge without authorization. The runtime
never performs merges. Use stable integer `NN-slug` phase names with this runtime;
decimal examples in upstream templates are not executable phase identifiers here.

After a phase, carry forward the actual interfaces, decisions, validation results,
documentation and remaining questions. Refresh the next phase against that
revision. If evidence changes its required approach within approved scope, record
the adjustment. If the outcome itself needs to change, resolve that decision with
the user before implementing dependent work.

## Know when preparation is ready to execute

The [preparation procedure](../.ai/commands/phase-prepare.md) requires concrete
assignments and meaningful project checks. Every acceptance outcome needs an
implementation owner and evidence, including the connections between components.
Assign required documentation to the component that will actually complete it.

Substantial scope receives an independent preparation check of coverage,
feasibility, interfaces and source evidence. The Python runtime's `check` command
also validates structure and dependencies. These are separate assessments.
Neither supplies user authorization or proves the future implementation works.

Before execution, the inputs are committed, the assigned worktree is clean,
relevant decisions are resolved, actual worker routes and checks are configured,
and prerequisite behavior is available. Non-autonomous checkpoint plans and
unresolved external setup cannot simply be launched by `run`; the coordinator
must resolve their prerequisites and prepare an autonomous continuation.

Use [phase-start](../.ai/commands/phase-start.md) for authorized execution, then
[phase-verify](../.ai/commands/phase-verify.md) for independent assessment and
corrections. Keep required documentation and acceptance evidence with the phase.
Publication, observed delivery and cleanup follow the user's actual boundary.

## Ask for a useful handoff

After planning, expect the agreed goal, current-versus-target evidence, requirement
and phase mapping, decisions, open questions, prepared files, committed revision,
check results and exact next action. Unresolved questions should identify the work
they block. Later goals should retain enough context to resume without being
presented as executable assignments before their prerequisites are known.

After implementation, expect the behavior achieved, relevant checks and results,
updated documentation, independent verification, unresolved acceptance and the
actual publication/delivery state. Preserve incomplete work and failed evidence.
A goal is complete because its agreed outcome is demonstrated, not because every
planned file or heading exists.
