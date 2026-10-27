# Gap Closure Mode — Planner Reference

Triggered by `--gaps` flag. Creates plans to address verification or UAT failures.

Read Findings, Acceptance and unresolved UAT actions/gaps as correction inputs. Exclude deferred work only when its deferral is explicitly authorized and recorded. A deferred heading alone cannot remove approved scope.

**1. Find gap sources:**

Use init context (from load_project_state) which provides `phase_dir`:

```bash
# Check for VERIFICATION.md (code verification gaps)
ls "$phase_dir"/*-VERIFICATION.md 2>/dev/null

# Read unresolved UAT actions and gaps; partial sessions are actionable.
ls "$phase_dir"/*-UAT.md 2>/dev/null
```

**2. Parse gaps:** Each gap has: truth (failed behavior), reason, artifacts (files with issues), missing (things to add/fix).

**3. Load existing SUMMARYs** to understand what's already built.

**4. Find next plan number:** If plans 01-03 exist, next is 04.

**5. Group gaps into plans** by: same artifact, same concern, dependency order (can't wire if artifact is stub → fix stub first).

**6. Create gap closure tasks:**

```xml
<task type="auto">
  <name>{fix_description}</name>
  <files>{artifact.path}</files>
  <read_first>{exact current contract and source paths}</read_first>
  <action>
    {For each item in gap.missing:}
    - {missing item}

    Reference existing code: {from SUMMARYs}
    Gap reason: {gap.reason}
  </action>
  <verify>{How to confirm gap is closed}</verify>
  <done>{Observable truth now achievable}</done>
</task>
```

**7. Assign waves using standard dependency analysis** (same as `assign_waves` step):
- Plans with no dependencies → wave 1
- Plans that depend on other gap closure plans → max(dependency waves) + 1
- Also consider dependencies on existing (non-gap) plans in the phase

**8. Write complete PLAN.md files:** include required `acceptance`, `documentation`, `checks` as argv lists, `issue_refs`, exact files/deletions/resources, task read_first and goal-backward evidence.

```yaml
---
phase: XX-name
plan: "NN"            # Sequential after existing
type: execute
wave: N               # Declared label; actual groups also serialize files/resources
depends_on: [...]     # Other plans this depends on (gap or existing)
files_modified: [...]
files_deleted: []
resources: []
acceptance: []
documentation: []
checks: []
issue_refs: []
autonomous: true
gap_closure: true     # Flag for tracking
---
```

**9. Number threat IDs after the phase's existing registers** (#4683): when `security_enforcement` is on, read the `<threat_model>` blocks of the phase's existing PLAN files and continue after their highest `T-{phase}-NN` — do not renumber from `T-{phase}-01`. Every ID already names a specific threat in an earlier plan; reusing it makes `SECURITY.md` rows and `VALIDATION.md`'s Threat Ref column ambiguous. Preserve an existing canonical `T-{phase}-SC` occurrence, but do not mint that reserved ID again in every new plan. New distinct supply-chain findings need unique phase-wide IDs with their own surface/remediation scope. Repeated occurrences of the same canonical risk retain aliases and links without conflating distinct risks. The execute-phase init reports any cross-plan duplicates and hard-stops on them (`threat_id_duplicates`), so a collision surfaces here as a failed plan check.
