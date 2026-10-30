---
status: complete
input_revision: 48ce2980b0b3bfec27c71bea9d1b8bfe95a9036e
branch: review-pr171-contract-comments
---

# PR 171 research, estimate and model guard contracts

Restored the reviewed research and planner instructions and implemented their
original CLI contracts. The template's adopting-project records remain unfilled.

## Comment mapping

| Review comment | Result |
|---|---|
| Researcher base 103 | Restored original temporary JSON input instruction. |
| Researcher base 108 | Removed added provider config fields and MCP tool declarations/references. |
| Researcher base 116 | Restored original config/kind explanation. |
| Researcher base 159–162 | Restored all original cache arguments; CLI accepts full metadata without mandatory URL. |
| Researcher base 165 | Restored key/confidence assignment instruction. |
| Researcher base 179 | Restored classify-confidence command reference and output assignment. |
| Researcher base 182–184 | Restored original provenance tags. |
| Researcher base 688 | Restored A–D execution protocol; commands work with external JSON and contained cache writes. |
| Researcher base 845 | Restored source hierarchy checklist. |
| Planner current 155 | Removed the added second sentence; retained existing research flag change. |
| Planner current 270–272 | Restored calibration and sample-derived confidence instruction. |
| Planner estimate block | Restored calibrated tokens, raw_tokens and sample-derived confidence. |
| Planner base 379/current 375 | Restored Projected cost wording. |
| Model guard rule owner | Restored model-profile-resolution.md ownership. |
| Model guard deviations | Restored original reference path mapping. |
| Model guard MODEL_REFERENCE | Restored original reference constant; reference file already matches parent exactly. |
| Model guard SHIP_GATE_RE | Restored original regex. |
| Model guard ship functions | Restored ship_gate_shape and ship_hook_violations exactly. |
| Model guard removed tests | Restored parent tests exactly, including before-shell validation cases. |
| Context budget | Restored original POOR warning/pause behavior and estimate emission text exactly. |

## Implementation

- Research JSON uses the existing bounded explicit-input reader, which supports
  external temporary files read-only. Cache destinations remain repository-contained.
- Full original source/provider/confidence/kind metadata permits cache reuse.
  Missing citations remain an empty sources list with citationStatus not-provided;
  actual provided citations are validated and claimJudgment remains false.
  Content alone still fails. Bare classify-confidence --verified remains supported.
- estimate-calibration and estimate-calibrate rebuild the calibration record from
  PLAN raw_tokens and matching SUMMARY actuals. Invalid/unpaired samples are skipped.
  Factor is 1 before three samples, then the median actual/raw ratio. Confidence is
  low below three samples, med for three through five, high at six or more.
- estimate-check retains advisory budget checking, optional calibrated projection,
  finite nonnegative input validation and workflow.smart_zone_tokens configuration.
- Restored the extract-learnings calibration caller. No YAML migration, external
  review backend, retired workstream or @file behavior was restored.

## Checks

- python -m unittest tests.test_research_contracts -v: 2 passed.
- python -m unittest tests.test_research_contracts tests.test_retained_planning_tools -q:
  15 passed after the final source validation change.
- python -m unittest tests.test_model_omit_when_inherit_guard tests.test_retained_planning_tools -q:
  41 run, 1 skipped, 1 failed. The sole failure is the restored real-tree ship
  validation test: this isolated input lacks the original ref.agent regex and
  IN-CONTEXT before-shell instructions in engineer/workflows/ship.md.
  All model guard fixture tests and retained planning tests passed.
- git diff --check: passed (Git emitted only checkout line-ending notices).

## Remaining

The coordinator must integrate the separately assigned ship.md restoration and
rerun the model guard suite on the combined revision. This worker did not edit
that path or weaken its restored tests. One pre-existing model profile test is
explicitly skipped because this repository does not expose the upstream unknown
agent fallback contract.

Coordinator extension: removed only the expectedFailure decorator from
tests/test_gen_health_docs.py's test_shipped_health_md_already_passes_check.
Its assertion is unchanged. Execution awaits integration of the doc worker's
regenerated health table; the isolated input still carries the old table.

No project state, roadmap, requirement or phase record updates are proposed.
No stubs introduced. No additional threat surface beyond the assigned explicitly
named read-only JSON input contract was identified.

## Self-Check: PASSED

Owned source and report paths exist. Final integration verification remains
coordinator-owned as stated above.
