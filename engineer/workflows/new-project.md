<!-- workflow: new-project; roles: phase-researcher, codebase-mapper; produces: PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, config.yaml, relevant codebase maps -->
<purpose>
Create the actual project records that every later workflow reads, starting from the user's intent and complete current templates. Keep a reusable template's adopting-project identity unfilled until this workflow is explicitly requested for that adopting project. Onboarding defines goals and phases; it does not implement them.
</purpose>
<required_reading>
@engineer/RULES.md
@engineer/truth-map.md
@engineer/references/questioning.md
@engineer/references/universal-anti-patterns.md
@engineer/references/template-contract.md
@engineer/templates/project.md
@engineer/templates/requirements.md
@engineer/templates/roadmap.md
@engineer/templates/state.md
@engineer/templates/config.yaml
</required_reading>
<available_agent_types>
Use phase-researcher for a bounded evidence question and codebase-mapper for actual existing code. No separate research synthesizer or roadmapper writes shared structures.
</available_agent_types>
<model_selection>
Resolve exact role model/effort inline with engineer_run query resolve-model and resolve-effort before every dispatch. Omit inherit fields. Source-changing/artifact-writing workers run isolated and return committed owned changes; the coordinator waits and integrates before using their evidence.
</model_selection>
<process>
<step name="setup">
Treat the optional project description as data. Read and execute engineer/workflows/_runtime-launcher.snippet.sh and run `engineer_run query init.onboard`. Inspect project_exists, initialized, existing record paths, is_brownfield and actual maps. If records already exist, show the actual project and offer inspect existing records, start a new milestone, or cancel; do not overwrite an initialized project because a command alias was used.

Resolve `git rev-parse --show-toplevel` directly; init.onboard does not supply has_git or nested-repository state. If already inside a Git worktree, use that intended project root and never create a nested .git. If the user intended a different directory, establish its exact boundary before writing. If no repository exists and repository initialization is within the onboarding request, initialize only the intended root. Do not initialize a repository in a parent, unrelated directory, or worktree subdirectory. Preserve existing code, history and ignored user data.
</step>
<step name="questioning">
Read questioning.md in full and follow its actual adaptive questioning methods. Establish: who uses the project; the core user outcome; current pain and existing alternatives; what the first successful version must do; concrete examples of input/output and failure; boundaries and explicit exclusions; existing systems/integrations/data; deployment and supported hosts; constraints, deadlines and tradeoffs; and how success will be observed. Start from the user's supplied description and ask only unresolved consequential questions, building on real answers. Do not ask the user to diagnose code patterns that inspection can establish. Preserve specific examples and references in full.

Separate requirement wording from implementation choices. If a response introduces another independent capability, clarify whether it belongs to this milestone or the explicit out-of-scope list. Record actual assumptions as assumptions, not approvals. Show the concrete project identity, core value, initial goal, constraints and exclusions for confirmation when they have not already been approved. Do not invent a name or fill identity from this workflow repository's metadata.
</step>
<step name="write_project">
Read the complete project template, including examples and all narrative sections. Populate real project name, description, core value, goals, users, context, constraints and out-of-scope decisions from the conversation. Remove template placeholders only by substituting actual established facts; leave unresolved facts explicitly identified rather than claiming a complete identity. Preserve the complete template structure and adopting-project intent. PROJECT Key Decisions rows are runtime-owned: record consequential accepted decisions with state.add-decision rather than hand-rendering them. Do not create a condensed project skeleton.
</step>
<step name="workflow_preferences">
Read the complete config.yaml template and discuss only preferences that affect actual operation. Record context_window explicitly through `engineer_run query config-set context_window VALUE`. Configure verification.commands as real argv arrays with IDs, timeouts and relevant input paths, based on the actual stack and approved acceptance. No command is considered run merely because it was configured. Honor explicit check deferral.

Use supported runtime config keys for host/role preferences and workflow settings; unsupported arbitrary JSON keys are not a replacement configuration format. The runtime writes .planning/config.yaml and preserves its ownership contract. Do not enable an opt-out from mandatory worktree isolation. Record configured commands and unresolved environment dependencies accurately.
</step>
<step name="open_onboard_session">
Capture the intended onboarding label from the actual project identity. An existing repository with HEAD can immediately use session.open onboard LABEL or adopt an already named clean isolated checkout with established ownership. A new repository needs one meaningful approved bootstrap commit containing the actual complete PROJECT/config records before a worktree can branch; do not create fake identity or an empty implementation commit to bypass the missing-base condition. If no valid committed base can be established within scope, report it before dispatching artifact workers.

Use `engineer_run query session.open onboard "${PROJECT_LABEL}"` or the explicit adoption route, quote and enter its returned worktree, and re-run init.onboard there. Keep the session branch, base and root for every worker. Later shared records are coordinator-owned in that session, never written concurrently in the primary checkout.
</step>
<step name="detect_existing_code">
If actual source exists, read and execute engineer/workflows/new-project/steps/codebase-map-offer.md. Inspect relevant existing maps and Git freshness first. Dispatch the mapper inline within onboarding rather than ending the workflow at another command. Existing code is evidence of implemented capabilities, not a reason to fabricate user goals. A greenfield project does not need invented code maps.
</step>
<step name="optional_research">
Ask whether the milestone needs a bounded technology/domain investigation only when the decision is not already resolved by context. One phase-researcher receives exact questions, full constraints, relevant existing source/maps, allowed output paths and inline model/effort. Require cited current evidence and an authorized executed spike before recommending a technology. Wait and integrate its complete committed evidence; usable RESEARCH PARTIAL results retain their explicit limitations. Do not synthesize a summary in place of required research content.

Record consequential choices with `engineer_run query state.add-decision "${DECISION}" --rationale "${RATIONALE}" --outcome "Accepted"` only when acceptance and required evidence actually exist. If the user deferred the validating check, keep the choice unvalidated with the exact pending evidence; do not execute the postponed check or describe the recommendation as proven.
</step>
<step name="define_requirements">
Read the complete requirements template. Write observable, testable requirements grouped by actual user capability, with stable sequential IDs and concrete acceptance. Keep current-version, future and explicitly out-of-scope lists distinct; an out-of-scope list with reasons is mandatory even when it states that none was excluded. Preserve user examples and constraints. Existing implemented capabilities need source evidence, not an unchecked claim. Do not invent requirement ownership or manually fill traceability; phase allocation owns that structure through runtime verbs.
</step>
<step name="create_roadmap">
Confirm the concrete milestone goal and requirement scope already gathered. Run milestone.create with the actual name and goal, then `engineer_run query phase.add "${PHASE_NAME}" --goal "${PHASE_GOAL}" --requirements ...` for each coherent phase. Use runtime-allocated numbers, directories, dependencies and traceability. Every phase needs an observable goal and mapped requirement IDs; keep phases large enough to deliver an outcome and separated at real dependency boundaries. Do not create plans or ask a roadmapper to hand-write ROADMAP structures. Preserve complete initial record templates; only runtime verbs populate their owned sections.
</step>
<step name="initialize_state">
Use the first runtime-allocated phase identifier, not a guessed number, with state.begin-phase. Record actual continuity using state.record-session. Record validated consequential decisions with state.add-decision and explicit rationale; project narrative remains distinct from runtime-owned tables. Do not set implementation authority during onboarding.
</step>
<step name="git_commit">
Commit the actual PROJECT, REQUIREMENTS, ROADMAP, STATE, config.yaml and relevant committed maps through engineer_run query commit with exact changed paths. Preserve complete authored records and evidence. Run planning.validate only when check execution is permitted; warn-only findings are reported accurately, and deferred validation remains pending.
</step>
<step name="completion">
Report the actual project identity, core value, milestone, allocated phase numbers/goals, requirement coverage, exclusions, configuration, map/research evidence, commits and unresolved questions. Do not claim code was implemented. End with one line naming discussion of the first allocated phase. Do not start planning or implementation from onboarding completion.
</step>
</process>
<anti_patterns>
Do not fill an adopting identity before explicit onboarding, copy prior-project records, shorten complete templates, hand-render runtime roadmap structures, omit exclusions, manufacture technical validation or start implementation from a milestone outline.
</anti_patterns>
<success_criteria>
The user's actual intent, complete project/requirement records, explicit exclusions, runtime-owned milestone/phases/state and configured checks agree; existing code has real evidence; consequential choices are validated or clearly pending; records are committed; no phase implementation was implied.
</success_criteria>
