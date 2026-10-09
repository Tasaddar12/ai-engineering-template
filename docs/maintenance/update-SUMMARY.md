# Guarded upstream workflow updates

Status: implemented; independent review and integrated project checks are coordinator-owned.

Repository: D:/Codex/2026-10-09/task-36/update-worker
Branch: feat/maintenance-update-slice
Base: 6e3280a06b680547972fe9def3240f872fb842dd
Authorization: bounded upstream-update maintenance assignment, implementation and slice
commit authorized; coordinator owns push/draft PR. No adoption records, product install,
merge, benchmark or AI evaluation campaign.

## Changes

- Fresh installer records .codex/workflow-ownership.json or .claude equivalent:
  source/revision, installed and rendered upstream SHA256, and distinct managed,
  customized, generated and project classes. Only newly created whole workflow
  files gain upstream ownership; existing equal preserved files stay customized.
  Reinstallation retains the existing manifest. Migration backups remain separate.
- New installed update.py pins Git refs, compares actual contents, emits full text
  diffs and saves candidates/hashes as reviewable JSON. Dry-run is the default.
  Apply requires the hash of the complete reviewed plan and recomputes candidates
  and all target fingerprints before mutation. Backups are verified first.
- Legacy missing ownership is unproven even for matching bytes; per-file reviewed
  classification/resolution enables a safe upgrade. Customized content survives
  keep resolutions and remains customized. Retired files require reviewed removal;
  project additions have no blanket prune. Generated conflicts require reconciliation.
- Nested missing operational settings are filled from pinned literal runtime DEFAULTS
  only for workflow.isolation, worktree.root, handoff.context_percent/context_tokens
  and verification.commands. Other defaults/example overrides are reported optional.
  Existing types/enums/ranges are checked as conflicts, preserving legitimate models,
  commands, settings and user hooks. Upstream code is never executed by comparison.
- Short identical command/skill route to a workflow that explicitly dispatches scout,
  coder and independent code-reviewer, then only needed named verification roles.
  Runtime/config APIs own configuration outside the guarded deterministic migration.

## Evidence

- `python -m unittest discover -s tests -p test_install_update.py -v`
  initial new fixture batch: 13 tests passed (137.172s).
- `python -m unittest discover -s tests -p test_install_update.py -k UpdateTests -v`:
  44 retained legacy tests passed (85.642s), four expected platform/host skips.
- Existing installer compatibility suite is running; final result will follow in
  the handoff or a follow-up evidence commit.
- `python -m py_compile .ai/install.py .ai/update.py`: passed.
- `python C:/Users/killi/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/update-workflows`:
  Skill is valid. Command and skill bytes match.
- Fixtures cover real offline Git refs, dry-run byte preservation, guarded CLI apply,
  customized/legacy ownership, nested settings, model and hook preservation, false
  version stamps, provenance, stale/tampered plans, traversal and project-code claims.

## APIs and integration

Comparison: `python .codex/update.py --target . --source <Git repository> --ref <ref> --plan review.json`.
Claude uses .claude/update.py. Optional --no-hooks / --from-ref supplies registration
policy / legacy content baseline. The updater requires existing Python 3.11+, Git and
PyYAML, and does not install dependencies.
Apply: `python .codex/update.py --apply review.json --reviewed-plan-sha256 <SHA256>`.
Review resolutions: `resolutions[path] = {action: keep|write|remove, classification:
upstream-managed|customized|generated|project}`; exact JSON strings required.

Coordinator integration needed: add new command/skill/workflow to shared indices,
document the guarded updater in installation guides and replace recommendations to
use destructive legacy installer --update/--prune for customized files. Those legacy
APIs remain unchanged for compatibility; the new workflow never calls them. There
is no install skill mirror at this base; .ai/commands/install.md was read instead.

## Limits

Apply validates resulting hashes and YAML/JSON/TOML syntax; independent runtime,
behavioral/project checks and live trusted hook execution belong to named verification.
YAML insertion uses safe-load/safe-dump and may reformat comments. Arbitrary conflict
merges are coder-owned reconciliation followed by replan; no automatic three-way merge.
Backups preserve originals if disk writes fail; applying multiple files is not atomic.
Path checks reject links/junctions and unsafe portable paths; concurrent edits detected
before application must be replanned. No production installation or network publication
was performed by this worker.

## Commits

The implementation and this required SUMMARY are committed together; the worker
handoff records the resulting SHA (self-reference cannot be embedded in that commit).
