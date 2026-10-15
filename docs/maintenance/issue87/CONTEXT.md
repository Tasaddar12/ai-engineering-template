---
issue_refs:
  - https://github.com/Tasaddar12/ai-engineering-template/issues/87
status: authorized
input_revision: 77b5668f2003bea60127d87e8785469286abafb3
---

# Issue 87 maintenance scope

## Authorization

The user explicitly requested investigation, planning and implementation today through multiple parallel subagents, isolated Git worktrees and stacked draft PRs. Publishing these PRs is authorized. Never merge a PR or close issue 87. This maintenance record preserves that instruction; no adopting-project phase or identity is invented.

## Decisions

- Preserve PR86 advisory worktree guard behavior, including ordinary scratchpad writes. Add destructive-operation safeguards separately.
- Preserve existing explicit authorization across internal workflow transitions. Ask only for new authority where an action exceeds written scope or requires destructive approval.
- Preserve GitHub and GitLab behavior. Issues73/74 and PRs76/77 own provider changes; do not implement those adapters here.
- Keep current canonical threat identity, safe disclosure and closure-evidence requirements. Add phase checklist tracking for planned security work and separate tracking for unplanned threats without hiding individual risk identity.
- Keep source changes narrow. No benchmark harnesses, unrelated checkout changes, installs or infrastructure changes.
- Independent plans own disjoint source paths. A later integration/cleanup slice may depend on earlier delivered guard behavior; stack only real dependencies.

## Acceptance

1. Destructive branch/worktree actions with open PR/MR and unapproved backup deletion are refused; primary checkout branch switches are refused. Tests exercise refusal and legitimate commands.
2. Cleanup previews only merged/closed eligible items, preserves unknown/open/dirty/unowned work, obtains exact deletion-list approval and reports final state.
3. Static guard repairs enumerate bypass and false-positive cases and write/run failing tests before implementation.
4. CONTEXT/PLAN/SUMMARY required frontmatter including issue_refs is validated before planning-record commits; runtime state/roadmap mutations report or prevent authored-content truncation.
5. Upstream comparison distinguishes CRLF-only from substantive changes and preserves authored planning content; shell/nginx files remain LF.
6. Parallel runs show each wave's worker/role/model, plan/execute/verify state, last progress, stall flag, blocker and PR. Stalls do not silently imply completion.
7. Review audits issue links; planned phase security risks can share a checklist while unplanned risks retain separate actionable tracking and safe lifecycle evidence.

## Investigation

- Main: 77b5668, PR86 advisory worktree guards; PR80 threat tracking and PR84 phase issue handoffs already merged.
- Open PR76 targets GitLab MR delivery for issue73; PR77 targets GitLab TODO publication for issue74. Both remain outside this assignment.
- Related issues81/82 preserve safe disclosure, canonical risk identity and evidenced closure. Issues66/67 describe separate planning retry/entry-path gaps; avoid unrelated rewrites.
- Issue87 latest comment requests phase security checklists and pre-merge issue-link review. The earlier comment's unattended-sync/autopilot examples are suggestions; implement bounded relevant guardrails without new automation or merge authority.
