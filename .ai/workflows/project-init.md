---
name: project-init
trigger: Explicit init or adopt command
responsible_role: orchestrator
required_inputs:
- project_root
permitted_effects:
- install_current_assets
- create_empty_state
outputs:
- framework-manifest
- state
stop_conditions:
- linked_or_escaped_path
- unmanaged_file_conflict
- legacy_layout_present
resume: Resolve the named conflict and repeat the same command.
---
# Project initialization

Initialize a project only after an explicit request. `adopt` accepts an existing
current-format `.ai` directory but is not a legacy migration route.

1. Resolve the exact project root and refuse links, junctions and path escapes.
2. Inventory root-authored agents, templates, workflows, constraints and framework
   configuration from installed resources.
3. Refuse obsolete monolithic constraints, separate models or YAML agent definitions.
4. Compare every managed destination with the digest manifest. Update only an unchanged
   previously managed file; never overwrite a user modification.
5. Install derived copies and remove obsolete manifest-owned defaults only when their
   prior digest still matches.
6. Create an empty `STATE.yaml` with no current plan, worktree, run, delivery record
   or implementation authority. Do not copy framework repository history.
7. Write the manifest last so an interrupted update can be safely repeated.

Return exact actions and framework version. Dry-run reports those actions without
creating the root, `.ai`, state or manifest.
