# Local material audit — 2026-09-08

The user requested that useful scripts have a concrete purpose, that required
project material be transferred into version control, and that `.ai/local` not
become an ignored dependency of the delivered project.

The audit found 21 top-level Python helpers. Source, tests, reusable docs, README
and package configuration contain no references to `.ai/local`, `.codex/local`,
`.claude/local` or the manual `coordinator.py`. This textual check does not prove
final packaging: the project is still being implemented, and TASK-037 owns the
clean checkout, wheel and source-distribution verification.

The [initial inventory](local-inventory.tsv) records top-level filenames, byte
counts and hashes before this cleanup. Nothing in the local runtimes or temporary
Git fixtures is a new product module.

| Material | Purpose and disposition |
| --- | --- |
| `coordinator.py` | Active manual gate/checkpoint helper. Moved into this tracked directory; root discovery and dispatch lookup now use this location. Candidate Python defaults to the invoking interpreter. No gate behavior is promoted into the runtime. |
| `count-native-invocations.py` | Active manual budget observation. Moved here with explicit input/output arguments; only whitelisted metadata is retained. |
| 21 `dispatch/*.json` files | Existing attempt identity observations needed to resume coordination. Preserved byte-for-byte here with `.json.txt` suffixes; new dispatches use the tracked directory. |
| `agent-brief.md`, `reviewer-brief.md`, 11 `next-*-dispatch.md` files, `review-024-focus.md` | Still-needed task/review constraints. Copied here as the current versions, with the user's requirement added to owner/reviewer and packaging briefings. Local copies are superseded. |
| `git-port-readiness.md`, advisory `probe.py`, Windows/Linux `results.json` | Still-needed TASK-007/009 planning evidence. Preserved byte-for-byte here as text. Temporary repositories, indexes and command logs remain disposable local fixtures; the saved results contain the observations. |
| `adopt-006-a3.py`, `adopt-recovery006.py`, `adopt-recovery017.py`, `amend_graph_r4.py` | One-use historical state/recovery mutations. Their resulting decisions, state transitions and review history are versioned. They are obsolete after their expected-generation operation and must not be reused as engine implementation. |
| `checkpoint-006-a2-failure.py`, `checkpoint-014.py`, `checkpoint-017-active.py`, `checkpoint-017-queued.py`, `preserve-006-a2-failure.py`, `record-a3-probe-classification.py` | One-use evidence/checkpoint writers. Required outcomes live in tracked state, recovery reports and progress history. No future workflow may depend on rerunning these fixed historical edits. |
| `cleanup-obsolete-worktrees.py` | Completed cleanup of three exact old checkouts. The tracked cleanup record preserves branch/commit and evidence checks. It is not a reusable cleanup tool and must not be rerun. |
| `contracts-probe.py`, `contracts-reference-probe.py` | Exploratory checks against the old TASK-004 attempt. Accepted tracked schema tests cover immutable schema snapshots and invalid/dynamic references; preserved R1 history explains failures. These probes are obsolete. |
| `check-python311.py`, `check-runtime-metadata.py`, `diagnose-a3-runtime.py`, `preflight-queued.py`, `preflight017.py`, `verify-queued-origins.py` | Past compatibility/origin diagnostics. The active candidate helper now records declared suites and actual origins, and relevant original results are in tracked validation/recovery evidence. Their fixed old heads are not current tests. |
| `CURRENT.md`, `implementation-notes.md` | Local conversation scratch with accumulated superseded checkpoints. The tracked STATE, task records, full-implementation progress, dispatches and decisions provide durable continuation; new important decisions must go there. |
| Local result text/JSON, virtual environments, Python runtimes, bytecode and temporary Git repositories | Execution artifacts/cache. Retain only meaningful results in tracked evidence; recreate environments from declared dependencies. Do not ship these directories. |

The actual product behavior belongs to the existing graph: TASK-009/010 own
durable state and intents, TASK-017 agent simulation, TASK-018 validation,
TASK-019/020 candidate/review gates, TASK-023 integration, TASK-025/026 recovery
and coordination, TASK-029/030 delivery/retention, TASK-034 CLI composition, and
TASK-037 packaging and complete test execution. Copying the manual helper into
`src` would bypass those accepted contracts and reviews; implement those slices
in their owned tracked modules instead.

TASK-007's owner confirms its finite Git helper is inside tracked `src/git_ops.py`
and regression tests are in its owned test file; temporary repositories/logs are
test fixtures. TASK-018 received the same requirement. Every subsequent owner
and reviewer receives the tracked brief. A required private subprocess helper is
part of the product's dependency closure, even if it is not a public CLI.

Final verification must run all required tests from tracked files and exercise
clean wheel/sdist installs outside the checkout, without `.ai/local` or an editable
root installation supplying modules, fixtures or assets. This is recorded in the
TASK-037 dispatch briefing and remains an outstanding gate, not a claimed pass.

After verifying original inventory hashes and tracked destinations, the two active
local script copies and 14 superseded local briefing copies were removed.
The local CURRENT file now only points to the tracked current checkpoint.
