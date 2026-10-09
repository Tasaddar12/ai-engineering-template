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

## Integration contract and remaining work

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

## Self-check

PASSED: all six owned deliverable paths exist; first source commit was verified
in Git. Final source commit identity is returned in the worker's handoff and
recorded by Git; this updated summary is included in that commit.
