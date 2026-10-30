---
status: complete
plan_head_before: "629ec42f29b0d2fb2b707aea05517d8c985d6496"
---

# PR 171 YAML detour rollback

Restored the exact 30 paths changed between `33990e5715f3977b8804324af21b8e2cf01a992b` and the starting revision `629ec42f29b0d2fb2b707aea05517d8c985d6496`, byte-for-byte from the former revision. Earlier authorized PR comment fixes remain intact. This rollback includes the YAML path, reader, fixture, health and subrepository documentation adaptations. No runtime-conformance repairs or format migration were added.

## Checks

- Verified the assigned repository root, `review-pr171-runtime` branch, starting revision and clean tree before writing.
- Compared all 30 restored files directly with their Git blobs at `33990e57`; every byte matched. The tracked tree matched that revision before this summary was added.
- All 42 command/skill pairs are byte-identical; `commands/COMMAND.md` is the separate catalog.
- `git diff --check 5ad2f56f` passed.
- With Git `usr/bin` on PATH and repository plus `tests` on PYTHONPATH, `python -m unittest tests.test_markdown_python tests.test_agent_sources tests.test_retained_runtime` passed: 46 tests in 34.805 seconds. The expected negative fixture prints a retired-helper finding while its test passes.

## Remaining

None within the exact rollback scope. No push, merge, branch switch, new tests or planning-record changes.

## Self-Check: PASSED

Rollback scope and checks verified; this summary accompanies the source-change commit.
