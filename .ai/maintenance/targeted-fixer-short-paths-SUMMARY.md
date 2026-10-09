---
status: complete
base: 6ec8749ec9f1bb420f677feef4ac9282f1f3b58d
---

# Windows handoff path canonicalization

## Changes

- In both embedded absolute-drive path handlers, resolve the candidate with `os.path.realpath` on Windows before containment and relative-path calculation. Non-Windows Windows-form path handling remains lexical.
- Added native Windows tests that execute both production embedded parsers. Real `GetShortPathNameW` aliases are accepted and normalized; outside-root absolute paths and actual directory-junction escapes are rejected.

## Checks

- PowerShell: `$env:PYTHONPATH='D:\Codex\2026-10-09\task-46\python-deps'; $env:PYTHONIOENCODING='utf-8'; & 'C:\Users\killi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -p test_handoff.py -v` — 39 passed, 0 skipped.
- Same environment; `-m unittest discover -s tests -p test_agent_sources.py -v` — 16 passed.
- Git Bash `.ai/hooks/context-handoff.test.sh` — pending/unverified at commit. The first run lost its output when the exec transport disconnected. A second run writes its output/exit code from the Bash child to `D:/Codex/2026-10-09/task-46/fixer-short-paths-shell.log` and `.exit`; no result was available before this commit. Do not count it as passed.
- External reviewer probe — not_run; the new native tests execute both assigned parser snippets directly.

## Deviations

- No source-scope deviations. Local full-suite evidence remains pending because the shell session transport disconnected; the coordinator should use the captured child result if it completes and require hosted CI before acceptance.

## Remaining

- Confirm the persisted context-handoff shell result or use final hosted CI; no local pass is claimed.
