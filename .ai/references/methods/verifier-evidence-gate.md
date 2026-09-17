# Convergence Evidence Gate

Bounds Step 7's anti-pattern scan so an approved gap-closure contract can
actually close. Applies **only** when `is_re_verification = true` (Step 0) —
a first pass has no prior contract to be out-of-contract from, so this gate
is a pure no-op there.

## Purpose

Re-verification must close actual gaps without promoting a fresh architectural
opinion into a new acceptance criterion. Retain the original approved outcomes,
check repairs and regressions, and separate supported defects from preferences.
This evidence discipline never waives current acceptance or a demonstrated defect.

## Definitions

**Carried-forward gap:** a prior report's unresolved finding tied to the same
acceptance and behavior. Match IDs, paths and the substantive problem; fuzzy token
overlap is only a search aid. Confirm the failure still exists.

**Possible regression:** behavior in code changed since the prior verified
revision. Compare revisions rather than relying on wall-clock timestamps:

```bash
git diff --name-status "$PREVIOUS_REVISION" "$CURRENT_REVISION"
git diff "$PREVIOUS_REVISION" "$CURRENT_REVISION" -- "$file"
```

A changed file directs inspection; it is not itself proof of a defect. If history
is unavailable, disclose the limitation and inspect the current behavior. Do not
claim that an unresolvable timestamp proves a regression.

**New concern:** an observation not previously reported and not tied to a changed
required path. Determine whether it is a real defect or a design preference.
The explicit debt-marker gate still applies: an unreferenced `TBD`, `FIXME` or
`XXX` in a changed file blocks completion. A referenced marker must also be
checked for unmet required behavior; traceability never waives acceptance.

**Deterministic evidence** — required for a new-scope finding to stay
blocking. One of:

- A **named test that FAILS when actually run** (red). Run the smallest relevant check authorized by the assignment; honor an explicit
  no-tests request and record that execution evidence is pending. Record the exact command and the failing output.
- **Direct source evidence** of a contradiction, with the relevant entry point,
  data/control path and why the required outcome cannot hold. Source evidence
  must demonstrate the defect, not merely an unusual pattern.
- **Another concrete, reproducible artifact** — a command + output that
  demonstrates the defect (a crash, a probe failure, a reproducible bad
  response). An assertion, opinion or architectural preference without a demonstrated
  causal path is not evidence, however confidently stated.

## The gate

- A demonstrated failure of current acceptance or a supported code defect remains
  blocking, whether old or new. Explain its evidence and practical impact.
- An unsupported preference or hypothesis is advisory. Keep its reasoning and
  the missing evidence visible without reverting completed outcomes.
- A required outcome that remains unverified still needs evidence; an advisory
  classification must not turn missing verification into `passed`.
- Report a scope conflict to the coordinator; do not invent new requirements or
  silently defer current ones. User restrictions on tests remain in effect.

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

## Worked example

Prior pass: `gaps_found`, 4 items — all closed by approved gap-closure plans,
re-verification begins.

- Finding: "the retry loop's backoff strategy is architecturally fragile
  under sustained load." Not in the prior `gaps:` list. The flagged file was
  last modified 3 weeks before this verification pass (before the
  gap-closure plans even started) — not a regression. No test run, no
  reproducible command demonstrating a failure. → **advisory**, does not
  block, does not revert the 4 closed gaps.
- Finding: `TBD: handle the timeout case` left in a file the gap-closure plan
  edited this pass. → inspect the timeout path. If required timeout handling is absent, record
  that implementation gap; the missing same-line follow-up also triggers the explicit debt-marker gate.
- Finding: a previously-closed gap's file now fails the SAME named test that
  originally proved it broken. → carried-forward gap, blocks.
