**Workstream collision check (when `is_last_phase: true`):**

Before routing to Route B, check whether other workstreams are still active.
This prevents one workstream from advancing or completing the milestone while
other workstreams are still working on their phases.

**Skip this check if NOT in workstream mode** (i.e., `Workflow_WORKSTREAM` is not set / flat mode).
In flat mode, go directly to **Route B**.

Parse `other_active_workstreams` from `INIT_TRANSITION` (already fetched above — no
`workflow_run` call needed here). `init.transition` pre-filters this list exactly as this
check requires: it excludes the current workstream (`$Workflow_WORKSTREAM`) and any
workstream whose status contains "milestone complete" or "archived"
(case-insensitive). Each remaining entry has `name` and `status`.

- **If `other_active_workstreams` is non-empty** → Go to **Route B1**
- **If `other_active_workstreams` is empty** (or flat mode) → Go to **Route B**


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

This complete authoring guide retains its source content, examples, and methods.
Only recorded namespace/reference substitutions and explicit local conflict
corrections have been made. Source attribution and exact original hashes are
isolated in `.ai/library/THIRD-PARTY-NOTICES.md` and `PROVENANCE.json`.

Read `.ai/library/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/template-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The retained `config.json`, `/workflow:*` commands, tool
names, hooks, and Node CLI examples describe supporting source capabilities;
this import does not install or activate them. Source catalog pointers in examples
identify provenance, not executable command arguments. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
