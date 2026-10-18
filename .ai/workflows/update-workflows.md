<!-- workflow
step: update-workflows
agent-roles: orchestrator, scout, coder, code-reviewer, verifier, doc-verifier
produces: reviewed update plan, installed workflow diff and verification evidence
consumes: installed ownership manifest, pinned upstream payload, project config
-->

<purpose>
Update an already installed .codex or .claude workflow through explicit bounded
roles. The coordinator routes and integrates evidence; source-changing work stays
with coder. A report request runs comparison only. An update implementation request
covers the stated target; preserve existing delivery authorization and exclusions.
Do not create adoption/phase records for template maintenance unless requested.
</purpose>

<required_reading>
Read AGENTS.md, RULES.md, the selected role and
[scout dispatch](../references/scout-dispatch.md). Identify the installed host root
and use its runtime, never a sibling checkout or personal configuration.
</required_reading>

<dispatch>
1. **Coordinator: pin scope.** Capture absolute Git root, branch, HEAD, source,
   requested ref, installed host and allowed paths. Use the existing runtime's
   `query runtime-identity`, `query config-get workflow.isolation` and
   `query config-get verification.commands` APIs to inspect current configuration.
   Resolve every spawned role using `query resolve-agent <name> --host <host>`;
   pass the returned model and effort inline, omitting `inherit`. The Codex scout
   resolves to `gpt-6-luna`/`high`; never substitute a generic worker. Config changes
   outside the deterministic updater use `query config-set <dotted-key> <value>`
   only for an explicitly authorized decision. Upstream examples cannot supply one.

2. **Coordinator: capture comparison, then spawn scout.** Run the deterministic
   installed updater on the pinned scope and capture its output and saved plan:
   `python .codex/update.py --target . --source <repository> --ref <ref> --plan <outside-workflow-plan.json>`.
   It fetches to a temporary directory and resolves the ref to a commit. No target
   mutation occurs. `--no-hooks` preserves existing hooks and skips new registration;
   Set `--from-ref <commit>` to compare current files with a prior content
   baseline. The ref does not establish ownership. Give scout the captured
   plan/log input ids, exact root/revision and a complete specialized
   `scout_assignment` with task_class `FACT_EXTRACTION`,
   question "Which supplied update candidates and classifications require review?",
   requested_fields: ownership/provenance, candidate diffs, config required/optional
   defaults/conflicts, generated hook/entry conflicts, project preservation and
   unresolved ownership. Bound search_scope and allowed_evidence to the supplied
   plan/log and named ownership/config files; require cited `field_results` for each
   field. Scout reads and classifies this supplied evidence; it never executes the
   updater, project code or tests. Coordinator joins and validates its structured
   packet before assigning implementation. Do not repeat known-source discovery.

3. **Spawn coder only for authorized implementation.** Give the pinned candidate
   revision, root/branch guards, exact allowed files, saved plan and scout packet.
   Coder loads installer APIs through `update.py`, reviews every content diff and
   records necessary decisions in the plan's `resolutions` mapping. For a customized
   or unproven file, a reviewed entry is
   `{"action":"keep","classification":"customized"}` or
   `{"action":"write","classification":"upstream-managed"}`. Use `project`
   for project additions. Files retired upstream may be kept or explicitly removed;
   there is no blanket prune. Legitimate custom logic needing a merge is reconciled
   in a bounded coder change and replanned; the updater never guesses a merge.
   A generated settings/block conflict must be reconciled or kept, then replanned.
   Do not relabel generated/project files to bypass protection. A missing manifest
   is unproven ownership even when content matches; reviewed classification makes
   an upgrade possible without claiming unknown files automatically.

4. **Spawn independent code-reviewer before apply.** Give the frozen root/HEAD,
   pinned source revision, full candidate plan with resolutions and owned path list.
   Require review of preservation, ownership, hook trust boundaries, hash guards,
   config behavior and actual diffs. Wait for its report; return bounded repairs to
   coder and obtain a new review when the candidate changes. For report-only scope,
   return scout/reviewer findings without an apply assignment.

5. **Coder: guarded apply and slice commit.** Hash the complete reviewed plan bytes
   with SHA256 and run
   `python .codex/update.py --apply <plan.json> --reviewed-plan-sha256 <digest>`.
   Apply fetches the recorded commit rather than a moving ref, regenerates candidates
   and compares every target fingerprint. It rejects stale plans/unresolved conflicts
   before writes, verifies backups under .workflow-backups, records current/previous
   provenance, and validates installed hashes and configuration syntax. It neither
   installs dependencies nor runs upstream executables. Coder runs assigned applicable
   tests, includes its evidence SUMMARY and commits the exact slice on the assigned
   branch. Coordinator owns push/draft PR and integration under existing authorization.

6. **Spawn named verification only for needed claims.** Assign verifier the exact
   installed revision, runtime-identity/status and the project's actual configured
   checks (`query verification.run-checks`); require results for runtime/config
   compatibility and preserved files. Run needed independent code-reviewer checks
   against the installed diff. Spawn doc-verifier only when changed installed docs
   have claims requiring independent checks. Wait for all assigned reports before
   accepting the update. Host hook registration is not evidence of trusted live
   hook execution; preserve host/project trust and report checks actually run.
</dispatch>

<configuration_contract>
The updater reads the pinned runtime's literal `DEFAULTS` using AST; it does not
execute source code. Its bounded required migration fields are `workflow.isolation`,
`worktree.root`, `handoff.context_percent`, `handoff.context_tokens` and
`verification.commands`: these operational safety settings are filled only when
missing, with the pinned runtime defaults, including missing nested mappings.
The runtime can also supply fallback defaults; this update materializes only the
listed safety fields. Other missing runtime defaults and template-only example
settings are separately reported as optional and are never automatically adopted.
Existing recognized leaf types, isolation/merge enums and handoff limits are
checked; invalid values are conflicts and remain untouched. Valid project values,
models, check commands, language and hooks remain authoritative. Adding required
YAML fields uses the runtime's safe-load/safe-dump style and may reformat comments;
review the actual diff. An unchanged config remains byte-for-byte unchanged.
</configuration_contract>

<comparison_contract>
Saved review schema 2 separates content comparison from ownership and action.
Each entry's `comparison` describes installed bytes versus the rendered upstream
payload, before project preservation, generated-file merging or config migration.
Its `candidate_comparison` describes installed bytes versus the effective candidate
after those operations. For example, protected PROJECT content can be substantive
versus upstream while its preserved effective candidate is unchanged. Ownership,
project preservation and conflict reasons remain separately visible.

The categories are `unchanged` for exact bytes (including identical binary bytes),
`line-ending-only`, `substantive`, `added` for a missing current file and `retired`
for a missing upstream candidate. Two absent values are unchanged; a missing file
is distinct from an empty file. A retired comparison also describes project-only
additions absent upstream: it does not establish that upstream ever owned them.

Line-ending-only requires two distinct strict UTF-8 byte strings with no NUL and
no bare CR, equal after replacing CRLF pairs with LF. Mixed LF/CRLF pairs qualify.
Invalid UTF-8, NUL-bearing data and lone-CR differences are substantive. Whitespace,
BOM and terminal-newline changes remain substantive; comparison never trims,
removes BOMs, decodes with replacement or normalizes other newline characters.
CLI output labels comparison alongside ownership/action and omits equivalent
newline diffs while retaining substantive candidate diffs. The updater reports
these differences and retains its equivalent-workflow skip.

Line-ending-only is information, never write or deletion authority. It cannot prove
ownership, reclassify a customized/generated/project file, clear a conflict or
prune a retired file. Review every existing classification and required resolution.

Candidate base64, candidate/installed/upstream/manifest hashes and the complete
reviewed-plan SHA256 use exact bytes. The plan also fingerprints raw tracked source
and baseline inputs because rendering can normalize source text. Apply regenerates
the full plan and rechecks target, manifest, source and baseline bytes after backup
before writes. A changed input byte, even CRLF-only, requires replan and review;
an older schema requires regeneration. Any saved JSON edit, including line endings,
comparison, candidate or resolutions, invalidates the prior reviewed digest. Review
valid resolutions or formatting edits and hash the complete file again. Manually
edited comparison/candidate metadata still fails full regeneration; generate a new
plan rather than treating a new digest as permission to change generated content.
After apply updates ownership, reuse of the original plan is stale. Generate and
review a fresh pinned plan and hash its complete bytes for a no-op apply.

Shell files and nginx.conf/nginx.conf.template basenames have explicit LF Git
attributes at every depth. This checkout policy does not authorize normalization
of authored records or backups. Apply writes the exact reviewed candidate bytes
and verifies their installed hashes; it never silently normalizes during writing.
</comparison_contract>

<output>
Return pinned current/previous upstream provenance, reviewed classifications,
changed/preserved files, unresolved conflicts/optional defaults, exact checks and
results, commit/draft PR if authorized, and any limitations. The ownership manifest
is .codex/workflow-ownership.json (or .claude equivalent), separate from migration
backup MANIFEST.json. Actual content hashes govern comparison; a version stamp
never suppresses differences. User code, plans, unrelated files and personal host
configuration are outside update ownership. No merge or product installation is
part of this workflow.
</output>
