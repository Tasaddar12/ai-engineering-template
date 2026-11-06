<!-- generated-by: executor -->
# Quick verification delivery slice

Related issue: https://github.com/Tasaddar12/ai-engineering-template/issues/193.

Base: `97a2f0dc03b739f4ba0ad89dc5f5298269d8cd46`.
Implementation: `0004627cd6a111881feccf441207dc154c833846`.
Owned checkout: `.worktrees/quick-verification-delivery` on
`agent-quick-verification-delivery` (renamed from the coordinator's original
`fix/quick-verification-delivery` assignment to satisfy the executor branch rule).

## Changes

- Add mutually exclusive `--quick DIR` selection for `pr.ready` and `pr.merge`.
  Resolve quick ownership through the shared verification resolver and require a
  direct canonical quick owner. Explicit `--phase` paths retain phase-only scope.
- Require a full `--expected-head` for quick delivery. Preserve current-evidence,
  local HEAD, OPEN PR identity, branch/head and provider-check gates; merges still
  require `--confirm` and use `--match-head-commit`, without an admin override.
- For quick readiness, require matching non-draft provider readback and recheck
  evidence and local HEAD around the provider operation. A failed or changed
  readback is never certified as ready. Forward complete evidence options to the
  shared currentness owner for both quick actions.

## Checks

Tests ran on the working candidate atop the base above, committed unchanged as
the implementation SHA. Commands used Python 3.12.14 from the bundled runtime;
`TEMP` and `TMP` selected the authorized local temporary directory.

| Command | Observed result |
|---|---|
| `python -m unittest discover -s tests -p 'test_*delivery*.py' -v` | 30 tests passed in 25.980 seconds, zero skips. |
| `python -I scripts/verbs.py --fail-on-unknown` | 324 registered verbs, 600 call sites, zero unknown call sites. |
| `git diff --check` | Passed. |

The 12 new delivery-owner tests control verification verdicts and context
resolution at the module boundary and replace the provider with an in-process
fake. They exercise successful quick selection, evidence forwarding, confirmation,
missing/failed/stale evidence, owner ambiguity, phase substitution refusal,
missing/closed/wrong-branch/wrong-head/malformed PR identity, pending/failed/missing
checks, conflicts, local movement, provider refusal and changed readback. Existing
14 head-guard and four body-template tests also pass.

## Remaining integration

This slice depends on the coordinator's new `verification.verification_dir` and
quick currentness implementation. Its isolated base does not contain that API;
delivery unit tests intentionally use an explicit resolver seam. Real CLI/Git
quick-owner, installed Codex/Claude, report-successor and configured-receipt
integration must run after composition. These tests do not establish live provider
readiness, deployment or consumer adoption.

No distinct new threat was identified in the bounded selector/gate delta. The
existing independent review, body/link audit, currentness and remote-provider
protections remain release requirements. No real PR was marked ready or merged;
no push or publication was performed by this worker.
