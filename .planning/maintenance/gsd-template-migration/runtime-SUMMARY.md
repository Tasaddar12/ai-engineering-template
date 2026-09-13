# Runtime and planning data migration summary

## Outcome

Complete GSD artifact structures now connect to the existing Python phase runtime.
Project records are separate from reusable instructions, and imported semantics
have explicit local execution extensions and boundaries.

| Slice | Commit | Result |
|---|---|---|
| Native planning inputs | 7b70ae1 | Move data, consume PLAN/XML/requirements, preserve runtime safeguards |
| Full artifacts | 155a61c | Full project skeletons, context seeding, summary/verification/UAT, STATE preservation |
| Audit completion | This commit | Enforce declared deletions, protect ROADMAP, fix encoding, record evidence |

## Source and data flow

| Entry or boundary | Owner and observed behavior |
|---|---|
| `.ai/runtime/phase.py` | Resolves repository and rejects leftover legacy data before CLI dispatch |
| `phase_records.load_phase` | Reads `.planning/config.yaml`, phase CONTEXT and native NN-CC-PLAN metadata/XML; validates authorization, paths, dependencies and executable tasks |
| `phase_runner.new_phase` | Extracts the complete upstream context File Template and appends local authorization/acceptance extensions |
| `phase_runner.run_phase` | Launches isolated subprocess workers; waits for integrated prerequisites, path/resource exclusion and capacity |
| `phase_runner.audit_worker` | Audits every commit, ancestry, clean output, exact path ownership, declared deletion, full summary evidence and real checks |
| `phase_runner.verify_phase` | Runs checks, assigns a separate verifier checkout, validates full upstream report plus exact revision/local evidence, and attests the committed report |
| `phase_runner.uat_phase` | Preserves full upstream UAT sections, summary sources, cases, observations and diagnostic gaps; source changes start a retained historical session |
| `phase_runner.sync_state` | Changes only Runtime Status; preserves all authored upstream STATE sections |
| `phase_runner.publish_phase` | Checks source/report attestation, checks and required human UAT, then publishes; never merges |

Durable project data is in `.planning/`. Runtime checkpoints, process receipts,
assignments and logs remain operational data under the Git common directory's
`ai/phases/`. Matching old-path checkpoints fail explicitly; no live attempt is
silently converted or forgotten. No external adopting-project state was inferred.

## Validation evidence

Python used: `C:/Users/killi/AppData/Local/Temp/gsd-runtime-test-venv/Scripts/python.exe`
(Python 3.13, PyYAML 6.0.3). Worker-only template tests used
`GSD_TEMPLATE_TEST_SOURCE=C:/Users/killi/AppData/Local/Temp/gsd-template-source-20260913/gsd-core/templates`
because template import is integrated by the parent separately.

| Check | Result | Scope and limit |
|---|---|---|
| Full-template end-to-end regression | Passed, 19.257s | Entire upstream output blocks for context/PLAN/summary/verification/UAT; real Git workers, source checks, failed then passed human observations, STATE prose retention, publication boundary |
| PhaseRecordTests after second slice | 10 passed, 64.542s | Creation, allocation, legacy rejection, malformed native tasks, replan/recovery, full artifact flow |
| Declared/undeclared deletion regressions | 2 passed, 13.998s | Declared exact deletion integrates; undeclared deletion is rejected and worker output preserved |
| Python compilation | Passed during implementation | Runtime and fixture modules |
| Final integrated suite | Parent must run at final integrated commit | Use actual imported `.ai/templates` with no template-source override |

Earlier broad runtime runs overlapped implementation edits and exposed fixture
migration errors that were corrected (old phase metadata, wave/must_haves fields,
and overly broad checkpoint text detection). They are development feedback, not
final revision evidence. The broad run still in progress during handoff is also
not the final integrated acceptance result. The parent runs the whole suite on a
committed integration revision. The GitHub API boundary is simulated; no live model
quality or real GitHub publication was tested by these deterministic fixtures.

The worker checkout's generic documentation scanner predictably sees stale links
in files assigned to other components and example references inside complete
upstream templates. The parent reconciles active links and tests upstream examples
through provenance/reference coverage; those failures are not suppressed here.

## Exact changes.log entries for coordinator integration

- Move adopting-project PROJECT, REQUIREMENTS, ROADMAP, STATE, phases, codebase maps, specifications, decisions and execution config from `.ai` to `.planning`; `.ai` retains reusable runtime/instructions/templates. Add the previously empty decisions directory to Git with `.gitkeep`.
- Seed the complete upstream PROJECT, REQUIREMENTS, ROADMAP and STATE artifact skeletons. Add an explicit unfilled-adoption notice so illustrative requirements, phases, metrics and placeholders cannot be mistaken for actual project intent or history.
- Adopt phase-local NN-CC-PLAN.md naming and upstream phase/plan/type/wave/files_modified/files_deleted/requirements/depends_on/XML task structure. Keep all imported teaching guidance; add local kind/resources/acceptance/documentation/argv-check fields and a Documentation handoff section.
- Keep the complete upstream context skeleton and append pending YAML authorization plus Acceptance, Authorization and Open Questions. The runtime reads the GSD domain/Phase Boundary and checks native task action/read/verification/done content.
- Preserve full upstream SUMMARY sections and requirements-completed; add local acceptance/documentation evidence and Checks. Preserve full verification-report sections and add exact revision plus Acceptance/Integration/Documentation/Findings; the runtime's source/report attestation remains separate from upstream covered_digest.
- Generate and update full upstream UAT Current Test/Tests/Summary/Gaps, preserve its source list of SUMMARY files, and add separate source_fingerprint/revision/cases/history receipts. CLI fail is rendered as upstream issue; blocked/skipped remain unresolved. Preserve authored test text, extra sections, diagnosed gaps and every recorded observation.
- Preserve the entire STATE artifact; sync updates a dedicated Runtime Status section only.
- Preserve upstream wave and coupling_justified guidance while retaining conservative path/resource serialization and dependency-driven scheduling; the current runtime does not override isolation for advisory coupling exemptions.
- Preserve upstream checkpoint and user_setup templates; process dispatch rejects unresolved non-autonomous/checkpoint/setup plans. The coordinator handles required interaction, records actual decisions/evidence, and prepares an autonomous continuation.
- Preserve upstream decimal phase insertion guidance; this Python allocator remains explicitly limited to integer NN phase identifiers until later command expansion. No rounding, silent ignoring or claimed decimal execution support is added.
- Keep `.planning/config.yaml` as the Python runtime's real execution config. Full upstream config.json is an optional upstream configuration template, with no invented equivalence to the Python config.
- Reject legacy `.ai` project data, IMPLEMENT records and matching old-path checkpoints explicitly. Inspect/finish old attempts with their original runtime; archive inspected checkpoints explicitly before new attempts rather than silently migrating live state.
- Honor the upstream files_deleted semantic: audit each commit and require exact declared deletion paths even if files_modified or a directory prefix otherwise grants ownership. Add ROADMAP to immutable coordinator input ownership/fingerprints.

## Remaining coordinator work

1. Integrate this final slice and push the draft progress update.
2. Run the full suite using integrated templates and reconciled active documents.
3. Independently review runtime claims, source/template mapping and all acceptance.
4. Perform user-authorized final publication/merge/cleanup only after required checks.
