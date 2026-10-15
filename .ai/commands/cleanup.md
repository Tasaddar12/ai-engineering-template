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
Read and execute `.ai/workflows/cleanup.md` end to end. Resolve the hook beside
that workflow in the invoking host namespace; installed commands use their
installed hook, not a guessed source checkout. Preview is read only. Apply waits
for the actual human reply approving the displayed exact list and snapshot.
</process>
