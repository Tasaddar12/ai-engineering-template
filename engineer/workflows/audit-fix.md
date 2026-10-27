@engineer/references/response-language-directive.md

<purpose>
Autonomous audit-to-fix pipeline. Runs an audit, parses findings, classifies each as
auto-fixable vs manual-only, spawns targeted-fixer agents for fixable issues, runs tests
after each fix, and commits atomically with finding IDs for traceability.
</purpose>

<available_agent_types>
- targeted-fixer — commits one bounded correction in an assigned isolated checkout; debugger supplies read-only root-cause evidence for unknown causes
</available_agent_types>

<process>

<authority>
Only an explicit user `/audit-fix` invocation without --dry-run, or already recorded implementation authority covering these exact corrections, authorizes fixing. `/audit-uat` alone is read-only. No automatic approval, changed acceptance, architecture redesign, scope expansion or human UAT substitution is authorized. Capture actual authority and its scope before dispatch; unresolved locked decisions block only dependent findings. Honor all user execution ordering.
</authority>

<step name="parse-arguments">
Extract flags from the user's invocation:

- `--max N` — maximum findings to fix (default: **5**)
- `--severity high|medium|all` — minimum severity to process (default: **medium**)
- `--dry-run` — classify findings without fixing (shows classification table only)
- `--source <audit>` — which audit to run (default: **audit-uat**)

Require --max to be an integer from 1 through 20; reject malformed/negative/zero values and unknown flags. Validate severity and `--source` against the listed enums. Validate `--source` is a supported audit. Currently supported:
- `audit-uat`

If `--source` is not supported, stop with an error:
```
Error: Unsupported audit source "{source}". Supported sources: audit-uat
```
</step>

<step name="run-audit">
Invoke the source audit command and capture output.

For `audit-uat` source:
Read and execute engineer/workflows/_runtime-launcher.snippet.sh. Run `engineer_run query audit-uat` without swallowing stderr or replacing failure with an empty object. Parse its actual `{items,count}` contract. Apply the entire audit-uat workflow's read-only inventory, archived/quick coverage, parse-gap reporting and historical resolution reconciliation; unavailable/failed audit input blocks fixing rather than manufacturing an all-clear.

Read existing UAT and verification files to extract findings:
- Glob: `.planning/phases/*/*-UAT.md`
- Glob: `.planning/phases/*/*-VERIFICATION.md`

Parse each finding into a structured record:
- **ID** — retain source path, scope identity and stable UAT/gap ID; F-01/F-02 may be display aliases only, never new identities on rerun
- **description** — concise summary of the issue
- **severity** — high, medium, or low
- **file_refs** — specific file paths referenced in the finding
</step>

<step name="classify-findings">
For each finding, classify as one of:

- **auto-fixable** — clear code change, specific file referenced, testable fix
- **manual-only** — requires design decisions, ambiguous scope, architectural changes, user input needed
- **skip** — severity below the `--severity` threshold

**Classification heuristics** (err on manual-only when uncertain):

Auto-fixable signals:
- References a specific file path + line number
- Describes a missing test or assertion
- Missing export, wrong import path, typo in identifier
- Clear single-file change with obvious expected behavior

Manual-only signals:
- Uses words like "consider", "evaluate", "design", "rethink"
- Requires new architecture or API changes
- Ambiguous scope or multiple valid approaches
- Requires user input or design decisions
- Cross-cutting concerns affecting multiple subsystems
- Performance or scalability issues without clear fix

**When uncertain, always classify as manual-only.** A path/line hint does not authorize a fix. Auto-fixable requires actual authority, unchanged locked acceptance, a grounded cause, exact bounded paths and a reproducible expected property. Human acceptance, missing credentials/devices or changes to a locked decision remain manual-only. A stale-looking requirement cannot be auto-deleted or marked accepted. Preserve parse gaps as unresolved input findings; do not run product repairs from malformed evidence.
</step>

<step name="present-classification">
Display the classification table:

```
## Audit-Fix Classification

| # | Finding | Severity | Classification | Reason |
|---|---------|----------|---------------|--------|
| F-01 | Missing export in index.ts | high | auto-fixable | Specific file, clear fix |
| F-02 | No error handling in payment flow | high | manual-only | Requires design decisions |
| F-03 | Test stub with 0 assertions | medium | auto-fixable | Clear test gap |
```

If `--dry-run` was specified, **stop here and exit**. The classification table is the
final output — do not proceed to fixing.
</step>

<step name="open_session">
After classification/dry-run, reuse the matching owned quick session or call `engineer_run query session.open quick "audit-fix-${SLUG}"`. Enter the returned absolute isolated worktree; retain root/branch/base/session/caller identity. Create `engineer_run query quick.create "${DESCRIPTION}"` in that session, use its real returned id/directory, and author a bounded QUICK/PLAN through the complete templates. Do not invent a phase for quick work. Record source finding IDs, fixed acceptance, exact owned paths/check argv/issue_refs and separate human obligations. No write occurs during an active frozen batch; join every reader/check first.
</step>

<step name="fix-loop">
Process at most --max auto-fixable findings sequentially, highest severity first with stable-ID ordering within severity. Each finding has one initial attempt and at most two revised attempts (three total); change the hypothesis/input before retrying. The first failed integrated check stops the pipeline. Never broaden the correction to consume ambiguous work.

```bash
FIXER_MODEL=$(engineer_run query resolve-model targeted-fixer --raw)
FIXER_EFFORT=$(engineer_run query resolve-effort targeted-fixer --raw)
engineer_run query dispatch-isolation --phase "quick-${QUICK_ID}" --plan "${PLAN_ID}"
```

Require successful resolution. Omit inherit model/effort parameters; pass all other actual values inline. Load the complete targeted-fixer role and bounded-correction-dispatch reference. Use the returned mandatory worktree mode. Under orchestrator-worktree call `worktree.create PLAN --phase quick-ID --base SHA --files PATH...` with real exact paths. Under harness-worktree dispatch native isolation="worktree", validate base and record actual path/branch via worktree.record-agent with the same scope. Refuse missing isolation or mismatched root/branch/base; never fall back to shared edits.

```text
Agent(
  subagent_type="targeted-fixer",
  model=<actual FIXER_MODEL; omit inherit>,
  effort=<actual FIXER_EFFORT; omit inherit>,
  prompt="<assignment>absolute isolated root, branch, full expected base, real quick PLAN/SUMMARY paths, exact files/deletions/resources and actual authority</assignment><finding>stable source ID, source report path/revision, cited cause, unchanged required property and exact pass/fail expectations</finding><required_reading>complete PLAN/QUICK, source report, approved CONTEXT/SPEC, relevant implementation/test files, full SUMMARY template and bounded correction method</required_reading><checks>exact argv/cwd/timeouts and user test order</checks><constraints>Minimal scoped repair, no refactors or acceptance edits, no shared records/publication/children; commit owned repair and schema-valid SUMMARY. Return actual commands and pending evidence, root/base/head, hashes and Remaining.</constraints>"
)
```

Wait for confirmed completion/stop; a timeout is not exit. Inspect the committed correction and SUMMARY, owned diff/deletions, finding IDs and actual focused evidence. A failed/blocked worker remains unmerged with its branch/checkout and evidence preserved. Never checkout/reset paths or delete evidence to recover. A user-deferred check remains pending; do not claim fixed or bypass the complete-summary integration gate.

Integrate only a valid committed complete worker through `engineer_run query worktree.merge-wave --phase "quick-${QUICK_ID}"`. Then run `engineer_run query verification.run-checks` on the integrated revision when execution is allowed. The configured argv/timeouts and current input-bound receipts are authoritative: no sniffed runner, shell-string normalizer, successful empty fallback or hidden timeout. Require nonempty configured coverage of the repaired property and applicable regressions; absent coverage is pending, not green. Preserve IDs/revision/input fingerprint/exit/timeout/output tails.

A passing integrated run confirms this technical correction, not human acceptance. If integrated checks fail, stop further findings, retain the integrated commit and diagnostic evidence, and route one bounded corrective continuation under the same authority before a fresh verification batch. A blocked branch is preserved unmerged; an already integrated failure is never mislabeled reverted. Continue no other fix until that failure is resolved. Do not rewrite published/source history or weaken the test to obtain pass.

Worker commits include the stable finding ID and exact owned paths plus SUMMARY. The coordinator owns record updates, tracking and integration; it does not restage worker files or create a second fix commit on their behalf.
</step>

<step name="report">
Present the final summary:

```
## Audit-Fix Complete

**Source:** {audit_command}
**Findings:** {total} total, {auto} auto-fixable, {manual} manual-only
**Fixed:** {fixed_count}/{auto} auto-fixable findings
**Failed:** {failed_count} (preserved with evidence; integrated status explicit)

| # | Finding | Status | Commit |
|---|---------|--------|--------|
| F-01 | Missing export | Fixed | abc1234 |
| F-03 | Test stub | Fix failed / preserved unmerged or integrated | {actual SHA} |

### Manual-only findings (require developer attention):
- F-02: No error handling in payment flow — requires design decisions
```
List each manual-only finding with its actual missing fact/decision, feasible options and a recommendation, plus owner, existing canonical URL/Pending and the first next action. Preserve historical observations and actual Human acceptance; no automatic accepted status. Route within-scope bugs and UAT through the complete canonical git-workflow issue template, matching, preview token and provider readback procedure; no duplicate tracker or issue closure bypass.

Use `engineer_run query quick.update "${QUICK_ID}" --status "${ACTUAL_STATUS}" --commit "${ACTUAL_SHA}"` for actual tracked work; leave pending evidence nonterminal. Record continuity through state.record-session. Follow quick.md's complete deliver_session procedure for the same quick/session lineage, canonical draft PR tracking and authorized delivery limits. Do not mark ready without independent current verification and required human acceptance; merge only on the human's instruction. Return stable findings, preserved hashes/worktrees, actual checks/pending evidence, remaining decisions and session/caller identity.
</step>

</process>

<success_criteria>
- Auto-fixable findings processed sequentially until --max reached or a test failure stops the pipeline
- Integrated corrections require actual passing configured receipts before technical fixed status; deferred executions remain pending
- Failed work is preserved with exact committed/dirty paths and unmerged/integrated status; no destructive recovery
- Pipeline stops after the first test failure (no cascading fixes)
- Every commit message contains the finding ID
- Manual-only findings are surfaced for developer attention
- --dry-run produces a useful standalone classification table
</success_criteria>
