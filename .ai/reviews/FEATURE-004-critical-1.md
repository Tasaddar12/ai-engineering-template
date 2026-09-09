---
subject: FEATURE-004
iteration: 1
status: CHANGES_REQUIRED
base: 49f1230224e518ca1d594aeee613612763c9e042
head: 2229b578061965b73e83036b7dcec73f5c43b0de
reviewer_session: critical-review-feature004-20260908-1
implementer_session: native-execution-agents
summary: Full updated agent/provider/handoff/review implementation inspected; incomplete diff acceptance after redaction and prohibited-scope alias bypass require repair.
issues:
- id: REVIEW-001
  category: correctness
  files: [src/ai_engineering/review.py, src/ai_engineering/git.py, src/ai_engineering/runner.py]
  explanation: A raw captured diff can be truncated and then shortened by secret redaction below the Git length sentinel, allowing review_assignment to publish an incomplete diff as complete.
  required_change: Carry explicit capture and final-output truncation/completeness evidence independent of redacted string length, and reject incomplete Git observations before constructing review assignments.
  validation_required: A committed diff with repeated harmless synthetic configured secret values exceeding capture capacity must fail closed or retain every changed line; ordinary oversized output, Unicode output and untruncated redacted output must also have honest completeness evidence.
- id: REVIEW-002
  category: security
  files: [src/ai_engineering/agents.py]
  explanation: Prohibited-scope validation compares raw changed_files strings, accepting backslash and Windows case aliases of prohibited paths.
  required_change: Compare normalized contained changed paths and prohibited path roots with platform-correct containment semantics instead of raw slash-sensitive string prefixes.
  validation_required: Reject private/code.py and private-backslash-code.py for prohibited private scope; reject differently cased aliases on Windows; preserve valid siblings and ordinary allowed changes.
security_findings:
- REVIEW-002 bypasses assignment-specific prohibited scope.
- REVIEW-001 can omit relevant code from the single critical review and must fail closed.
documentation_findings: []
validation:
- command: root venv python -m pytest tests/test_agents.py -q
  status: success
  result: 23 passed in 18.03 seconds on Windows
- command: ruff check and format --check
  status: success
- command: mypy src/ai_engineering
  status: success
  result: No issues in 12 source files
- command: git diff --check
  status: success
---
# Critical Change Review

## Summary

CHANGES_REQUIRED. Reviewed the complete 49f1230224e518ca1d594aeee613612763c9e042..2229b578061965b73e83036b7dcec73f5c43b0de FEATURE-004 diff, covering the agent, handoff and review modules, seven definitions, six structured output templates and agent tests. Role/model/phase selection, immutable dispatch evidence, replay, uncertainty handling, transport authority, result identity and full-diff review preparation were inspected. Two independently reproduced failures block acceptance. These are implementation repairs within the single critical review stage.

## Blocking issues

| Category | Location | Exact issue | Required fix |
| --- | --- | --- | --- |
| correctness | review.py:124; git.py:55; runner.py:53 | Redaction conceals that raw captured diff was truncated | Explicit completeness/truncation signal, independent of final string length |
| security | agents.py:274 | Raw path prefix checks miss prohibited backslash and Windows case aliases | Normalize paths and compare actual contained path roots |

### REVIEW-001 — Redaction hides truncated full-diff evidence

Category: correctness

Files: src/ai_engineering/review.py:124, with affected integration boundaries src/ai_engineering/git.py:55 and src/ai_engineering/runner.py:53/372.

Issue: review_assignment relies on Git.diff's returned stdout as the complete committed diff. Git rejects output whose final string length reaches the runner limit, so ordinary ASCII overflow correctly fails closed. However, the runner first truncates raw capture, then replaces configured secret values, then applies its final character limit. Redaction can shrink a truncated prefix below Git's sentinel. In a temporary Git repository with execution.max_output_chars: 512 and a harmless synthetic configured secret repeated in a greater-than-10KB committed diff, review_assignment succeeded and wrote a 379-character patch containing 22 redacted lines. The final changed statement was absent and truncation was not reported. The assignment nevertheless presented the patch as the complete reviewed revision.

Required change: Make completeness explicit at the command/Git boundary, including discarded raw bytes and final character truncation, and require complete evidence before preparing a review. Do not infer raw completeness from the length of transformed/redacted text. A bounded oversized diff may fail with an actionable recovery error; it must never silently become an approved review input. Coordinate any narrow dependency-boundary change with the coordinator because Git and runner were introduced by FEATURE-002.

Validation required: Preserve the exact redaction-shrink reproduction with a synthetic secret and a final sentinel change beyond capture capacity. Assert review assignment fails before publishing an incomplete patch or else retains all expected changes. Cover ordinary ASCII overflow, Unicode capture boundaries and complete redacted output. Never expose an actual credential in fixtures or reports.

### REVIEW-002 — Prohibited paths are accepted through separator and case aliases

Category: security

Files: src/ai_engineering/agents.py:274.

Issue: scope_paths validates/normalizes changed_files, but its normalized return value is discarded. The later prohibited-scope check uses original strings with only forward-slash prefix comparison. A temporary-project assignment with allowed_scope: ['.'] and prohibited_scope: ['private'] accepted COMPLETE outputs claiming private\code.py and, on Windows, PRIVATE/code.py. ConstraintPolicy correctly considers those paths inside the broad allowed checkout; the assignment-specific prohibition is the missing boundary. Both outputs were durably accepted as completion results.

Required change: Resolve each changed path and prohibited root consistently through contained, validated worktree-relative paths, then compare equality/descendant relationships using filesystem-correct case semantics. Ensure the normalized values are actually used. Keep broad allowed scope subject to the explicit prohibition and existing protected-file constraints.

Validation required: Reject the original forward-slash form, backslash form, mixed-separator descendants and Windows case aliases. Confirm a true sibling such as private-other/code.py remains allowed where declared. Failed validation must not persist result.yaml as verified completion.

## Security findings

The two blockers affect the relevant review and file-authority boundaries. Other inspected behavior includes explicit reviewer capability/read-only checks, independently generated reviewer sessions, model/role/permission binding in bridge preflight, configured authority before external bridge invocation, immutable output/request/intent checks, refusal to blindly replay uncertain effects, secret-value rejection before request serialization and contained handoff/output paths. No actual external provider, credentials or paid service was used by the reviewer.

## Documentation findings

No additional documentation blocker. Module docstrings clearly distinguish a trusted permission-enforcing bridge from a subprocess sandbox, describe the exact output write exception and preserve immutable evidence. Agent behavior and model configuration remain separate. Structured output schemas and templates are explicit. Plan-specific contracts remain under .ai; package definitions were inspected as instructed because installed root definitions are awaiting reviewed synchronization.

## Validation inspected and limits

- Verified worktree HEAD: 2229b578061965b73e83036b7dcec73f5c43b0de.
- Independently ran root .venv/Scripts/python.exe -m pytest tests/test_agents.py -q in the assigned agents worktree: 23 passed in 18.03 seconds.
- ruff check src/ai_engineering tests: passed.
- ruff format --check src/ai_engineering tests: 51 files already formatted.
- mypy src/ai_engineering: no issues in 12 source files.
- git diff --check for the complete feature range: passed.
- Independently reproduced ordinary oversized diff rejection, then the distinct redaction-shrink acceptance failure, using a temporary real Git repository and harmless synthetic configured secret.
- Independently reproduced accepted prohibited completions for backslash and Windows case aliases with controlled providers in temporary projects.
- Coordinator additionally reports final-head Ubuntu 24.04/Python 3.12 agent suite: 23 passed in 24.09 seconds; that Linux run was not independently repeated by this reviewer.
- No source edits, Git/index mutations in the assigned repository, installations, actual credential access or external actions were performed. Temporary Git repositories were used only for bounded behavioral probes.
