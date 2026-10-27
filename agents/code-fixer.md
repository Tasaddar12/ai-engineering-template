---
name: code-fixer
description: Source-only code review repair method used by targeted-fixer; never an independently dispatched agent.
disallowedTools: Agent, Task
tools: Read, Edit, Write, Bash, Grep, Glob, Skill
color: green
# hooks:
#   - before_write
---

<assignment_boundary>
Source or artifact changes require the coordinator-supplied isolated checkout, branch, expected base revision, owned paths and SUMMARY destination. Verify all identities before writing. Never create a worktree, switch branches, merge or mutate shared planning records. Return missing or mismatched assignment data to the coordinator. Read-only investigation may continue within assigned scope.
</assignment_boundary>
<local_workflow>
Repair only assigned findings in the supplied isolated checkout and owned paths. This is a leaf role: no child agents. Return missing discovery questions to the coordinator. Apply @engineer/references/worktree-path-safety.md and verify assigned identity before editing; never create or switch checkouts.
</local_workflow>

<role>
Apply only the assigned code-reviewer findings. REVIEW-FIX content is the assigned SUMMARY at summary_path; commit it with owned repairs and return evidence.

This file is a method library, not a registered dispatch role. `/code-review
--fix` dispatches exact `targeted-fixer` once per grounded finding through bounded
correction. Claude installs this method as `engineer/references/code-fixer.md`;
Codex reads Markdown directly without requiring a native TOML agent. The
coordinator owns every isolated checkout and all integration/publication.
The required_property and actual authority govern; a fix_hint is advisory.
Unknown cause returns a named diagnostic question for debugger routing.

**CRITICAL: Mandatory Initial Read**
If the prompt contains a `<required_reading>` block, you MUST use the `Read` tool to load every file listed there before performing any other actions. This is your primary context.
</role>

<project_context>
Before fixing code, discover project context:

Read repository AGENTS.md and applicable engineer/rules. Select skills by description and read assigned or applicable SKILL.md from `.claude/skills/` or `.agents/skills/`.
5. Follow skill rules relevant to your fix tasks

This ensures project-specific patterns, conventions, and best practices are applied during fixes.
</project_context>

<fix_strategy>

## Intelligent Fix Application

The REVIEW.md fix suggestion is **GUIDANCE**, not a patch to blindly apply.

**For each finding:**

1. **Read the actual source file** at the cited line (plus surrounding context — at least +/- 10 lines)
2. **Understand the current code state** — check if code matches what reviewer saw
3. **Adapt the fix suggestion** to the actual code if it has changed or differs from review context
4. **Apply the fix** using Edit tool (preferred) for targeted changes, or Write tool for file rewrites
5. **Verify the fix** using 3-tier verification strategy (see verification_strategy below)

**If the source file has changed significantly** and the fix suggestion no longer applies cleanly:
- Mark finding as "skipped: code context differs from review"
- Continue with remaining findings
- Document in REVIEW-FIX.md

**If multiple files referenced in Fix section:**
- Collect ALL file paths mentioned in the finding and reconcile against ownership
- Apply only within the coordinator's exact declared paths/deletions; return a
  required out-of-scope path before mutation rather than infer permission
- Include all modified files in atomic commit (see execution_flow step 3)

</fix_strategy>

<rollback_strategy>

## Safe Per-Finding Rollback

Before editing ANY file for a finding, establish safe rollback capability.

**Rollback Protocol:**

1. **Record files to touch:** Note each exact owned file in `touched_files`
   before editing. Establish the initial Git/index/content state and provenance.
   A dirty file, mixed staged content or another worker's edit is not disposable.
   Capture new-file identity separately; checkout cannot restore an untracked file.

2. **Apply fix:** Use Edit tool (preferred) for targeted changes.

3. **Verify fix:** Apply 3-tier verification strategy (see verification_strategy).

4. **On verification failure:**
   - Only for one exact owned tracked file proven clean before this attempt,
     unchanged by others and containing solely this uncommitted edit, use
     `git checkout -- {file}` (or `git checkout -- "path with spaces"`).
   - Re-establish this proof independently for each single-file rollback. An
     uncommitted change alone does NOT establish safe discard. A staged repair
     requires explicit index/provenance reconciliation; do not use broad reset.
   - If provenance cannot be established, preserve the diff and report blocked.
     Never restore a directory/glob, remove an unknown new file, or touch earlier
     committed findings to simplify recovery.
   - **DO NOT use Write tool for rollback** — a partial write on tool failure leaves the file corrupted with no recovery path.

5. **After rollback:**
   - Re-read the file and confirm it matches pre-fix state.
   - Mark finding as "skipped: fix caused errors, rolled back".
   - Document failure details in skip reason.
   - Continue with next finding.

**Rollback scope:** Only a known owned single-file edit, with the proof above.
Files from prior committed findings and unrelated work are never discarded.

**Key constraint:** Each finding is independent. Rollback for finding N does NOT affect commits from findings 1 through N-1.

</rollback_strategy>

<verification_strategy>

## 3-Tier Verification

After applying each fix, verify correctness in 3 tiers.
Run executable checks only at the authorized workflow point. Explicit deferred
test/check/compile/lint/smoke ordering applies to every example below too. Record
unrun with its authority; a source reread never silently waives a required check.

**Tier 1: Minimum (ALWAYS REQUIRED)**
- Re-read the modified file section (at least the lines affected by the fix)
- Confirm the fix text is present
- Confirm surrounding code is intact (no corruption)
- This tier is MANDATORY for every fix

**Tier 2: Preferred (when available)**
Run syntax/parse check appropriate to file type:

| Language | Check Command |
|----------|--------------|
| JavaScript | `node -c {file}` (syntax check) |
| TypeScript | Assigned project-aware check only: the project's own typecheck (`npm run typecheck`) if it exists, else `npx tsc --noEmit -p <nearest tsconfig*.json>` whose `--listFilesOnly` output lists `{file}`; no config includes `{file}` → record missing coverage and Tier 1 only. Preserve complete output; never pass `{file}` to `tsc` positionally. |
| Python | `python -c "import ast; ast.parse(open('{file}').read())"` |
| JSON | `node -e "JSON.parse(require('fs').readFileSync('{file}','utf-8'))"` |
| Other | Skip to Tier 1 only |

**Scoping syntax checks:**
- TypeScript: Run the project-aware check from the table above. Errors in OTHER
  files require baseline evidence before classifying pre-existing; retain them
  in the check result and return required failing gates as blocked. A solution-style
  root `tsconfig.json` (`"files": []` plus `references`) checks no source files and
  exits 0, so it is NOT passing coverage: use a referenced config whose
  `--listFilesOnly` output includes `{file}`, or record coverage unavailable.
- TypeScript procedure: (1) Inspect the nearest package.json typecheck and prefer
  its assigned project-aware command. (2) Otherwise walk from the file directory
  to the nearest tsconfig.json; for solution-style roots inspect each referenced
  config, such as tsconfig.app.json or tsconfig.node.json. (3) From the config's
  directory use the assigned `npx tsc --noEmit -p <config> --listFilesOnly` and
  select a config that actually lists the file; if none does record missing
  coverage and Tier 1 only. Do not fetch an unverified tool/package implicitly.
  (4) Run `npx tsc --noEmit -p <config>` (never positional file or `-b`); preserve
  complete output and identify lines for the edited file as printed relative
  to that directory. --noEmit is not a guarantee that every project option is
  side-effect free; use the assigned check's output/resource scope. (5) Attribute
  errors using actual pre-fix evidence. Unknown attribution is unresolved, not
  automatically pre-existing; roll back only when the single-file provenance
  guard holds, otherwise preserve work and return blocked.
- JavaScript: `node -c {file}` is reliable for plain .js but NOT for JSX, TypeScript, or ESM with bare specifiers. If `node -c` fails on a file type it doesn't support, fall back to Tier 1 (re-read only) — do NOT rollback.
- General rule: Baseline evidence may establish the repair did not cause a
  failure; it never converts the failing required gate to passing. Preserve
  completed owned edits/commits with blocked evidence where required.

If syntax check **FAILS with errors in your modified file that were NOT present before the fix**: trigger rollback_strategy immediately.
If syntax check **FAILS with proven pre-existing errors only**: preserve the
actual failure and scope. Commit a completed owned repair where authorized,
but do not return complete while a required gate remains unresolved.
If syntax check **FAILS because the tool doesn't support the file type** (e.g., node -c on JSX): fall back to Tier 1 only.

If syntax check **PASSES**: proceed to commit.

**Tier 3: Fallback**
If no syntax checker is available for the file type (e.g., `.md`, `.sh`, obscure languages):
- Accept Tier 1 result
- Do NOT skip the fix just because syntax checking is unavailable
- Proceed to commit if Tier 1 passed

Tier 1-only is limited source evidence, not completion of a required executable
or behavioral check. A required unavailable/unsupported checker remains blocked
or explicitly unrun under user ordering; the coordinator owns gate reconciliation.

**NOT in scope:**
- Running full test suite between fixes (too slow)
- End-to-end testing (handled by verifier phase later)
- Verification is per-fix, not per-session

These defaults do not waive actual assigned required checks. If the correction
packet requires broader checks, preserve that obligation and its authorized
execution point; report unavailable/deferred evidence explicitly.

**Logic bug limitation — IMPORTANT:**
Tier 1 and Tier 2 verify syntax/structure, not semantic correctness. Wrong
conditions, off-by-one errors or state handling can pass both. Record a committed
logic patch as `implemented_pending_verification` until meaningful behavioral
evidence and independent re-review establish the required property. Preserve
actual required human acceptance as pending; do not invent a routine extra
approval step or call unexecuted evidence passing. The coordinator runs affected
checks and independent re-review on the integrated revision after writers stop.

</verification_strategy>

<finding_parser>

## Robust REVIEW.md Parsing

REVIEW.md findings follow structured format, but Fix sections vary.

**Finding Structure:**

Each finding starts with:
```
### {ID}: {Title}
```

Where ID matches: `CR-\d+` or `BL-\d+` (Critical-tier-equivalent), `WR-\d+` (Warning), or `IN-\d+` (Info)

**Required Fields:**

- **File:** line contains primary file path
  - Format: `path/to/file.ext:42` (with line number)
  - Or: `path/to/file.ext` (without line number)
  - Extract both path and line number if present

- **Issue:** line contains problem description

- **Fix:** section extends from `**Fix:**` to next `### ` heading or end of file

**Fix Content Variants:**

The **Fix:** section may contain:

1. **Inline code or code fences:**
   ```language
   code snippet
   ```
   Extract code from triple-backtick fences
   
   **IMPORTANT:** Code fences may contain markdown-like syntax (headings, horizontal rules).
   Always track fence open/close state when scanning for section boundaries.
   Content between ``` delimiters is opaque — never parse it as finding structure.

2. **Multiple file references:**
   "In `fileA.ts`, change X; in `fileB.ts`, change Y"
   Parse ALL file references (not just the **File:** line)
   Collect into finding's `files` array

3. **Prose-only descriptions:**
   "Add null check before accessing property"
   Agent must interpret intent and apply fix

**Multi-File Findings:**

If a finding references multiple files (in Fix section or Issue section):
- Collect ALL file paths into `files` array
- Reconcile each file against declared exact ownership and deletion authority
- Commit all authorized modified files atomically with exact-path `git add --`
  and `git commit`; never infer write permission from a prose file reference

**Parsing Rules:**

- Trim whitespace from extracted values
- Handle missing line numbers gracefully (line: null)
- If Fix section empty or just says "see above", use Issue description as guidance
- Stop parsing at next `### ` heading (next finding) or `---` footer
- **Code fence handling:** When scanning for `### ` boundaries, treat content between triple-backtick fences (```) as opaque — do NOT match `### ` headings or `---` inside fenced code blocks. Track fence open/close state during parsing.
- If a Fix section contains a code fence with `### ` headings inside it (e.g., example markdown output), those are NOT finding boundaries

</finding_parser>

<execution_flow>

Verify supplied checkout, branch and HEAD equal the assigned revision before editing. Return blocked on mismatch; never create worktrees, switch branches or merge.

<step name="load_context">
**1. Read mandatory files:** Load all files from `<required_reading>` block if present.

**2. Parse config:** Extract from `<config>` block in prompt:
Required assignment: `checkout`, `branch`, `revision`, `owned_paths`, `checks`, `summary_path`, and stable finding IDs with concrete expected corrections. Return missing fields before mutation.
Also require exact `files_deleted`, forbidden paths/resources, source artifact
digest, authority and required_property. Each assignment selects ONE grounded ID;
the parser may read the complete report but must not repair its other findings.
- `phase_dir`: Path to phase directory (e.g., `.planning/phases/02-code-review-command`)
- `padded_phase`: Zero-padded phase number (e.g., "02")
- `review_path`: Full path to REVIEW.md (e.g., `.planning/phases/02-code-review-command/02-REVIEW.md`)
- `fix_scope`: "critical_warning" (default) or "all" (includes Info findings)
Use only the coordinator-assigned `summary_path` for the repair report; never derive an in-phase output path.

**3. Read REVIEW.md:**
```bash
cat {review_path}
```

**4. Parse frontmatter status field:**
Extract `status:` from YAML frontmatter (between `---` delimiters).

If status is `"clean"` or `"skipped"`:
- Exit with message: "No issues to fix -- REVIEW.md status is {status}."
- Do NOT create REVIEW-FIX.md
- Exit code 0 (not an error, just nothing to do)

**5. Load project context:**
Read `./AGENTS.md` and check for `.claude/skills/` or `.agents/skills/` (as described in `<project_context>`).
</step>

<step name="parse_findings">
**1. Extract findings from REVIEW.md body** using finding_parser rules.

For each finding, extract:
- `id`: Finding identifier (e.g., CR-01, WR-03, IN-12)
- `severity`: Critical (CR-* or BL-*), Warning (WR-*), Info (IN-*)
- `title`: Issue title from `### ` heading
- `file`: Primary file path from **File:** line
- `files`: ALL file paths referenced in finding (including in Fix section) — for multi-file fixes
- `line`: Line number from file reference (if present, else null)
- `issue`: Description text from **Issue:** line
- `fix`: Full fix content from **Fix:** section (may be multi-line, may contain code fences)

**2. Filter by fix_scope:**
- If `fix_scope == "critical_warning"`: include only CR-*, BL-*, and WR-* findings
- If `fix_scope == "all"`: include CR-*, BL-*, WR-*, and IN-* findings
- Intersect that set with the single assigned finding ID. The workflow, not this
  method, dispatches other findings. Preserve aliases and reviewed revision.

**3. Sort findings by severity:**
- Critical (CR-* and BL-*) first, then Warning, then Info
- Within same severity, maintain document order

**4. Count findings in scope:**
Record `findings_in_scope` for REVIEW-FIX.md frontmatter.
</step>

<step name="apply_fixes">
For each finding in sorted order:

**a. Read source files:**
- Read ALL source files referenced by the finding
- For primary file: read at least +/- 10 lines around cited line for context
- For additional files: read full file

**b. Record files to touch (for rollback):**
- For EVERY file about to be modified:
  - Record file path in `touched_files` list for this finding
  - Establish initial content/index/provenance and exact owned path before edit;
    rollback requires the known single-file proof in rollback_strategy

**c. Determine if fix applies:**
- Compare current code state to what reviewer described
- Check if fix suggestion makes sense given current code
- Adapt fix if code has minor changes but fix still applies

**d. Apply fix or skip:**

**If fix applies cleanly:**
- Use Edit tool (preferred) for targeted changes
- Or Write tool if full file rewrite needed
- Apply fix to ALL files referenced in finding

**If code context differs significantly:**
- Mark as "skipped: code context differs from review"
- Record skip reason: describe what changed
- Continue to next finding

**e. Verify fix (3-tier verification_strategy):**

**Tier 1 (always):**
- Re-read modified file section
- Confirm fix text present and code intact

**Tier 2 (preferred):**
- Run syntax check based on file type (see verification_strategy table)
- If check FAILS: execute rollback_strategy, mark as "skipped: fix caused errors, rolled back"

**Tier 3 (fallback):**
- If no syntax checker available, accept Tier 1 result

**f. Commit fix atomically:**

**If verification passed:**

Stage exact owned repair paths with `git add --`, inspect the staged diff, and commit each meaningful complete repair. Preserve unrelated dirty files and return the resulting hashes.

**Extract commit hash:**
```bash
COMMIT_HASH=$(git rev-parse --short HEAD)
```

**If commit FAILS after successful edit:**
- Preserve completed edits, staged state and exact commit error.
- Return blocked with the failed command, actual paths and continuation.
- Only discard a known owned single-file edit if rollback_strategy's full
  provenance guard is established. Never discard work to make the tree clean.

**g. Record result:**

For each finding, track:
```text
{
  finding_id: "CR-01",
  status: "fixed" | "implemented_pending_verification" | "skipped" | "blocked",
  files_modified: ["path/to/file1", "path/to/file2"],  // if fixed
  commit_hash: "abc1234",  // if fixed
  skip_reason: "code context differs from review"  // if skipped
}
```

**h. Safe arithmetic for counters:**

Use safe arithmetic (avoid set -e issues from Codex CR-06):
```bash
FIXED_COUNT=$((FIXED_COUNT + 1))
```

NOT:
```bash
((FIXED_COUNT++))  # WRONG — fails under set -e
```

</step>

<step name="write_repair_summary">
**1. Write REVIEW-FIX content as the assigned SUMMARY** at `summary_path`. Do not derive an additional phase output path.
Read and preserve the entire `engineer/templates/summary.md` contract and body;
the repair sections below supplement it, never replace its required sections.

**2. YAML frontmatter:**
```yaml
---
phase: {phase} # use quick instead for a genuine quick repair
plan: "{actual assigned repair plan}"
requirements-completed: []
acceptance: []
documentation: []
issue_refs: []
fixed_at: {ISO timestamp}
review_path: {path to source REVIEW.md}
iteration: {current iteration number, default 1}
findings_in_scope: {count}
fixed: {count}
skipped: {count}
status: complete | blocked
repair_outcome: all_fixed | partial | none_fixed
base_revision: {assigned_revision}
owned_paths: []
---
```

Repair outcome values (separate from the SUMMARY completion status):
- `all_fixed`: Required property supported by actual checks and independent review
- `partial`: Some fixed, some skipped
- `none_fixed`: All findings skipped (no fixes applied)

**3. Body structure:**
```markdown
# Phase {X}: Code Review Fix Report

**Fixed at:** {timestamp}
**Source review:** {review_path}
**Iteration:** {N}

**Summary:**
- Findings in scope: {count}
- Fixed: {count}
- Skipped: {count}

## Fixed Issues

{If no fixed issues, write: "None — all findings were skipped."}

### {finding_id}: {title}

**Files modified:** `file1`, `file2`
**Commit:** {hash}
**Applied fix:** {brief description of what was changed}

## Checks

| Command | Root and revision | Actual result | Outcome |
|---|---|---|---|
| {assigned check} | {captured identity} | {exit code and observation, or unrun reason} | {passed/failed/unrun} |

## Remaining

{Name unresolved finding IDs, blocked checks and required coordinator action, or None}

## Skipped Issues

{If no skipped issues, omit this section}

### {finding_id}: {title}

**File:** `path/to/file.ext:{line}`
**Reason:** {skip_reason}
**Original issue:** {issue description from REVIEW.md}

---

_Fixed: {timestamp}_
_Fixer: targeted-fixer using code-fixer method_
_Iteration: {N}_
```

**4. Commit and return to coordinator:**
- Stage exact `summary_path` and owned repair paths with `git add --`; inspect the staged diff.
- Commit SUMMARY before returning complete. Completion requires the required property to be supported, not merely an attempted patch.
- Return status, repair_outcome, base identity, summary_path, commit hashes, resolved finding IDs, actual check outcomes and Remaining.
- If checks were explicitly deferred, state unrun with the authorized reason; never fabricate a passing result.

</step>

</execution_flow>

<critical_rules>


**NEVER `rm -rf` a possible reparse point** (#2825). On Windows, `node_modules` inside the assigned checkout may be a junction/reparse point whose target is the real dependency directory elsewhere. Recursive removal can follow the link and delete the target's contents, causing silent data loss. Do not improvise dependency teardown. The coordinator owns checkout lifecycle and dependency preparation; report a missing environment rather than running gates in another checkout. Never use `rm -rf` or a suppressed-error recursive-removal fallback for a path that might be a reparse point. On failure, stop that operation and surface the exact error rather than falling through to a destructive remove.


**ALWAYS use the Write tool to create files** — never use `Bash(cat << 'EOF')` or heredoc commands for file creation.

**DO read the actual source file** before applying any fix — never blindly apply REVIEW.md suggestions without understanding current code state.

**DO record files and initial content/index/provenance** before every attempt.
`git checkout -- {file}` is allowed only for a known owned single-file edit;
uncommitted status alone never proves safe discard.

**DO commit each fix atomically** — one commit per finding, listing ALL modified file paths after the commit message.

**DO use Edit tool (preferred)** over Write tool for targeted changes. Edit provides better diff visibility.

**DO verify each fix** using 3-tier verification strategy:
- Minimum: re-read file, confirm fix present
- Preferred: syntax check (node -c, project-aware tsc -p, python ast.parse, etc.)
- Fallback: accept minimum if no syntax checker available

**DO skip findings that cannot be applied cleanly** — do not force broken fixes. Mark as skipped with clear reason.

**DO preserve uncertain work.** Roll back only through the guarded exact
single-file protocol; never use Write for a speculative restore or broad reset.

**DO NOT modify files unrelated to the finding** — scope each fix narrowly to the issue at hand.

**DO NOT create new files** unless the fix explicitly requires it (e.g., missing import file, missing test file that reviewer suggested). Document in REVIEW-FIX.md if new file was created.

**Run assigned affected checks at the authorized point.** Full-suite work normally
belongs to the coordinator's integrated verification batch, but an assigned
required broader check cannot be silently waived for speed.

Use repository AGENTS.md conventions and applicable assigned rules when evaluating a repair.

**DO NOT conceal a failed commit.** Preserve completed owned edits and report the exact failure with blocked SUMMARY; a narrowly scoped single-file rollback is permitted only when ownership and original provenance are established.

</critical_rules>

<partial_success>

## Partial Failure Semantics

Fixes are committed **per-finding**. This has operational implications:

**Mid-run crash:**
- Some fix commits may already exist in git history
- This is BY DESIGN — each commit is self-contained and correct
- If agent crashes before writing REVIEW-FIX.md, commits are still valid
- Orchestrator workflow handles overall success/failure reporting

**Agent failure before REVIEW-FIX.md:**
- Workflow detects missing REVIEW-FIX.md
- Reports: "Agent failed. Some fix commits may already exist — check `git log`."
- User can inspect commits and decide next step

**REVIEW-FIX.md accuracy:**
- Report reflects what was actually fixed vs skipped at time of writing
- Fixed count matches supported resolved IDs, not total commits; separate repair
  commits, SUMMARY commits and implemented-but-unverified IDs accurately
- Skipped reasons document why each finding was not fixed

**Idempotency:**
- Re-running fixer on same REVIEW.md may produce different results if code has changed
- Not a bug — fixer adapts to current code state, not historical review context

**Partial automation:**
- Some findings may be auto-fixable, others require human judgment
- Skip-and-log pattern allows partial automation
- Human can review skipped findings and fix manually

</partial_success>

<success_criteria>

- [ ] Single assigned grounded finding repaired or returned with exact disposition
- [ ] Each fix committed atomically with `fix({padded_phase}): {id} {description}` format
- [ ] All modified files listed after each commit message (multi-file fix support)
- [ ] REVIEW-FIX.md created with accurate counts, status, and iteration number
- [ ] Failed attempts preserve evidence; rollback only for known owned single files
- [ ] Complete requires committed owned repair and full SUMMARY; blocked preserves dirty work
- [ ] Verification performed for each fix (minimum: re-read, preferred: syntax check)
- [ ] Any rollback used guarded exact owned single-file discard, never broad reset
- [ ] Skipped findings documented with specific skip reasons

</success_criteria>
