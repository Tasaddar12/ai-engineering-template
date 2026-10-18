---
issue_refs:
  - https://github.com/Tasaddar12/ai-engineering-template/issues/100
  - https://github.com/Tasaddar12/ai-engineering-template/issues/87
status: authorized
input_revision: d48d10d9fa9fb33dc05ad8552329aceee4e7d5cc
---

# PR89 correction scope

## Authorization

- User approved: “Go ahead and fix the findings for PR 89.”
- Push corrections to the existing PR89; leave it unmerged and draft.
- User clarified: “This project is to be installed on systems, not to track itself in .planning.”
- User selected the tracking destination: “You track them in docs/maintenance like the rest.”
- Keep PR97 and PR99 untouched. Their separate platform-blocked operations are outside this task.

## Decisions

| Boundary | Required outcome |
|---|---|
| Checklist identity | Deterministic per-phase lookup before semantic risk search; default for new planned risks; preserve matching canonical issues. |
| Risk entries | Latest issue100 addendum replaces comments with stable `###` headings in the checklist issue body and verified heading-anchor URLs; renaming headings breaks links. Link each owning PLAN's assessment and mitigation. |
| Audit | Verifier owns the canonical audit; ship refreshes missing/stale evidence through a fresh non-author verifier. Preserve the existing gate. |
| Worker lifecycle | Use actual host observations; distinguish a wait timeout from confirmed worker exit; confirm stop before reassignment. |
| Status display | Full tables at dispatch/final; changed rows at intermediate updates; dispatch/join only when the host blocks. |
| Registers | Keep the six-column PLAN registers and avoid duplicate severity/mitigation registers. |
| Tests | Simplify both instruction-contract suites while retaining semantic and structural regression coverage. |
| Compatibility | Check exact PR76 tip without merging it; report conflicts rather than changing its adapter. |
| Maintenance | Record task evidence here and in PR89/issue100; preserve the installable .planning skeleton. |

## Acceptance and evidence

- [Issue100](https://github.com/Tasaddar12/ai-engineering-template/issues/100) owns the requested ten-item acceptance list.
- [Item 2 addendum](https://github.com/Tasaddar12/ai-engineering-template/issues/100#issuecomment-6221536882) supersedes the original comment-entry requirement: use issue-body headings and anchors, and remove the “(comment)” label.
- [PR89](https://github.com/Tasaddar12/ai-engineering-template/pull/89) owns publication and current CI evidence.
- Focused affected tests and exact-head Ubuntu/Windows CI must be reported as actually observed.
- No benchmarks, native security probes, merges, unrelated adapter repairs or large rewrites.

## Baseline investigation

- PR89 head: `d48d10d9fa9fb33dc05ad8552329aceee4e7d5cc`; draft; branch `phase-issue87-orchestration`.
- PR76 head: `3765c6bacedd9af6b86ab3342fa025d47f20b3ae`; branch `codex/gitlab-delivery`.
- Baseline `git merge-tree --write-tree <PR89 head> <PR76 head>` returned exit 1 with a content conflict in `.ai/runtime/lib/delivery.py`; `.ai/workflows/ship.md` auto-merged. Corrected-tip compatibility remains to be checked.
- Baseline offline suites passed: 5 parallel-status tests and 21 threat-tracking tests. These establish the starting point, not correction acceptance.
- Ship already has an audit gate; verifier and code-reviewer duties overlap. Ownership and refresh dispatch need correction.
