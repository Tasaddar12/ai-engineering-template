# Adopt this template

Start in a separate Git worktree created from the destination project's agreed
base. Confirm its absolute root and branch before copying or changing files.
Do not replace existing project content without the user's authorized scope.

Copy `.ai/` and the useful guides from `docs/`. Reconcile existing instructions
with [AGENTS.snippet.md](../.ai/templates/AGENTS.snippet.md) in the destination
root AGENTS.md. Keep established fact owners rather than creating duplicate
requirements. This repository's own PROJECT, STATE, SPEC-002, PLAN-004,
amendments and journal describe this template; do not adopt them as the new
project's history or intent. Create the destination records from templates.

Use [onboard](../.ai/commands/onboard.md) to inspect the destination, draft its
PROJECT from confirmed user intent, choose the supported mode, set paths and
real verification commands, and identify current specs. Preserve existing logs
and decisions; classify old documents before moving or deleting them. Return
the [decision summary](../.ai/templates/decision-summary.md) for approval of
changes not already authorized.

Command files are Markdown procedures. A slash-style name means to follow the
matching file under `.ai/commands/`; it is not a shell command. `$1`, `$2` and
`$ARGUMENTS` in command bodies are input placeholders, not environment values.
Supply them with the actual record, run and track identifiers.

Role `tools`, `reads`, `writes`, `model` and `reasoning` fields describe the
intended assignment. They do not configure a runtime. Map them to capabilities
that the chosen host actually provides and preserve the narrower role scope.
Do not spawn workers without authority or claim fresh/cold review in a reused
context. Manual sessions are the default dispatch mechanism.

The [hook examples](../.ai/hooks/README.md) are optional and unregistered. A
host adapter must provide compatible events and interpret their output; retain
the host's permission controls. Background dispatch additionally needs a
launcher and completion mechanism. Validate that integration in its real host
before switching the destination's config to background dispatch.

Use [onboard-pr](../.ai/commands/onboard-pr.md) for an authorized adoption PR.
Use [deliver](../.ai/commands/deliver.md) for merge confirmation, pulling the
target and removing only the verified merged worktree and branch.
