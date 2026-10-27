# Plan-Checker Examples

> Progressive-disclosure reference for `agents/plan-checker.md`. The checker
> inlines this file from its `<examples>` block via `@`; the calibrated few-shot
> set lives separately in `engineer/references/few-shot-examples/plan-checker.md`.

## Outcome-scoped sizing warning

**Plan 01 analysis:** five tasks touch twelve files while delivering one account recovery outcome. Inspect the configured task cap and `estimate_scope`; file count alone does not prove excessive scope. Preserve D-07's approved outcome and contract-first thin slice.

```yaml
issue:
  id: PC-01-01-SCOPE
  authority: "Configured task cap and approved D-07 outcome boundary"
  dimension: scope_sanity
  severity: warning
  required_property: "A coherent independently verifiable outcome within the configured cap"
  description: "Explain the estimate_scope and actual producer/consumer dependencies; file count is only a signal"
  plan: "01-01"
  metrics:
    tasks: 5
    files: 12
  fix_hint: "Preserve the complete authorized outcome; propose a dependency/outcome split to the coordinator only if needed"
```

A demonstrated cap violation or missing acceptance is assessed against its actual authority. Do not invent a fixed 2-3-task rule, context percentage guarantee or layer-by-layer split.
