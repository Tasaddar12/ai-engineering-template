<!-- workflow: clean-planning; roles: scout, executor, doc-verifier -->
<purpose>
Review planning records against current templates and evidence, repair safe structural drift through runtime guards, and archive only explicitly selected retired records. Preserve the adopting project's intent and history.
</purpose>
<required_reading>
@engineer/RULES.md
@engineer/truth-map.md
@engineer/references/scout-dispatch.md
@engineer/references/template-contract.md
@engineer/templates/phase-prompt.md
@engineer/templates/summary.md
@engineer/templates/context.md
@engineer/templates/verification-report.md
</required_reading>
<process>
<step name="resolve_scope">
Resolve the repository and current engineer source namespace. Read the user-selected paths and current planning state without inventing an adopting-project identity. Load the relevant artifact template in full, including its frontmatter, examples and runtime-owned section contract. Optional decision rationale may reference a linked ADR; PROJECT.md Key Decisions remains the decision owner. Do not create an ADR just to satisfy a missing link.

Separate requested structural repair from narrative edits, changed acceptance, missing evidence, and selected archival. A review request alone does not authorize retirement or scope changes. Keep all project narrative and requirement wording unless an actual source-backed correction is within scope.
</step>
<step name="review_records">
Read and execute `engineer/workflows/_runtime-launcher.snippet.sh`. Run `engineer_run query planning.review` for the selected scope using the runtime's supported path selection. Save its full returned findings and expected digest; do not shorten the finding packet. Each finding needs its owning record, violated template field, current evidence and proposed outcome. Use `engineer_run query planning.validate` for warn-only record-health reporting; warnings never invent implementation work or stall unrelated authorized work.
</step>
<step name="collect_evidence">
When source location is unknown, dispatch a single read-only scout with inline resolved model/effort and an exact evidence output. Give selected records, their complete templates, the relevant runtime contract and authoritative source revision. Require cited evidence and distinguish structural drift from missing implementation proof. The scout may not change shared records, invent acceptance, infer a passed test from prose, or dispatch children. Wait for the packet before touching assigned paths.
</step>
<step name="classify_repairs">
For each finding, identify the owning runtime verb or narrative owner. Safe repairs preserve approved meaning: missing structural sections, normalized supported frontmatter, stale paths with an established current owner, and runtime-owned section alignment. Do not fabricate outcomes, decisions, requirements, summary claims, UAT replies, check receipts, execution authorization or verification. Route uncertain semantics to a concrete decision and leave that finding blocked while independent safe repairs continue.
</step>
<step name="guarded_repair">
Show the full repair preview and captured expected digest. Apply safe approved structural changes only through `engineer_run query planning.repair --apply --expect "${EXPECTED_DIGEST}"` with the exact reviewed scope. Re-read the result; stale evidence requires a new review, never an overwritten digest. Use the dedicated state, roadmap, requirement or todo verbs for their runtime-owned fields. Hand-edit only narrative prose the runtime does not own, preserving all retained methods and project wording. Commit the exact changed records with a meaningful description and explain any remaining semantic finding.
</step>
<step name="selected_archival">
Archive only records explicitly selected by the user after establishing that each is retired and its evidence/history remains recoverable. Preview with `engineer_run query planning.archive --paths "${RECORD_PATH}" ...`. Retain its digest and complete entries. Show the concrete source and archive destinations before a destructive operation. Apply that exact selection with `engineer_run query planning.archive --paths "${RECORD_PATH}" ... --expect "${ARCHIVE_DIGEST}" --confirm` only after authorization covers those exact records. A milestone-wide archive request does not imply approval to retire arbitrary records. Do not archive all old records by age, overwrite archives, renumber phases, strike through entries, or mark them Closed in place. Worktree/branch cleanup is a separate exact-snapshot workflow.
</step>
<step name="review_result">
Re-run planning review only when the user permits checks and when changed records require it. Dispatch `doc-verifier` read-only with inline model/effort when independent documentation verification is required. Keep structural validity separate from evidence that the phase goal shipped. On deferred checks, report the pending review and do not claim repaired records passed validation.
</step>
<step name="report">
Report reviewed paths, safe repairs applied, explicit archival source/destination pairs, commits, preserved semantic questions, and check results or pending checks. Keep the complete planning evidence available; do not replace records with condensed versions.
</step>
</process>
<anti_patterns>
Never reconstruct project intent from a template, hand-edit runtime sections, fabricate evidence, retire unspecified records, or turn warn-only validation into an implementation blocker.
</anti_patterns>
