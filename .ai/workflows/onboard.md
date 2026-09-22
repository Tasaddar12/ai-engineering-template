<!-- workflow
step: onboard
agent-roles: orchestrator, researcher, codebase-mapper
produces: PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, config.yaml
consumes: the user's intent, and any existing codebase
-->

<purpose>
Initialize a project's planning records from the user's actual intent. Question
until the vision is concrete, write PROJECT.md, scope requirements with REQ ids,
then break the work into phases.

This is the only workflow that creates the records every other workflow reads.
Everything it writes comes from the user, not from the template's placeholders.
</purpose>

<required_reading>
@~/.ai/references/questioning.md
@~/.ai/references/universal-anti-patterns.md
</required_reading>

<available_agent_types>
Valid subagent types (use these exact names — never fall back to a generic agent):
- researcher — researches project-level technical decisions
- codebase-mapper — explores an existing codebase and writes structured analysis
</available_agent_types>

<model_selection>
Models are injected inline at dispatch, never read from an agent's frontmatter.
Resolve each agent's model from the runtime and pass it on the `Agent(...)` call:

```bash
phase_run query resolve-model <agent> --raw
```

A result of `inherit` means the project set no override — **omit the `model`
argument entirely** in that case and let the host choose. Pass `model` only when
resolution returned a concrete model name. The `models` map in each init bundle
carries the same resolved values for every agent that workflow dispatches.
</model_selection>

<process>

<step name="setup">
```bash
_root="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
for _c in "$_root"/.{ai,claude,codex}/runtime/phase.py "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/runtime/phase.py "${CODEX_HOME:-$HOME/.codex}"/runtime/phase.py; do
  [ -f "$_c" ] && PHASE_RUNTIME="$_c" && break
done
[ -n "${PHASE_RUNTIME:-}" ] || { echo "ERROR: phase runtime not found; run the installer." >&2; exit 1; }
phase_run() { "$(command -v python3 || command -v python)" "$PHASE_RUNTIME" "$@"; }
INIT=$(phase_run query init.onboard)
```

Extract: `records` (each of project, requirements, roadmap, state is `missing`,
`skeleton` or `filled`), `initialized`, `phase_count`, `models`,
`agents_installed`, `checks_configured`, `templates_dir`, `commit_docs`,
`text_mode`, `response_language`, `paths`.

**If `response_language` is set:** all user-facing output MUST be presented in
`{response_language}`; technical terms, code, file paths and subagent prompts stay
in English.

**If `initialized` is true:**

```
This project is already initialized ({phase_count} phases, PROJECT.md filled).

Re-running onboarding would overwrite the project's own record of its intent.
```

Use AskUserQuestion (header: "Already set up"; options: "Start the next
milestone instead" / "Revise PROJECT.md only" / "Cancel"). On the first, stop and
point at `/new-milestone`.

Display: `► ONBOARDING`
</step>

<step name="detect_existing_code">
Determine whether this is a greenfield project or an existing codebase:

```bash
git log --oneline -n 5 2>/dev/null || true
ls
```

**If there is substantial existing code**, map it before questioning — scoping
work against a codebase you have not read produces phases that do not fit:

```
Agent(
  prompt="
Explore this codebase and write a structured map of it.

Cover: the stack and its versions, the main components and how they fit, the
existing conventions a new phase would have to follow, and anything that
constrains what can be built next.

Write to: .planning/codebase/STACK.md and .planning/codebase/ARCHITECTURE.md
(uppercase — the runtime tracks these exact names).

Return: ## MAP COMPLETE with the files written and the three constraints that
matter most for planning new work.
",
  subagent_type="codebase-mapper",
  ${models['codebase-mapper'] === 'inherit' ? '' : `model="${models['codebase-mapper']}",`}
  description="Map the existing codebase"
)
```

> **ORCHESTRATOR RULE**: wait for the subagent before continuing.

Confirm both maps exist:

```bash
phase_run query codebase.status
```

A `missing` map means the mapper did not finish its assignment — say so rather
than continuing on a map that was never written.
</step>

<step name="questioning">
**Open the conversation.** Ask inline — freeform, not AskUserQuestion:

"What do you want to build?"

Wait for the answer. It gives you the context you need to ask intelligent
follow-ups.

**Follow the thread.** Based on what they said, ask follow-ups that dig into
their answer. Use AskUserQuestion with options that probe what they actually
mentioned — interpretations, clarifications, concrete examples.

Keep following threads. Each answer opens new ones. Ask about:

- What excited them
- What problem sparked this
- What they mean by vague terms
- What it would actually look like in use
- What is already decided

Techniques are in `@~/.ai/references/questioning.md`: challenge vagueness, make
the abstract concrete, surface assumptions, find edges, reveal motivation.

**Check coverage silently.** As you go, track the gaps in your head. Weave the
missing questions in naturally — do not switch into checklist mode.

**Decision gate.** When you could write a clear PROJECT.md, use AskUserQuestion:

- header: "Ready?"
- question: "I think I understand what you're after. Ready to create PROJECT.md?"
- options:
  - "Create PROJECT.md" — let's move forward
  - "Keep exploring" — I want to share more, or ask me more

On "Keep exploring", ask what they want to add, or name the gaps you see and
probe them. Loop until they choose to create.
</step>

<step name="write_project">
Synthesize everything into `.planning/PROJECT.md` using the template at
`{templates_dir}/project.md`.

Record: the core value in one line, the vision, hard constraints, the key
decisions already made and why, and what is explicitly not being built.

**Every placeholder must be replaced.** A PROJECT.md that still contains
`CHANGEME` or bracketed placeholders has not been filled — it has been copied.
</step>

<step name="workflow_preferences">
Establish how this project wants to run, and write it to `.planning/config.yaml`:

```bash
phase_run query config-set commit_docs true
phase_run query config-set context_window 200000
```

Ask about, and configure:

- **Verification commands** — the project's real checks, as argv lists under
  `verification.commands`. This is the single most valuable thing to get right:
  without it, every phase is verified by reading alone.
- **Agent models** — only when the user wants to override an agent's default.

If the project has no runnable checks yet, say so plainly and note that the first
phase should establish them.
</step>

<step name="research">
**Optional — only for genuine project-level unknowns**, such as choosing between
frameworks or protocols the whole project rests on. Skip it otherwise.

```
Agent(
  prompt="
Research the project-level technical decisions for this project.

**What is being built:** {summary from PROJECT.md}
**Constraints:** {from PROJECT.md}
**Open questions:** {the specific unknowns, listed}

Report options with trade-offs and cite what you actually read. Name real
versions and APIs. Do not pick for the user — surface what the choice costs.

Return: ## RESEARCH COMPLETE with findings and their implications for scoping.
",
  subagent_type="researcher",
  ${models['researcher'] === 'inherit' ? '' : `model="${models['researcher']}",`}
  description="Research project decisions"
)
```

> **ORCHESTRATOR RULE**: wait for the subagent before continuing.

Present the findings and let the user decide.

**A project-level technology choice is validated before it is proposed.** The
whole project rests on it, and research reports what a technology claims rather
than what it does here. Open a record, prove the claim, then propose it:

```bash
phase_run query decision.draft "{the choice}" --kind stack \
  --question "{what the project needs from it}"
phase_run query decision.validate ADR-00N \
  --method "{the smallest spike that could fail}" \
  --command "{what was run}" \
  --evidence "{what it actually printed}" --result pass
phase_run query decision.propose ADR-00N
```

The spike is deliberately small: install the dependency and call the one API the
project depends on, run the target runtime version, or make the integration
return one real response. Enough to find out that it does not work before the
roadmap is built on the assumption that it does.

Then record the user's answer, which is what makes it a decision:

```bash
phase_run query decision.accept ADR-00N --basis "{who decided, when, on what}"
phase_run query state.add-decision "{the choice}" --rationale "{why}" --outcome "Accepted"
```

`state.add-decision` writes it to PROJECT.md's Key Decisions table as well as the
digest, so PROJECT.md stays the durable log without a second hand edit.
</step>

<step name="define_requirements">
Write `.planning/REQUIREMENTS.md` using `{templates_dir}/requirements.md`.

Each requirement is an observable capability with a REQ id, not a task:

```markdown
- REQ-01: A user can sign in with their IDP account
- REQ-02: A session expires after the configured idle period
```

Group them into what the first milestone delivers and what is deliberately
deferred. **The out-of-scope list is mandatory** — it is what makes the scope
guard in `/discuss-phase` enforceable later.
</step>

<step name="create_roadmap">
Break the first milestone into phases with the user. Each phase delivers
something coherent and independently verifiable; 3–8 phases is the usual range
for a first milestone.

Where there are milestones from the start, declare the first one:

```bash
phase_run query milestone.create "${MILESTONE_NAME}" --goal "${MILESTONE_GOAL}"
```

Then add each phase in order through the runtime, so numbering, directories, the
overview checklist and the progress table stay consistent:

```bash
phase_run query phase.add "${PHASE_TITLE}" --goal "${PHASE_GOAL}" --requirements "${REQ_IDS}"
```

Every REQ id from REQUIREMENTS.md must be claimed by some phase. Report any that
are not — an unclaimed requirement is scope with no home.

Do not create plans here. Planning is per phase, in `/plan-phase`.
</step>

<step name="initialize_state">
If `records.state` is `missing`, create `.planning/STATE.md` from
`{templates_dir}/state.md` — first-time creation from a template is the one time
a workflow writes STATE.md directly.

Then hand it to the runtime, which derives its counters from the roadmap:

```bash
phase_run query state.begin-phase 1 --status "Ready to plan"
phase_run query state.add-decision "{each key decision from PROJECT.md}"
```
</step>

<step name="git_commit">
```bash
phase_run query commit "docs: initialize project planning" \
  --files .planning/PROJECT.md .planning/REQUIREMENTS.md .planning/ROADMAP.md \
          .planning/STATE.md .planning/config.yaml .planning/codebase
```
</step>

<step name="completion">
```
► PROJECT INITIALIZED

{Project name}
{Core value}

Requirements: {N} ({M} deferred)
Phases: 1-{last}
Checks configured: {yes, listing them | no — the first phase should establish them}

Records:
  .planning/PROJECT.md
  .planning/REQUIREMENTS.md .planning/decisions
  .planning/ROADMAP.md
  .planning/STATE.md

---

## ▶ Next Up

**Phase 1: {name}** — {goal}

`/clear` then:

`/discuss-phase 1`

---
```
</step>

</process>

<anti_patterns>
- Don't leave placeholders — a record still containing `CHANGEME` was copied, not filled
- Don't infer the project's intent from its code; the code shows what exists, the user knows what they want
- Don't walk a checklist of questions; follow the threads the user opens
- Don't decide the technical choices for the user during research; surface the trade-offs
- Don't create plans here — phases only
- Don't hand-write ROADMAP.md phase entries; `phase.add` owns numbering and structure
- Don't skip the out-of-scope list; without it nothing downstream can refuse scope creep
</anti_patterns>

<success_criteria>
- [ ] Existing code mapped before scoping, where there was any
- [ ] Questioning continued until the vision was concrete enough to write down
- [ ] PROJECT.md written from the user's intent, with no placeholders left
- [ ] Verification commands configured, or their absence stated plainly
- [ ] REQUIREMENTS.md written with REQ ids and a mandatory out-of-scope list
- [ ] Phases created through the runtime, every REQ id claimed by some phase
- [ ] STATE.md initialized and pointed at the first phase
- [ ] Everything committed, and the user knows the next step
</success_criteria>
