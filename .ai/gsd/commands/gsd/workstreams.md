---
name: gsd:workstreams
description: Manage parallel workstreams — list, create, switch, status, progress, complete, and resume
allowed-tools:
  - Read
  - Bash
  - Grep
requires: [new-milestone, phase, progress, resume-work]
---

# /gsd:workstreams

Manage parallel workstreams for concurrent milestone work.

## Usage

`/gsd:workstreams [subcommand] [args]`

### Subcommands

| Command | Description |
|---------|-------------|
| `list` | List all workstreams with status |
| `create <name>` | Create a new workstream |
| `status <name>` | Detailed status for one workstream |
| `switch <name>` | Set active workstream |
| `progress` | Progress summary across all workstreams |
| `complete <name>` | Archive a completed workstream |
| `resume <name>` | Resume work in a workstream |

## Step 1: Parse Subcommand

Parse the user's input to determine which workstream operation to perform.
If no subcommand given, default to `list`.

## Step 2: Execute Operation

### list
Run: `gsd-tools query workstream.list --raw --cwd "$CWD"`
Display the workstreams in a table format showing name, status, current phase, and progress.

### create
Run: `gsd-tools query workstream.create <name> --raw --cwd "$CWD"`
After creation, display the new workstream path and suggest next steps:
- `/gsd:new-milestone --ws <name>` to set up the milestone

### status
Run: `gsd-tools query workstream.status <name> --raw --cwd "$CWD"`
Display detailed phase breakdown and state information.

### switch
Run: `gsd-tools query workstream.set <name> --raw --cwd "$CWD"`
Also set `GSD_WORKSTREAM` for the current session when the runtime supports it.
If the runtime exposes a session identifier, GSD also stores the active workstream
session-locally so concurrent sessions do not overwrite each other.

### progress
Run: `gsd-tools query workstream.progress --raw --cwd "$CWD"`
Display a progress overview across all workstreams.

### complete
Run: `gsd-tools query workstream.complete <name> --raw --cwd "$CWD"`
Archive the workstream to milestones/.

### resume
Set the workstream as active and suggest `/gsd:resume-work --ws <name>`.

## Step 3: Display Results

Format the JSON output from gsd-tools query into a human-readable display.
Include the `${GSD_WS}` flag in any routing suggestions.


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

The complete upstream body above is retained from GSD-Core at
`c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977`; only recorded reference substitutions
and explicit local conflict corrections have been made. See
`.ai/gsd/PROVENANCE.json` for exact source hashes and changes.

Read `.ai/gsd/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/gsd-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The upstream `config.json`, `/gsd:*` commands, tool
names, hooks, and Node CLI examples describe GSD's system; this import does not
install or activate that system. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
