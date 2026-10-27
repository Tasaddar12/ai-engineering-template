# Convergence Evidence Gate (#3304)

Bounds Step 7's anti-pattern scan so an approved gap-closure contract can
actually close. Applies **only** when `is_re_verification = true` (Step 0) —
a first pass has no prior contract to be out-of-contract from, so this gate
is a pure no-op there.

## Revision-scoped convergence

Re-verification begins from the previous exact covered revision, stable findings and approved correction scope. Use commit ancestry and a revision diff, never verification timestamps or approximate text overlap, to determine what changed.

```bash
git merge-base --is-ancestor "$PREVIOUS_REVISION" "$CURRENT_REVISION"
git diff --name-status "$PREVIOUS_REVISION" "$CURRENT_REVISION" --
```

If history is missing or ambiguous, record that limitation and request the coordinator's valid comparison base; do not invent regression provenance.

## Finding classification

| Finding | Required evidence | Disposition |
|---------|-------------------|-------------|
| Carried-forward stable finding | Exact ID, authority and unresolved obligation | Recheck its correction and preserve remaining gap |
| Demonstrated regression | Covered revision diff plus reproducible failure | Blocking finding |
| New demonstrated defect | Named failing check or reproducible behavior | Blocking within applicable authority; route scope to coordinator |
| Unsupported architectural preference | No violated contract or reproducible defect | Advisory with rationale |
| Missing required verification | Absent/invalid evidence | Remains a gap; never passed |

A changed file alone does not prove a regression; trace the affected behavior and its evidence. A previously untouched file can still contain a real newly demonstrated defect. Do not suppress evidence because the finding is new.

## Bounded recheck

1. Read the correction packet and exact stable finding dispositions.
2. Compare covered inputs, commands and configuration with current source.
3. Reuse passing receipts only when their command/config/input digest and history remain valid.
4. Rerun affected checks and required independent semantic verification at the frozen revision.
5. Preserve failures, missing evidence and required human judgments. Never upgrade missing verification to passed because all known findings were fixed.
6. Return advisory preferences separately with their limits; do not invent blockers to prolong review or waive demonstrated failures to force convergence.

This gate limits unsupported opinions, not acceptance requirements. A demonstrated failure blocks; an unsupported preference is advisory; neither alters the approved scope without the coordinator's recorded decision.

## Advisory frontmatter

```yaml
advisory: # Only if new-scope findings lack deterministic evidence (Step 7)
  - finding: "Short description of the new-scope concern"
    category: architectural | security | other
    reason: "Why this was raised; what would resolve it"
    evidence_status: "none provided" # or cite what was attempted but inconclusive
```

## Report section

```markdown
### Advisory (New Scope, Unevidenced)

New-scope findings from Step 7 with no deterministic evidence — reported,
not blocking, do not revert a completed must-have.

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | {finding} | {category} | new-scope, no deterministic evidence |
```

Include this section (even if empty, stating "None") whenever
`is_re_verification = true` ran — an omitted section reads as "not
checked," not "checked and clean."

## Worked example (from the issue's reported incident)

Prior pass: `gaps_found`, 4 items — all closed by approved gap-closure plans,
re-verification begins.

- Finding: "the retry loop's backoff strategy is architecturally fragile
  under sustained load." Not in the prior `gaps:` list. The flagged file was
  last modified 3 weeks before this verification pass (before the
  gap-closure plans even started) — not a regression. No test run, no
  reproducible command demonstrating a failure. → **advisory**, does not
  block, does not revert the 4 closed gaps.
- Finding: `TBD: handle the timeout case` left in a file the gap-closure plan
   edited in the covered revision diff. Record the marker, its owning rule and concrete missing obligation; marker text alone is not behavioral failure evidence.
- Finding: a previously-closed gap's file now fails the SAME named test that
  originally proved it broken. → carried-forward gap, blocks.
