---
phase: maintenance-issue87-auto-worktree
revision: 602804072671516a6fbe16d5535e1a3b6480c280
scope: DOC-01 correction only
status: clean
claims_checked: 6
claims_passed: 6
claims_failed: 0
claims_unverifiable: 0
issue_refs: [87, 98]
---

# Independent DOC-01 correction recheck

Repository doc-verifier, gpt-6-luna/medium, independently inspected the frozen
README wording against actual entrypoints and installer launchers. No tests,
edits, children, commits or provider writes. DOC-01 resolved; no failures.

The corrected paragraph at .ai/hooks/README.md:90-98 distinguishes registered
scripts, interpreters and decision adapters correctly after the frozen93 join.

| Claim | Evidence | Result |
|---|---|---|
| Python-suffix entries use Python; shell entries use Bash | install.py:497-505 | PASS |
| source-prewrite.sh delegates to runtime/lib/prewrite.py | source-prewrite.sh:6-16; prewrite.py:10-13,632-644 | PASS |
| Codex Python commandWindows resolves root in Python, uses runpy, propagates status | install.py:507-514 | PASS |
| Destructive hook copies import adjacent runtime module | destructive-git-guard.py:7-8; install.py:128-142 | PASS |
| Hooks reside under the selected host hooks directory | install.py:504-505,513-514 | PASS |
| Python source is not passed to Bash by Codex Windows launcher | install.py:507-514 versus separate Bash branch:515-559 | PASS |

This closes the wording correction only, not Task4 or live host movement. Final
joined-source documentation verification remains required after implementation.
