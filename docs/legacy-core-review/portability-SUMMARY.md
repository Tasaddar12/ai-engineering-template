# Final workflow identity and portability correction

## Why

Repair the two remaining bounded source defects CR08 and CR09 without changing runtime behavior, host evidence policy or broader orchestration.

## Changes

- CR08: both new phase-execution SUMMARY assignments now read the full id directly from the selected phase-plan-index plan_json entry and derive the same repo-relative `${plan_id}-SUMMARY.md` path. records.plan_index derives this id from the exact PLAN filename stem; the bare frontmatter plan number and unbound plan_padded variable are not used by these assignments. Checkout ownership and the terminal receipt therefore retain the exact selected SUMMARY identity.
- CR09: Quick manifest, shared native terminal receipt and batch merge manifest creation now pass suffixless XXXXXX templates to mktemp, then rename/append .json. All mktemp sites in the four owned workflow files were inspected; the existing suffixless execute-wave site remains unchanged.

## Verification

Root: D:/Codex Projects/ai-engineering-template/.worktrees/legacy-portability-205504142.
Branch: phase-legacy-portability.
Verified initial revision: 67627af5f621cf3325d488776956ec30c1b7a90a.

- git diff --check: passed.
- Actual CLI phase-plan-index plus extracted Bash assignment fixtures: 4 passed, covering both isolation assignment sites with phase 01/plan 02 and dotted phase 01.1/plan 02, directories containing spaces, actual schema ids 01-02 and 01.1-02, and deliberately unbound plan_padded. Each derived path matched the actual runtime summary_path and selected PLAN filename sibling.
- Extracted temp creation/rename snippets under a strict BSD-style template wrapper: 3 real filesystem fixtures passed. The wrapper required terminal XXXXXX, rejected the old XXXXXX.json shape as a control, then delegated the valid requests to installed mktemp and verified the renamed .json file exists without a leftover suffixless file. This simulates the template restriction; no live macOS/BSD execution is claimed.
- Static scan of every mktemp site in the four assigned files: no suffix-after-X template remains.
- Markdown and Git Bash bash -n comparison: 49 original / 49 edited Bash fences; no added unbalanced/nested fences or syntax failures.
- Exact scope and deletion guard: only the four assigned workflow files plus this summary; no deletions, runtime edits, shared planning changes, integration or publication.

## Rows

Independent final review findings CR08 (exact SUMMARY identity) and CR09 (portable mktemp templates). All other findings and parent migration surfaces remain outside this correction.
