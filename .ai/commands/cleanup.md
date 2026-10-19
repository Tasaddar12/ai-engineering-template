---
name: cleanup
description: "Preview owned integrated work and apply only a freshly approved exact deletion list."
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
---

<objective>
Preserve valuable work while reviewing terminal, integrated, clean owned
worktrees, local branches and explicitly recorded backups for removal.
</objective>

<process>
Read and execute `.ai/workflows/cleanup.md` end to end. Resolve its sibling
`../hooks/cleanup.py` in the invoking host namespace. Preview is read only.
Apply waits for the actual human reply approving the displayed exact list and
snapshot. Read `.ai/references/cleanup.md` for eligibility and evidence contracts.
</process>
