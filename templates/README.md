# Installable asset design

TASK-002 implements the manifest and package-data catalog; TASK-026 implements project initialization/adoption. Templates are not installable yet. Schema examples under `schemas/examples/` are illustrative contract fixtures and must not be installed as real successful runs.

Framework-owned: versioned schemas, role rules, checklist versions and managed pointers. Seed-only/project-owned after creation: commands, model bindings, autonomy policy, specs, plans, ADRs and state. Upgrade compares stored manifest hashes and never overwrites project-owned seeds.
