<!-- workflow
step: milestone-summary
agent-roles: orchestrator
produces: human-readable milestone summary
consumes: ROADMAP.md, REQUIREMENTS.md, MILESTONES.md, phase artifacts
-->

<purpose>
Generate a human-friendly summary of a milestone from its artifacts. Written for
onboarding: someone who was not present reads the output and understands what the
milestone delivered and why.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="resolve_version">
```bash
_root="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
for _c in "$_root"/.{ai,claude,codex}/runtime/phase.py "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/runtime/phase.py "${CODEX_HOME:-$HOME/.codex}"/runtime/phase.py; do
  [ -f "$_c" ] && PHASE_RUNTIME="$_c" && break
done
[ -n "${PHASE_RUNTIME:-}" ] || { echo "ERROR: phase runtime not found; run the installer." >&2; exit 1; }
phase_run() { "$(command -v python3 || command -v python)" "$PHASE_RUNTIME" "$@"; }
MILESTONES=$(phase_run query milestone.list)
```

`$ARGUMENTS` names the milestone. When empty, use `current` from the result; if
there is no current milestone, use the most recently shipped one.

If neither exists:

```
No milestone found. Start one with `/new-milestone "<name>"`.
```

Exit.
</step>

<step name="locate_artifacts">
Gather the milestone's material:

```bash
INIT=$(phase_run query init.complete-milestone "${VERSION}")
```

Extract `milestone_phases`. For each phase, read:
- `{NN}-CONTEXT.md` — the decisions that shaped it
- `{NN}-*-SUMMARY.md` — what was actually built
- `{NN}-VERIFICATION.md` — what was confirmed

Also read `.planning/REQUIREMENTS.md` for the requirement ids the milestone
claimed, and `.planning/MILESTONES.md` for the shipped entry when it exists.

Budget: read summaries and verification reports in full; read CONTEXT.md files
only for their decisions sections.
</step>

<step name="compose_summary">
Write the summary. It is for a reader with no history here, so lead with what the
software does, not with process:

````
# {Project Name} — {Milestone version} {name}

**Status:** {shipped YYYY-MM-DD | in progress}
**Phases:** {range} ({count} phases, {plans} plans)

## What This Milestone Delivered

{Two or three paragraphs in plain language: what a user can now do that they
could not before, and why it was worth doing.}

## How It Works

{The shape of the implementation — the main components and how they fit. Name
real files and modules so the reader can go look.}

## Key Decisions

| Decision | Why | Where it shows up |
|----------|-----|-------------------|
| {from CONTEXT.md decisions} | {rationale} | {file or module} |

## Requirements Covered

- {REQ-id}: {requirement} — {how it was satisfied}

## What Was Verified

{From the VERIFICATION.md reports: what was confirmed true, and by what evidence.
Say plainly where verification was partial or absent.}

## Known Gaps

{Anything the verification reports flagged and the milestone shipped anyway,
plus deferred ideas recorded in the phase CONTEXT.md files. If there are none,
say so rather than omitting the section.}

## Where To Go Next

- {The natural next area of work, from the roadmap}
````
</step>

<step name="output">
Present the summary in the response.

If `--write` is in `$ARGUMENTS`, also write it to
`.planning/milestones/{version}-SUMMARY.md` and commit:

```bash
phase_run query commit "docs(milestone): summarise ${VERSION}" --files .planning/milestones
```
</step>

</process>

<anti_patterns>
- Don't summarise from ROADMAP.md alone — it records intent, summaries record outcomes
- Don't claim verification that no VERIFICATION.md supports
- Don't hide known gaps to make the milestone read well
- Don't write process narrative; the reader wants the software, not the workflow
</anti_patterns>

<success_criteria>
- [ ] Milestone resolved from arguments, current state, or the newest shipped entry
- [ ] Phase summaries, contexts and verification reports read
- [ ] Summary explains the delivered capability in plain language
- [ ] Key decisions traced to where they show up in the code
- [ ] Verification and known gaps reported honestly
- [ ] Written to disk and committed when `--write` was passed
</success_criteria>
