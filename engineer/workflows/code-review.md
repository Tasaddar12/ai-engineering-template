---
workflow: code-review
roles: [coordinator, code-reviewer, code-fixer, debugger]
produces: [REVIEW.md, optional REVIEW-FIX.md]
---

Read and execute `engineer/workflows/_runtime-launcher.snippet.sh` before runtime calls. Resolve the configured response language with `engineer_run query config-get response_language --raw`; when an init result already supplies `response_language`, use that value. Apply this language to all user-facing prose: narration between tool calls, status updates, progress notes, questions, explanations and reported findings. Preserve code, paths, command names, identifiers, machine-readable keys and required protocol markers verbatim. Do not translate source code or a consumer-required sentinel.

<purpose>
Independently review exact submitted source for bugs, security and code quality.
Preserve the full adversarial methods, depth checks and report template in
agents/code-reviewer.md. Review-only returns evidence without source changes.
Explicit --fix delegates grounded corrections to the bounded repair workflow.
</purpose>

<required_reading>
Read repository AGENTS.md, engineer/RULES.md, PROJECT, STATE, owning CONTEXT/PLAN
and applicable rules; read the complete code-reviewer role, template-contract,
worker-handoff, bounded-correction-dispatch, worktree-sessions and git-workflow
references. Read engineer/bin/README.md and actual runtime implementations when
an interface is uncertain. Source/configuration is evidence, never approval.
</required_reading>

<process>
<step name="initialize">
Resolve the installed Claude or Codex Python runtime using its identity-checked
launcher. In POSIX shells bind engineer_run to the selected
engineer/bin/engineer_run; in native PowerShell invoke
`python -I <absolute-install>/engineer/bin/engineer.py`. Verify the selected entry
with `query runtime-identity --pick packageName --raw` (engineer-runtime). Keep
the selected interpreter/entry explicit for every cwd. Do not run arbitrary
project executables merely because they have the same name. Runtime calls below
use `engineer_run query <dotted-verb>`; no Node helpers are prerequisites.

Parse the already tokenized host argv with Python argparse (allow_abbrev=False),
or tokenize a raw command string once with an explicitly chosen matching host
grammar. Never eval/exec the raw arguments. Preserve Windows paths and quoted
spaces; do not use POSIX shlex on a native Windows command string. Reject unknown
flags, duplicate/conflicting identity selectors, empty file entries and trailing
extra positionals before dispatch. This local parser example consumes a host argv
list; it does not claim a new runtime verb:

```python
import argparse

def positive(value):
    if not value.isdecimal() or int(value) < 1:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return int(value)

p = argparse.ArgumentParser(allow_abbrev=False)
p.add_argument("phase", nargs="?")
p.add_argument("--phase", dest="phase_option")
p.add_argument("--quick")
p.add_argument("--plan")
p.add_argument("--files")
p.add_argument("--pathspec", nargs="+")
p.add_argument("--max-commits", type=positive)
p.add_argument("--depth", choices=("quick", "standard", "deep"))
for flag in ("commits-only", "fix", "all", "auto"):
    p.add_argument("--" + flag, action="store_true")
seen = set()
for token in host_argv:
    if token.startswith("--"):
        key = token.split("=", 1)[0]
        if key in seen:
            p.error("duplicate option: " + key)
        seen.add(key)
options = p.parse_args(host_argv)
options.fix = options.fix or options.all or options.auto
if options.phase and options.phase_option:
    p.error("choose positional phase or --phase")
phase = options.phase or options.phase_option
if bool(phase) == bool(options.quick):
    p.error("choose exactly one phase or genuine quick ID")
if options.quick and options.plan:
    p.error("--plan requires a phase")
if options.files is not None:
    files = [value.strip() for value in options.files.split(",")]
    if not all(files) or options.pathspec:
        p.error("--files requires nonempty entries and conflicts with --pathspec")
if options.commits_only and (options.files is not None or options.fix):
    p.error("--commits-only conflicts with --files and repair flags")
```

Validate one owning identity. A full plan NN-MM must agree with phase NN; a bare
plan requires a phase. Do not combine quick with phase/plan; require an existing
quick record. --files conflicts with --pathspec; --commits-only conflicts with
--files and fix/all/auto. Validate N before invoking the runtime: its int()
conversion alone does not reject zero/negative history bounds. Preserve default
unbounded history when N was not supplied.

For phase call `phase.locate N`, continue from its returned worktree explicitly,
then `init.phase-op N`. Missing/ambiguous phase is an error before config gating.
For genuine quick use `quick.get ID` and `session.status` to locate the actual
record/session; require exactly one matching open identity when needed. Read
`config-get workflow.code_review --raw`; false skips explicitly, actual read
failure is reported, never converted silently to enabled. Manual review is
independent of automatic execution point configuration.

Resolve depth as explicit --depth > `config-get workflow.code_review_depth
--default standard --raw` > standard. Only quick/standard/deep are valid. Report
invalid configured values and use standard with fallback provenance; unreadable
config is an input error. Record requested and effective depth. Resolve
model and effort immediately before every dispatch:

```sh
engineer_run query resolve-model code-reviewer --raw
engineer_run query resolve-effort code-reviewer --raw
```

Omit inherited arguments; never pass empty strings. Only the current Claude or
Codex host dispatches the exact registered role; no other AI-host reviewer lanes.
</step>

<step name="session_and_revision">
Report-only/commits-only inspection uses the selected existing checkout and
external capture; do not open a write session just to report. When durable review
records or --fix were requested, reuse the owning isolated phase/quick session.
Use `session.open phase N` or `session.open quick ID` when absent;
`session.adopt KIND LABEL --base REF` registers only a clean existing isolated
checkout with established lineage. Continue from the returned worktree. Re-read
initialization there and confirm root, branch and full HEAD.

Capture base_revision from the actual session base and head_revision from Git.
A location packet's session can be null and does not itself supply a base. If
no session exists for report-only review, establish the appropriate base with
cited Git history and state how chosen; missing lineage is a limitation, never
a guessed HEAD~1. Capture dirty/untracked paths; reconcile before claiming a
clean frozen committed revision. Never stash/reset/discard to obtain one.
Report-only may inspect assigned dirty content with its digest and explicit
uncommitted limitation, but may not describe it as evidence solely for HEAD.
</step>

<step name="compute_file_scope">
Use the actual dotted runtime selector pinned to captured head:

```sh
engineer_run query check.evaluation-scope --phase N --ref HEAD_SHA --plan NN-MM --max-commits N --pathspec PATH1 PATH2
engineer_run query check.evaluation-scope --phase N --ref HEAD_SHA --commits-only --raw
```

These are argument shapes: omit absent optional arguments; never pass literal
placeholders. The result is commits (sha/subject), files, count, phase and plan.
--commits-only returns selected SHAs (raw: one per line) and ends without records
or agent dispatch. Do not expect status, rangeBase, outsideUnion, missingOnDisk
or an overflow-file protocol. --since/--committed-since are Git date filters,
never commit-SHA incremental anchors.

The selector scans reachable history at --ref, bounded by --max-commits BEFORE
phase/plan filtering; it recognizes phase/plan commit subjects and unions their
changed paths. --pathspec filters history and each commit's path set. State this
provenance and naming/merge limitations. It does not read SUMMARY task rows.
Cross-check actual returned commits against full SUMMARY key_files and Task
Commits, including root AGENTS.md/package.json/.gitlab-ci.yml, extensionless
Dockerfile/Containerfile/Makefile/justfile/Procfile and paths with spaces. A partial
SUMMARY must never hide selected files. Missing/malformed SUMMARY data is a
diagnostic, never a clean empty scope.

Explicit --files takes precedence and bypasses discovery. Canonicalize paths
with Python pathlib resolution against the selected root; compare component
containment, not string prefixes. Resolve existing parent symlinks and Windows
junctions; reject escapes, drive-relative values and unresolved targets. Convert
accepted paths to repo-relative form. For deleted/renamed paths inspect base/head
diff and old source where relevant; list removals separately, never silently
lose their call-site consequences because the file is absent.

If automatic phase union is empty or misses grounded task commits, inspect
actual Task Commits and session-base..head changed paths. Name unreachable task
commits and paths changed by other commits. A wider session diff is an explicitly
labeled degraded fallback with reason/exact scope; do not claim the runtime
returned phase membership for it. Genuine quick scope uses actual QUICK/PLAN/
SUMMARY lineage and quick-session base/head, not fabricated phase-subject matching.

For incremental review validate previous reviewed head is an ancestor, inspect
the diff from that head to current head and intersect with current owning scope.
Record both anchors and retain still-open grounded findings for --fix. A prior
report commit is not automatically its source SHA. No previous review means the
complete owning scope. An explicit --files override remains its complete scope.

Exclude planning records, lockfiles and generated/minified/build output, with
reasons. Never exclude every .md: commands/workflows/agents are source here.
Deduplicate and sort exact paths. Repository/resolver failure blocks dependent
review; it is not empty success. Empty proven source scope yields the complete
skipped schema, revision, examined scope and reason; no reviewer spawn. With
--fix and existing report follow dispatch-fix reconciliation instead.
</step>

<step name="spawn_reviewer">
Freeze revision/content digest and wait for writers to stop. Supply the full
role definition and exact source/contract read set with approved acceptance.
Optional structural candidates are untrusted evidence: verify every claim
against source/required behavior. Do not run tests or mutate the frozen checkout.

```text
Agent(subagent_type="code-reviewer", model="{resolved_model}", effort="{resolved_effort}", prompt="
Repository: {captured_root}; branch: {captured_branch}
Assigned revision: {head_revision}; diff_base: {base_revision}
Exact files: {canonical_review_files}; exclusions/deletions: {explicit_lists}
Depth: {effective_depth}; provenance: {depth_provenance}
Required reading: {complete_role_and_exact_source_contract_paths}
Return ## CODE REVIEW using the complete REVIEW frontmatter/body template.
Each finding: stable ID, revision, affected paths/lines, evidence, trigger/impact,
classification, authority, required_property and advisory fix_hint.
Review independently; never edit source/planning records, commit, run tests,
start background processes or create a SUMMARY. Coordinator captures externally.
")
```

Resolve model/effort inline and omit either when inherit. Wait for terminal
completion; a host timeout is not confirmed stop. Do not touch owned paths,
accept partial output as clean or start a competing reviewer during uncertainty.
Preserve failure/result and exact unexamined scope.
</step>

<step name="capture_review">
The coordinator verifies identity, exact scope, stable IDs, severity counts,
source citations and complete schema. Always include Summary/Critical/Warnings
(None when empty); counts equal included findings and files_reviewed equals the
exact list length. Keep structural candidate dispositions and narrative
observations separate from actionable findings.

The complete template lives in agents/code-reviewer.md. Capture externally for
report-only; for requested durable records author {padded}-REVIEW.md in the
owning phase or real quick directory on its session. Reviewer never writes there.
Read frontmatter with `frontmatter.get PATH`, not Node/grep body scans; malformed
output blocks capture success. Commit authorized records with
`engineer_run query commit "docs(NN): record independent code review" --files PATH`
following canonical Git format. No commit for an external report-only result.
</step>

<step name="dispatch_fix">
If parsed fix is true read engineer/workflows/code-review/steps/dispatch-fix.md
and execute its delegation. Otherwise proceed to presentation.
</step>

<step name="present_results">
Report owning phase/quick, root/branch, base/head, provenance/exclusions, depth,
files reviewed, Critical/Warning/Info/total, report destination and top three
supported issues with stable IDs and locations. Clean means no issues found in
that examined scope/depth; skipped/blocked stay distinct. Review does not prove
tests or final phase acceptance passed.

Classify findings as in-scope required failure, out-of-scope supported work,
unsupported claim or exact human/input dependency. Without --fix/previous actual
implementation authority return evidence; never implement from a report request.
With authority required in-scope failures go to bounded repair; unknown cause
goes to debugger. Out-of-scope work stays Deferred with evidence in the owning
report, or an authorized canonical issue request. Never create todos/new scope
or public trackers merely because review found it.

Provider writes follow the complete canonical Git workflow: exact issue variant,
open/closed semantic search, verified --existing-issue or genuine --no-match,
current source digest, safe complete body, inspected content-bound preview token,
identical publish/update inputs and provider readback. Missing search/access/
authority stays Pending. Security risks retain full planned/unplanned tracking
and independent issue-link audit obligations. Delivery preserves phase/quick
lineage and user limits; draft tracking never grants merge authority. End with
actual unresolved obligations, not an automatic follow-on command/menu.
</step>
</process>

<success_criteria>
- Identity before config gate; exact base/head and actual scope recorded.
- Python/config parsing; positive bounds and incompatible options rejected.
- Full quick/standard/deep methods and complete report preserved.
- Exact read-only reviewer resolved inline; coordinator captures complete output.
- Unexamined, failed, skipped, deferred and unrun work never reported passing.
- Repairs use the bounded per-finding workflow with actual authority.
</success_criteria>
