# Repository restoration and cleanup review

Date: 2026-09-07. This is repository setup, not implementation of PLAN-001.

## Source and history

The transferred `AI-Engineering-Framework-Foundation.zip` contains 196 source files, a complete Git bundle, and transfer instructions. The loose root `README.md` and `PLAN-001.md` were byte-identical copies of the archive's root README and `docs/plans/PLAN-001.md`.

Restored the source directly into this repository, without an extra nested checkout. Verified every restored file against the archive and confirmed the tracked tree matches the imported foundation commit:

`943375423a992a54f55385ae9b48f9bbf822b92f` — Establish AI engineering framework architecture and isolated implementation plan.

Both `main` and the retained `ai/state` branch were recovered from the bundle. No remote is configured. The local setup commit on `main` follows the original foundation commit; `ai/state` retains the original state checkpoint because no workflow state has changed.

Transfer fingerprints (SHA-256):

- Source ZIP: `572c7d2b07160e70b8cb24b731882e98bfdc324313f75254c0f457cc15eabebd`
- Git bundle: `df2e4aa17090ce22115c441c4324415de5f72b7139a00049f1c1f18c3da7f2d9`

## Active work and retained history

Reviewed both planning conversations, **Git Repo Layouts** and **Framework foundation complete**, against the copied records. The later foundation documents refine the earlier examples: JSON records and stable entity paths are intentional, as is the six-workflow CLI. There is no reason to recreate the earlier YAML or status-directory examples.

- [Current state](../.ai/STATE.json) remains the completed engineering foundation, with no active runtime runs or completed implementation plans.
- [SPEC-001](../.ai/specs/SPEC-001.md) and [PLAN-001](plans/PLAN-001.md) are active. The approved task graph is revision 2, with its existing independent isolation review.
- All 39 implementation tasks remain: TASK-001 is `ready`, and the other 38 are `backlog`. TASK-001 is the only task with no prerequisites; start it in a dedicated worktree. Subsequent tasks become eligible only after their dependencies pass the required acceptance gates.
- [Graph revision 1](../.ai/graphs/PLAN-001-r1.json) is explicitly superseded. Its [draft task snapshot](../.ai/archive/PLAN-001-draft-r1/task-snapshot.md), the [isolation review history](plans/PLAN-001-isolation-review.md), and the original Linux validation evidence are retained as provenance.
- Real agent/provider adapters, real PR/CI integration, and release hardening remain future plans in the [roadmap](plans/ROADMAP.md).

The task records, approved graph digest, schemas, and implementation scope are unchanged by repository setup. Help and version are still the only supported CLI features.

## Cleanup disposition

| Item | Disposition |
| --- | --- |
| Root `README.md` | Retain as the entry point; link to this review. |
| Loose root `PLAN-001.md` | Remove the verified duplicate; `docs/plans/PLAN-001.md` is the canonical human plan. |
| Transfer ZIP and imported bundle | Remove after source, history, and validation checks; Git retains the foundation. |
| Transfer-only `RESTORE.md` | Inspect from the archive; do not add to the restored source tree. |
| Superseded graph, draft snapshot, prior review and command evidence | Retain in their existing locations; these explain approved planning decisions. |
| Temporary validation environment, build outputs, and import scratch files | Remove after checks; do not leave untracked or ignored setup debris. |
| Git text and ignore settings | Normalize text to LF across platforms; ignore local credentials, caches, coverage output, and desktop metadata. |

The original [foundation report](FOUNDATION-REPORT.md) and [Linux validation report](VALIDATION-RESULTS.md) describe the earlier session. They are historical evidence, not claims that this Windows restoration ran the planned runtime.

## Validation

Windows restoration results are captured separately in [initialization command evidence](validation/initialization-windows.json). The checks cover imported Git integrity, source/archive parity, installed package help/version, rejection of unsupported plan execution, schemas, task dependencies, isolation approval, acceptance coverage, and local documentation links. They do not establish runtime worktree orchestration, live model execution, remote hosting, or CI behavior.
