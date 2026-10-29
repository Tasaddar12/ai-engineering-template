# Legacy core retirement maintenance plan

The human requested a stacked PR against PR 129 on 2026-10-28, a very deep review of every file in agents/, commands/, skills/ and engineer/, removal of confirmed retired GSD components, and no merge. This is template maintenance; the adopting-project identity and planning skeleton remain unfilled.

Base: 7723b2d1ce2b0d698613639547c35e2b98688a70, PR 129 branch phase-overhaul-mechanical.

## Acceptance

- R1: Full-content inspection of all 434 tracked files at the base; coverage.json records every path, byte count, line count, SHA256 and reviewer.
- R2: Remove confirmed retired implementations, advertised routes and callers together. Preserve local replacements and the PR 127 human retention overrides.
- R3: Preserve supported manager/pipelines/issues/ideas, internal independent review, isolated execution, owned process supervision, verification gates and probes. Replace dynamic hook plumbing with the already selected direct gates.
- R4: Check retired command rejection, supported runtime imports and representative behavior; detect new broken local links and orphaned callers. Report pre-existing migration gaps separately.
- R5: Publish only this delta as a draft targeting phase-overhaul-mechanical. Do not merge or rewrite parent history.

## Owned slices

| Slice | Owner | Source ownership | Summary |
|---|---|---|---|
| entrypoints | coder | agents/, commands/, skills/ | entrypoints-SUMMARY.md |
| workflows | coder | engineer/workflows/ | workflows-SUMMARY.md |
| runtime | coder | engineer/bin/, tests/ | runtime-SUMMARY.md |
| references | doc-writer | engineer/references/, engineer/templates/ | references-SUMMARY.md |

Workers use separate runtime-created worktrees and commit exact owned paths plus their summary. No shared planning records or publication. The coordinator joins every worker, integrates through worktree.merge-wave, checks the merged revision, publishes and obtains fresh independent review. Every deletion must be enumerated before integration.

## Preservation boundaries

Retain the complete seed, note, session-report, extract-learnings, graduation, scan, milestone-write, quick discussion/research and native discussion-analysis methods. Keep host-qualified @~/.claude imports for installer translation. Preserve the human-authored code-fixer method and examples while removing only confirmed retired ownership/opt-out blocks.

Keep response-language-directive.md, ui-brand.md and run-resolver.md where deletion/repointing rows conflict. Keep the six Batch B references until their replacement prerequisites exist. This PR does not perform the remaining general semantic or installer migration.

## Checks

Run checks appropriate to the source changes, including syntax/import smoke checks, the retained runtime tests affected by retirement, command/skill equality, normalized local link comparison and independent source review. The adoption configuration has no project check commands; report exact checks actually run rather than claiming that empty configuration passed acceptance.
