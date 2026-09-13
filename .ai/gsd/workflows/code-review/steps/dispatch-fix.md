<step name="dispatch_fix">
If the `--fix` flag was passed (`FIX_FLAG=true`), delegate to the `code-review-fix.md` workflow
to auto-apply findings from the REVIEW.md that was just written (or that already existed).

This step runs AFTER `commit_review` so REVIEW.md is guaranteed to be on disk before the fixer
is invoked. If REVIEW.md was not created (agent failed, scope was empty, etc.), the `code-review-fix.md`
workflow handles the missing-review error and exits cleanly.

```bash
if [ "$FIX_FLAG" = "true" ]; then
  echo ""
  echo "─────────────────────────────────────────────────────────────────"
  echo "  --fix: delegating to code-review-fix.md"
  echo "─────────────────────────────────────────────────────────────────"
  echo ""

  # Build the fix sub-arguments: pass phase arg plus any --all/--auto flags
  FIX_ARGS="${PHASE_ARG}"
  if [ "$FIX_ALL" = "true" ]; then
    FIX_ARGS="${FIX_ARGS} --all"
  fi
  if [ "$FIX_AUTO" = "true" ]; then
    FIX_ARGS="${FIX_ARGS} --auto"
  fi

  # Load and execute the code-review-fix workflow.
  # The fix workflow is the canonical implementation for all fix logic:
  # gsd-code-fixer agent dispatch, --auto iteration loop, REVIEW-FIX.md commit,
  # and result presentation. Do not duplicate that logic here.
  Workflow(workflow=".ai/gsd/workflows/code-review-fix.md", args="${FIX_ARGS}")

  # Exit after fix workflow completes — present_results is for review-only output.
  # The fix workflow has its own present_results step.
  # Exit workflow.
fi
```

If `FIX_FLAG` is false, skip this step entirely and proceed to `present_results`.
</step>


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

The complete upstream body above is retained from GSD-Core at
`c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977`; only recorded reference substitutions
and explicit local conflict corrections have been made. See
`.ai/gsd/PROVENANCE.json` for exact source hashes and changes.

Read `.ai/gsd/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/gsd-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The upstream `config.json`, `/gsd:*` commands, tool
names, hooks, and Node CLI examples describe GSD's system; this import does not
install or activate that system. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
