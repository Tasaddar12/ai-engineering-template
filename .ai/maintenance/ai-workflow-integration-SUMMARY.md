# AI workflow integration correction

- **CR-01:** Corrected `.ai/workflows/execute-phase.md` so it permits opening or
  updating the tracking draft after an integrated slice and applicable checks,
  while keeping verified delivery and merging under `/ship`. The tracking step,
  pending-verification wording, and other gates and rollback guidance remain
  intact.
- **Source evidence:** `track_integrated_slice` in `execute-phase.md` requires
  the tracking draft after integration and applicable checks. The canonical
  `.ai/references/git-workflow.md` says a draft is tracking only, while the
  `.agents/skills/ship/SKILL.md` gates publication on current passed verification
  and says merge happens only on the user's instruction.
- **Checks:** `git diff --check` passed; inspected the exact patch and confirmed
  only the assigned workflow and this summary are changed.
- **Review:** Independent review and CI are pending; this correction does not
  claim either result.
