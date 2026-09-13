**Workstream collision check (when `is_last_phase: true`):**

Before routing to Route B, check whether other workstreams are still active.
This prevents one workstream from advancing or completing the milestone while
other workstreams are still working on their phases.

**Skip this check if NOT in workstream mode** (i.e., `GSD_WORKSTREAM` is not set / flat mode).
In flat mode, go directly to **Route B**.

Parse `other_active_workstreams` from `INIT_TRANSITION` (already fetched above — no
`gsd_run` call needed here). `init.transition` pre-filters this list exactly as this
check requires: it excludes the current workstream (`$GSD_WORKSTREAM`) and any
workstream whose status contains "milestone complete" or "archived"
(case-insensitive). Each remaining entry has `name` and `status`.

- **If `other_active_workstreams` is non-empty** → Go to **Route B1**
- **If `other_active_workstreams` is empty** (or flat mode) → Go to **Route B**


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
