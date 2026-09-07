# Installable asset design

The corrective bootstrap installs canonical schemas, helper tools, and the visible product payload under `docs/agents/`, `docs/templates/`, `docs/workflows/`, and `docs/defaults/` into one selected `.ai` or `.claude` namespace. TASK-031 must integrate this behavior with planned adoption/state services; TASK-037 owns the final flat-module dependency catalog and release packaging. Schema examples under `schemas/examples/` are illustrative contract fixtures and must not be installed as real successful runs.

Framework-owned: versioned schemas, role rules, checklist versions and managed pointers. Seed-only/project-owned after creation: commands, model bindings, autonomy policy, specs, plans, ADRs and state. Upgrade compares stored manifest hashes and never overwrites project-owned seeds.
