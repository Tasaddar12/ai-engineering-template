<!-- generated-by: doc-writer -->
# Quick verification documentation slice

Related issue: https://github.com/Tasaddar12/ai-engineering-template/issues/193.

Documentation checkout base: `97a2f0dc03b739f4ba0ad89dc5f5298269d8cd46`.
Source inspected in the coordinator's checkout:
`032aa1c2fedf9d1f50d0916cb57d91ce42022a43`.

## Changes

- Explain explicit canonical quick-directory selection for verification in both
  host runtimes, QUICK/PLAN identity and task-owned fingerprint inputs.
- Document quick report statuses separately from complete currentness, including
  invalid identity/status refusal and fresh capture after QUICK record changes.
- Replace the old phase-only successor claim with matching tracked QUICK/PLAN
  ownership while preserving protected inputs and report-only history proof.
- Document exclusive `--quick`/`--phase` delivery selection, required full
  `--expected-head` for both quick ready and merge, provider readback, and
  unchanged independent review and merge authorization requirements.

## Checks

The final documentation candidate was checked with Python 3.12.14 from the
bundled runtime. The commands below are documentation/static checks, not proof
of integrated runtime behavior or a live provider operation.

| Command | Observed result |
|---|---|
| `python -I scripts/links.py` | Zero broken targets. |
| `python -I scripts/check_markdown_python.py` | 337 tracked Markdown files scanned, zero findings. |
| `python -I scripts/verbs.py --fail-on-unknown` | 324 registered verbs, 600 call sites, zero unknown call sites. |
| `git diff --check` | Passed. |

## Limits and handoff

Owned paths are `engineer/bin/README.md` and this summary. Source claims were
checked against `verification.py`, `verification_successors.py` and `delivery.py`
at the inspected source revision. The assigned doc-writer skills query returned
an empty skill list. No full source verification, installed-host execution,
consumer update, live readiness transition, push, PR publication or merge is
claimed by this documentation slice. The coordinator must integrate these docs
and obtain applicable independent review and runtime verification.
