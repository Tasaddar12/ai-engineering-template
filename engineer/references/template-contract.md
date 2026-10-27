# Planning record and template contract

This document owns record integrity and producer/consumer boundaries. The complete [artifact registry](../templates/README.md) and individual templates own complete authoring shapes, methods and examples; this contract does not replace them. Read the [runtime API](../bin/README.md) for supported argv and returned fields.

## Planning-record integrity

Structured records are current execution data, not examples. Preserve exact identity, types and cross-record ownership. Runtime operations own phase numbering, ROADMAP structures, STATE structures, PROJECT Key Decisions, REQUIREMENTS traceability, todos, quick tasks, milestones, sessions and archive manifests. Author narrative in its own section; do not hand-edit runtime-owned tables or reconstruct them from guesses.

Every runtime invocation captures planning-file digests and schema findings before and after dispatch. A read-only verb that changes planning content fails. A mutation that introduces new schema corruption fails; pre-existing corruption is reported so repair remains possible. Atomic writes and a planning lock reduce concurrent corruption; they do not prove the workflow's semantic correctness or replace exclusive ownership.

`planning.integrity` fails for supported malformed records; `planning.validate` reports findings without blocking. Warn-only validation is not permission to ignore missing acceptance or to silently rewrite approved intent. `frontmatter.set` preserves the body and rejects newly introduced schema errors in a recognized record. The parser does not establish user authorization.

## Source templates versus current records

| Concern | Reusable template | Current record |
|---------|-------------------|----------------|
| Identity | Placeholder and fictional example | Actual phase/plan/quick identifier matching its path |
| Required fields | Complete schema and guidance | Every mandatory key with correct type; empty only when semantically valid |
| Evidence | Example format, clearly fictional | Actual revision, command, result and accessible reference |
| Human decision | Pending placeholder | Actual human words/identity/date or explicit Pending |
| Issue link | Placeholder or Pending example | Verified canonical provider reference or concrete Pending reason |
| Scope | Explains boundaries | Approved outcome and exact ownership, no invented additions/deferrals |

Read full templates before creating records. Preserve all required sections; explain not applicable content. Do not substitute compact summaries, omit consumer guidance or copy fictional evidence into current records.

## PLAN

**Path:** `.planning/phases/NN-name/NN-MM-PLAN.md`; quote plan IDs to preserve leading zeros and suffixes.
**Producer:** planner under the approved CONTEXT and roadmap scope.
**Consumers:** checker, executor, coordinator, verifier and runtime plan/task operations.

| Field | Shape | Contract |
|-------|-------|----------|
| phase | string identifier | Matches actual phase directory and roadmap identity |
| plan | quoted string identifier | Matches unique PLAN basename |
| type | string | execute or assigned tdd discipline |
| wave | integer | Declared label; actual groups honor dependencies/overlap |
| depends_on | list of sibling plan IDs | Inter-plan producer/consumer requirements, no self/cycle/invented ID |
| files_modified | exact path list | Complete authorized write ownership |
| files_deleted | exact path list | Explicit deletion authority; undeclared deletion blocks |
| resources | stable identity list | Shared external mutable resources serialize dispatch |
| autonomous | boolean | Does not waive any required human decision |
| requirements | requirement ID list | Approved obligations covered by this plan; quick mode follows its assigned contract |
| acceptance | top-level list | Explicit observable acceptance, including mandatory human judgment |
| documentation | top-level list | Required reader-facing artifacts and evidence, or explicit applicability |
| checks | list of nonempty argv string lists | Exact required checks, no shell strings or fabricated commands |
| issue_refs | top-level list | Canonical source/finding relationships or concrete Pending reasons |
| must_haves | mapping | truths, artifacts and key_links; preserve backstop/prohibition schema when used |
| user_setup | list when applicable | Real unavailable prerequisite, not a request for automatable manual work |

Tasks preserve `name`, `files`, `read_first`, `action`, `verify` and `done`. Actions name exact values and expected behavior. Checkpoint tasks preserve their actual option/resume contract. A tracer is a real thin end-to-end slice; a human-check stops for required human judgment in every mode. A test assignment applies by `type: tdd` / `tdd=true`, not filename or mode alone.

Each PLAN retains its complete six-column threat register: Threat ID, Category, Component, Severity, Disposition, Mitigation Plan. Preserve phase-unique IDs, aliases/occurrences, canonical references and Pending dependencies. See [canonical threat tracking](git-workflow.md#canonical-threat-tracking).

Update PLANs only under the assigned planning/correction ownership. Workers executing code do not rewrite shared plans to declare success. A plan-ready state does not authorize implementation.

## SUMMARY

**Path:** same phase/plan identity, `NN-MM-SUMMARY.md`.
**Producer:** executor after committing the owned slice.
**Consumers:** coordinator, verifier, planning dependency readers and runtime handoff/merge operations.

Required current metadata: phase, plan, status, requirements-completed, acceptance, documentation and issue_refs. The acceptance, documentation and issue_refs values are top-level lists. Record only requirement IDs actually completed by delivered behavior and evidence; never copy every planned ID automatically. Preserve dependency/provided interfaces, key files, relevant decisions and actual metrics when used by consumers.

| Section | Required content |
|---------|------------------|
| Accomplishments | Concrete delivered outcomes |
| Task Commits | Actual owned commit SHAs and descriptions |
| Checks | Tested SHA, exact argv, observed result and evidence |
| TDD Evidence | Actual RED format/classifier/semantic result, GREEN pass and ancestry when assigned |
| Deviations | Smallest in-scope repairs and their evidence; no invented scope |
| Threat Flags / Outcomes | Canonical identities, actual mitigation evidence and distinct lifecycle |
| Remaining / Deferred | Exact unfinished/out-of-scope obligations, impact, owner and first continuation |
| Readiness | What the next consumer can actually rely on; pending human/check gates |

Coverage is per delivered outcome with stable id, description, optional requirement, verification entries and explicit human_judgment; rationale is required when human judgment is true. Each verification entry preserves kind/ref/status from an actual result. Automated classification requires non-empty passing evidence with matching revision/input coverage. It never waives required UAT or final acceptance. Missing/malformed/legacy coverage requires coordinator/verifier classification rather than an automatic pass.

A source-changing worker reports complete only with owned commits and the required full-schema SUMMARY. Artifact-only producers return and commit their assigned artifact without manufacturing a SUMMARY; read-only roles return their assigned packet/report without a completion commit or SUMMARY.

## CONTEXT and discussion log

Current CONTEXT metadata requires phase identity, `discussion` (`pending` or `complete`) and top-level `issue_refs`. `discussion: pending` remains while decisions are unresolved; complete means the actual answers are captured. The body records the approved phase boundary, locked decisions, delegated discretion, open questions and the actual explicit implementation instruction with date/scope/limits. Ready-for-planning text does not supply execution authority.

DISCUSSION-LOG preserves alternatives, actual answers, recommendation checks and rationale incrementally. It supports audit/dispute reconstruction; CONTEXT remains the implementation input. Consequential project decisions are recorded in PROJECT Key Decisions while deciding; an ADR supplies optional linked rationale only.

## Verification report

**Phase path:** `NN-VERIFICATION.md` in its phase directory.
**Producer:** coordinator from joined read-only verifier/reviewer/auditor packets at one frozen revision.
**Consumers:** progress, completion, ready/ship and final currentness gates.

Required identity is phase for phase records or quick for genuine quick records, plus status. Status values are passed, gaps_found or human_needed for completed verification evaluation; pending/not_started does not pass readiness. Preserve verified timestamp, score, covered_files, fingerprint, revision and `covered_digest: "v4:sha256:..."` as the runtime/report contract requires. A digest/fingerprint is content binding, not behavioral proof.

| Evidence group | Obligation |
|----------------|------------|
| Observable truths | VERIFIED, FAILED, PRESENT_BEHAVIOR_UNVERIFIED or uncertainty with actual evidence |
| Artifacts and key links | Existence, substance, actual wiring and behavioral limits |
| Requirements / decisions | Exact approved obligation and delivered evidence |
| Deliverable Coverage | Every outcome classified by coordinator/verifier; missing evidence remains a gap |
| Required checks | Current passing receipts at matching command/configuration/input digest |
| Human Verification | Actual required judgments and prepared protocol; Pending until actual response |
| Security / issue links | Full canonical coverage and fresh independent non-author audit |
| Findings / gaps | Stable IDs, authority, observed failure, affected paths and next owner |

The verifier returns gaps and does not author fix PLANs. Decision-reference traceability never waives acceptance. Incidental success records its undeclared precondition/order/fixture reliance and necessary hardening without inventing a failure that was not observed.

## Genuine quick verification

The path is `.planning/quick/NNN-slug/NNN-VERIFICATION.md`. Its metadata includes quick: NNN, status, covered_files, fingerprint, revision and issue_refs; retain v4 covered digest when synchronized by the current runtime. Quick fingerprinting includes QUICK.md and relevant PLAN/SUMMARY/covered source. Do not create a fictional phase ID.

Use `verification.status --quick ID`, `verification.resolve-file --quick ID`, `verification.fingerprint --quick ID` and `verification.current --quick ID`. Ready/merge use `--quick ID`, with explicit confirm and actual merge authorization for merge. Human acceptance, independent issue-link audit and semantic requirements still apply.

## UAT

Read the entire [UAT template](../templates/UAT.md#authoring-contract). Source contains one or more actual SUMMARY paths. Status is testing, partial or complete; diagnosis happens while partial and is never a completion/acceptance status.

Every action states acceptance identity, exact delivered entry point/controls, safe fixtures, one-sentence expected result and observed result. Replies are N PASS, N FAIL <observation> or N BLOCKED <reason>. Unavailable prerequisites remain blocked; product defects remain failed. Skips and blocks require a reason; skipping is not passing a required action. Preserve accurate total/pass/issue/pending/skipped/blocked counters.

A resolved gap requires a real executed resolving PLAN and matching SUMMARY, with resolved_by and resolved_at. Preserve stable gap identity and history; later regression gets a fresh gap ID. Reconciliation does not invent an action result or final human decision.

Complete requires every required action to pass and the actual human's final acceptance recorded. Keep PENDING HUMAN acceptance otherwise. Maintainer technical preparation, AI review, source inspection, issue closure and silence never supply that decision. The canonical UAT issue has its own exact Human acceptance fields and does not replace the local UAT record.

## STATE, PROJECT and requirement ownership

STATE is derived by state runtime operations and its guarded save/review contract. Preserve the closed section set, explicit active blockers, roadmap evolution, authorized deferred items and continuity. Keep the current digest small (150 lines), preserving full history in owning records/Git/archive. Do not restore upstream performance sections without a runtime writer.

PROJECT Key Decisions is written with state.add-decision; optional ADR rationale links to it. REQUIREMENTS traceability changes use requirements operations. Narrative wording changes need approved intent and evidence; structural repair is not scope editing.

## Integrity and validation boundaries

The current runtime validates strict PLAN metadata: phase, plan, type, wave, depends_on, files_modified, files_deleted, resources, autonomous, requirements, acceptance, documentation, checks, issue_refs and must_haves. Acceptance, documentation and issue_refs are top-level lists; `checks` is a list of nonempty argv string arrays. SUMMARY requires phase, plan, status, requirements-completed, acceptance, documentation and issue_refs. CONTEXT requires phase, discussion and issue_refs. Identity must match the artifact path and related phase records. These structural checks do not prove task semantics, behavioral correctness, actual human approval or safe provider links.

Verification reports preserve fingerprint, revision, covered_files and `covered_digest: "v4:sha256:..."`; currentness binds clean source, fingerprint, exact revision ancestry and valid check receipts. A matching digest proves content correspondence, not behavior. Validation enforces the current record contract; it does not grant authority, waive acceptance, or manufacture SUMMARYs for artifact-only roles.

The supported YAML reader handles safe anchors, aliases and merge keys, including indentationless sequences. Do not describe all YAML anchors or merges as unsupported. YAML parsing and structural validation still do not validate every semantic relationship or establish human decisions.

## Update, review and retirement

1. Use the operation owning the structure and preserve all unrelated narrative.
2. Read planning.review findings and snapshotDigest before structural repair.
3. Apply only the fresh reviewed digest with planning.repair --apply --expect DIGEST; stale source blocks.
4. Resolve semantic conflicts through the coordinator and approved owner, never automated guessing.
5. Retire selected records through exact-path planning.archive preview, expected digest and confirm. Preserve manifests and collision-safe recovery.
6. Close blockers/todos/phases/milestones through their owning operations with actual evidence. Do not strike through, mark Closed in place or delete history by hand.
7. Resource cleanup is separate: fresh exact deletion preview/token approval and integration evidence are required.

All command arguments here are examples of the owning interface; read [the current API](../bin/README.md) for exact positional/options/results before invoking. Report checks actually run, pending evidence and implementation limits honestly.

## Historical gap reconciliation and final human evidence

A historical `result: issue` may stop blocking only through the preserved resolved-gap path: valid stable gap_id, resolved_by and resolved_at; an executed resolving PLAN; a complete matching committed SUMMARY with specific evidence for that gap; and final actual Human acceptance of the covered build. Every remaining required current action must pass. Skipped, not-testable, blocked and pending required actions remain blocking.

If explicit human retest is required, record that actual retest pass; never assume it from a SUMMARY. Diagnosis, a relabeled status, a checked item or a resolving commit alone is insufficient. This narrow historical effective-resolution path preserves the original issue evidence and does not manufacture final human acceptance.
