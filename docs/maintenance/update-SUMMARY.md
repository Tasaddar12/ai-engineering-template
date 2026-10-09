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
- `python -m unittest discover -s tests -p test_install.py -v`: 37 tests passed
  (320.537s), one expected symlink creation skip. Windows junction/short-path tests pass.
- Temporary offline guarded Claude apply: passed; custom model/user hook preserved
  and current/previous provenance verified (three changed files).
- Focused invalid-config fixture rerun: one test passed (33.677s).
- Documented runtime config-get/resolve-agent/runtime-identity commands executed
  successfully at the frozen implementation revision.
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

Initial implementation: cab7a8bde9de12416354d0949ad49c6a090edad4.
Follow-up: coordinator-owned deterministic comparison captures plan/log, then scout
classifies supplied evidence as FACT_EXTRACTION without executing project code.
This repairs the scout permission/task_class mismatch found during integration.
The follow-up documentation and this SUMMARY are committed together; the handoff
records its SHA (self-reference cannot be embedded in that commit).


## CR-01 repair: kept managed instruction blocks

Repair repository: D:/Codex/2026-10-09/task-36/update-fixes
Repair branch: feat/maintenance-update-fixes
Repair base: b00a0c5116d93dd2f447fcb3acb19c2500bde181
Authorization: confirmed independent CR-01 only; updater, regression tests and this
SUMMARY owned by coder. Publication/integration/re-review remain coordinator-owned.

The installed whole-file digest records deliberately kept bytes, including local
instructions. It cannot prove that the root managed block matches upstream. The
updater now compares AGENTS.md/CLAUDE.md managed blocks with the actual pinned
baseline regardless of an installed digest match. A kept customization remains a
review conflict on repeated updates and after upstream provenance advances. Normal
upstream blocks still upgrade while surrounding project guidance stays unchanged.
No API, manifest schema, installer, workflow or unrelated source changes.

Regression evidence:
- Before repair: `python -m unittest discover -s tests -p test_install_update.py -k test_kept_managed_block -v`
  reproduced CR-01: both Codex and Claude failed when a repeated plan lost its conflict
  after keep/generated recorded customized installed bytes (33.879s).
- After repair: `python -m unittest discover -s tests -p test_install_update.py -k managed_block -v`
  six tests passed (118.978s), including both-host keep/repeat/succeeding revision,
  provenance advancement and clean-block upgrade with surrounding guidance preserved.
- `python -m unittest discover -s tests -p test_install_update.py -k ReviewedUpdates -v`
  all 15 guarded fixtures passed (242.879s): the relevant 13 existing fixtures plus
  two new regressions, each testing both Codex and Claude.
- `python -m py_compile .ai/update.py` and `git diff --check`: passed.

Root blocks without a supplied proven baseline remain conservatively conflicted;
the CLI fetches the recorded pinned baseline. This repair does not claim a broader
merge policy. Independent re-review of the integrated repair remains outstanding.
The repair commit includes these exact three files; its resulting SHA is returned
in the worker handoff because a commit cannot contain its own SHA.
