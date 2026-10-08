# Reusable source evidence implementation

Completed the authorized source/context/scout packet slice on
`phase-parallel-artifacts`, base `aa0b0443aa3e583e8a60370928c44b5edc9463c6`.
Owned files: `.ai/runtime/lib/evidence.py`, `tests/test_evidence_cache.py`, and
this summary. Pipeline/phase wiring, documentation, shared planning records,
benchmark fixtures and PR56 remain coordinator/other-worker owned.

## Delivered behavior

- `store(cwd, request)`, `lookup(cwd, request)` and `invalidate(cwd, request)`
  accept strict JSON envelopes or detached mappings. The pipeline coder owns
  `evidence.store`, `evidence.lookup`, `evidence.invalidate --spec <JSON path>`
  CLI wiring and safe request-file loading.
- The `source-evidence/v1` contract includes task class, question, full current
  source SHA, exact input paths, bounded scope, acceptance, explicit configuration
  and role/model/prompt-version provenance. Packets preserve structured outputs,
  cited evidence, status and SHA-256 fingerprints of every scoped file.
- All scoped bytes and directory/file inventories are revalidated, including
  ignored/untracked entries. Default reuse binds the original revision; explicit
  `reuse: {cross_revision: true, complete_scope: true}` permits identical-content
  reuse across revisions. Original source revision is retained on a hit.
- Common Git directory `ai-phase/evidence/state.json` shares packets across linked
  worktrees. Process locks serialize read/modify/write, temporary files are
  flushed and atomically replaced, and both state and packet digests are checked.
- Missing inputs, changed contracts/bytes/inventories, corrupt JSON/digests and
  incomplete/blocked/failed packets cannot produce reuse. Explicit invalidations
  preserve history and remain effective after an identical packet is stored.
- Traversal, Git metadata, unsafe refs, symlinks/junctions and nonregular scope
  entries are rejected. Lookup payload/citations are opt-in via `include_payload`.
  These records confer no execution or verification authority and make no
  provider prompt-cache-hit claim. Scouts remain read-only; coordinators store.

## Validation

`python -m unittest discover -s tests -p test_evidence_cache.py -v`:
14 tests in 20.196s, OK, one skipped. Real temporary repositories verify payload
citations, contract/config/question/provenance changes, byte/config/add/delete
invalidation, ignored/untracked/staged inputs, complete scope cross-revision
contracts, linked worktree reuse, failed packet history, invalidation permanence,
invalid/missing JSON fields, corrupt/rehashed-incomplete packets, unsafe paths,
and eight concurrent process writers preserving all packets and invalidations.
The native symlink creation test skipped with WinError 1314 because the host
lacks the required privilege. `git diff --check` passed. No heavy checks,
engine, Docker, model runs, push or merge were performed.

Required scouts `evidence-conventions` and `evidence-tests` completed at the
assigned base. Their consequential runtime/result and temporary-Git-fixture
citations were inspected before implementation. No unresolved scout questions
remain: working-tree bytes are explicitly fingerprinted, and common Git directory
state uses its own serialized lock.

## Decisions and deviations

Within the approved contract, hash the complete declared scope, including empty
directory inventory, rather than trusting only a selected subset of input files.
Capture compares file identity/mtime across stat and fstat and ctime within each
API because this Windows/Python host demonstrably reports different ctime values
between those APIs; a second byte-hash pass rejects concurrent content changes.
This preserves byte revalidation without false stale results on ordinary reads.

## Remaining and coordinator reconciliation

- Integrate this commit and the other worker's phase.py CLI wiring; run integrated
  CLI/aggregate checks and fresh independent review before final acceptance.
- Execute native symlink coverage on Linux CI (Windows test is retained and will
  run on hosts with symlink privilege). This is a host limitation, not a claimed
  passing check.
- Advance position/progress only after integrated evidence; this summary alone
  does not complete the phase. Record this source-evidence component as locally
  tested, with the above integration/verification dependencies outstanding.
- Metrics: three owned files; one source-evidence component; base recorded above;
  focused suite actual runtime 20.196s. No adoption requirement IDs changed.
- Session resume point: integrate the source-evidence slice, validate CLI and
  independent review, then publish under the existing authorization.

No known stubs or additional threat surface beyond the planned local filesystem
cache and JSON validation boundary. No shared STATE/ROADMAP/REQUIREMENTS updates.

## Self-Check: PASSED

Assigned root/branch/base verified; source module, tests and summary exist;
focused test evidence and diff checks recorded above. Only the three owned files
are staged for the slice commit; the coordinator receives its actual SHA in the
worker completion report.
