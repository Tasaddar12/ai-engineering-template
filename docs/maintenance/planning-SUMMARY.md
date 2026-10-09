# Planning cleanup maintenance summary

Implemented a short `clean-planning` command/skill mirror, a full evidence-led
workflow, and a runtime audit with guarded dry-run mechanical repair proposals.

## Assignment and revision

- Root: `D:/Codex/2026-10-09/task-36/planning-worker`
- Branch: `feat/maintenance-planning-slice`
- Base: `6e3280a06b680547972fe9def3240f872fb842dd`
- Scope: only the assigned planning entrypoint/mirror/workflow, new runtime
  helper and offline tests, and this summary. No adopting `.planning` records
  were filled or changed.

## Changes and evidence

`planning_review.review` reuses `validate.run`, `Roadmap`, STATE derivation,
frontmatter/section/table parsers, phase filename identities, requirement status
values, quick status values and verification status readers. It audits templates,
IDs, references, dependency ordering and contradictory completion evidence.
Findings distinguish structure, semantics and existing conformance warnings.
The hardening slice reports dependency cycles and malformed verification YAML,
keeps human checkpoints distinct from automatic task fields, and resolves actual
SUMMARY commit hashes (canonical `## Task Commits` or an explicit hash list) with
Git rather than mistaking `actuals.commits` for commit evidence. Missing STATE
status, wrong-level headings and fenced example field anchors are not guessed.

`planning_review.repair` previews exact diffs. Only unique intact STATE field
blocks can restore a heading; progress metadata copies roadmap checkboxes when
identity/completion findings permit. Apply requires a matching fingerprint of
planning sources and canonical templates and takes the existing planning lock.
It preserves the STATE body, other custom metadata, statuses, roadmap checkboxes,
requirement wording and historical rationale. Adoption skeletons are exempt.

The workflow dispatches named read-only scouts for distinct evidence questions,
resolves actual host model/effort inline, retains coordinator decision ownership,
routes code/prose repairs to their owners, and requires independent code review
for source changes and factual doc verification. Archive integration uses the
archive worker's `planning.archive <kind> <selector>` dry-run API, discovery and
guarded recovery; active age-only retirement is excluded.

## Checks

- `python -m unittest discover -s tests -p test_planning_review.py -v`: 18 passed.
  Fixtures cover missing headings, ambiguous anchors, identities/dependencies,
  local references, conflicting completion, unfilled adoption exemption,
  review fingerprint rejection, dry-run, idempotence and exact prose preservation.
  Final cases additionally cover malformed verification, dependency cycles,
  canonical human checkpoints, actual Git evidence versus commit counts, wrong
  heading levels, fenced field examples and preservation of an absent status.
- `python -m unittest discover -s tests -p test_agent_sources.py -v`: 12 passed.
- `python -m unittest discover -s tests -p test_workflow_links.py -v`: 3 passed.
- `python .ai/runtime/phase.py query planning.validate`: clean, zero warnings.
- Skill quick validation initially rejected the command-only `argument-hint`
  metadata; moved usage into the body and kept mirror parity.
- `python .../skill-creator/scripts/quick_validate.py .agents/skills/clean-planning`:
  `Skill is valid!` after that correction.
- `python .ai/runtime/phase.py query resolve-agent scout --host codex`: confirmed
  `gpt-6-luna`, `high`, read-only role. Source `.ai` defaults to Claude unless
  `--host codex` is explicit; workflow dispatch examples now name the actual host.

## Commits

- `5aaff9a`: first tested source/workflow/skill slice, including this SUMMARY.
- Hardening and this updated SUMMARY are committed in the following slice; its
  exact hash is supplied in the final handoff. Git owns commit identity.

## Initial integration contract

Coordinator owns CLI registry and runtime README integration. Import
`planning_review` in `phase.py`; register `planning.review` calling
`planning_review.review(workspace)` and `planning.repair` calling
`planning_review.repair(workspace, apply=bool(options.get("apply")),
expected=options.get("expect"), only=as_list(options.get("only")))`.
No strict status-inference repair or arbitrary file editing is exposed.

The deterministic report is a lower bound; narrative acceptance, bare canonical
paths, approved human intent, actual commit/check evidence and historical ADR
meaning still require the workflow's cited owner review. The archive API and
CLI registration must be integrated before executing those workflow verbs.
Independent code-reviewer/doc-verifier dispatch and integrated CLI tests remain
coordinator-owned. No benchmarks, model campaign, product changes, publishing,
merging, or unrelated PR work was performed.

## Independent review repair: CR-03 and workflow entrypoint

Follow-up root: `D:/Codex/2026-10-09/task-36/planning-fixes`, branch
`feat/maintenance-planning-fixes`, base
`b00a0c5116d93dd2f447fcb3acb19c2500bde181`. Root, branch and base were checked
before edits; root and branch are checked again before commit. This slice owns
only the audit helper/tests, mirrored entrypoint pair and this summary.

CR-03 identified that containment relative to a resolved `.planning` directory
could permit a linked planning root to read/write outside the repository. The
audit and repair now preflight planning roots, descendant entries and every path
ancestor with `lstat` before content reads or lock creation. They reject ordinary
symlinks and Windows reparse points using `st_file_attributes` (including real
junctions on Python 3.11, without `Path.is_junction`). Planning paths must remain
lexically and physically beneath the actual repository root; repair rechecks its
target immediately before writing. Inventory and repair identifiers stay lexical
repository-relative paths instead of following linked targets.

Canonical template fingerprint inputs receive the same link/ancestor guard within
the runtime's source/installed namespace. This preserves support for a global
host runtime whose templates legitimately live outside the project checkout.
The source namespace is retained lexically so resolving it cannot hide a junction
before its templates are checked. This is a preflight and pre-write guard; it
does not claim protection against an attacker concurrently replacing filesystem
entries between checks and access.

The command/skill pair now loads `.ai/workflows/clean-planning.md` from the project.
Focused installer rendering confirms the Codex and Claude namespace substitutions
and correct skill discovery destinations; the tilde path previously bypassed that
project lookup. The source pair remains byte-identical.

Follow-up checks:

- `python -m unittest discover -s tests -p test_planning_review.py -v`: 28 run,
  24 passed, 4 skipped. The original 18 fixtures still pass. Real Windows root and
  nested planning junctions and a canonical-template namespace junction were
  rejected before any content read, lock or write. Mocked OS symlink metadata
  covers root/file/directory rejection; lexical identifiers and a forged external
  repair candidate are also checked.
- Four actual symlink fixtures (planning root, STATE file, nested directory,
  template file) are present but skipped on this Windows host because symlink
  creation returns `WinError 1314`. They run on a host with symlink privilege.
- `python -m unittest discover -s tests -p test_agent_sources.py -v`: 12 passed.
- `python -m unittest discover -s tests -p test_workflow_links.py -v`: 3 passed.
- `python C:/Users/killi/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/clean-planning`:
  `Skill is valid!`.
- `python .ai/runtime/phase.py query planning.review`: `ok: true`, `unfilled`,
  lexical planning inventory, no findings/repairs. CLI integration is present in
  this follow-up base; the adoption skeleton was inspected without edits.
- `git diff --check`: passed.

The correction commit hash is returned with the final handoff. Independent
re-review of the integrated source remains coordinator-owned. No shared registry,
archive implementation, workflow, project records or other agents' files changed.

## Case-insensitive Markdown fingerprint correction

The next narrow review found that the inventory accepted only lowercase `.md`,
while Windows readers also access a physical `STATE.MD` through `STATE.md`.
Continuation in the same root/branch started from committed `b32dce6`. Inventory
now compares the extension with `casefold()`, preserving physical lexical names,
existing link/reparse guards and containment checks. Uppercase Markdown evidence
therefore participates in the source fingerprint.

- `python -m unittest discover -s tests -p test_planning_review.py -k uppercase -v`:
  2 passed, including the genuine Windows physical `STATE.MD` rename, review and
  post-review mutation. Both regressions reject the old fingerprint with
  `stale-review`, invoke no record writer, preserve existing STATE bytes and leave
  no lock file behind.
- `python -m unittest discover -s tests -p test_planning_review.py`: 30 run,
  26 passed, the same 4 actual-symlink fixtures skipped for Windows privilege.

Only the helper, focused fixtures and this summary changed. No broader checks or
scope expansion accompanied this correction; its commit hash is returned in the
final handoff for immediate integration and independent re-review.

## Self-check

PASSED: all six owned deliverable paths exist; first source commit was verified
in Git. Final source commit identity is returned in the worker's handoff and
recorded by Git; this updated summary is included in that commit.
