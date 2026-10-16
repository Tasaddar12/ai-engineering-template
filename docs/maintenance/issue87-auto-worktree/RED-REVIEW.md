# Independent pre-implementation RED review

## Native-entry RED: valid; corrected test gate released

Bounded independent recheck at `7081867d44fb8c02bd20984c523934ead4d587ae` compared correction `dcf73710d9557fc18b7ec8e8fa60cd09ce9594cd` with the prior authored test commit. **Clean; zero remaining findings; test gate RELEASE.** CR-01 now distinguishes observed entry HEAD from historical base and advances both existing-session controls. CR-02 passes the anchored primary environment through every real editing handler. Native receipt: six tests, eight intended assertions, 17.900s, exit 1; note-control receipt: four tests, two historical denial failures, both controls pass, 48.969s, exit 1. No errors/skips. Reviewer inspected receipts without rerunning tests or modifying files. Downstream assertions remain unexecuted until GREEN; no implementation or live verdict is implied.

### Initial native-entry test findings

Fresh code-reviewer `gpt-6.1-sol/high` reviewed integrated `5273cfd353fd46e3d1582d71c3fcbc5e58a3248e`, authored test-only `efa6da649b65585d939c1b88e2c369af327b2168`, against `c58af6db4f41b0acc88c6ef1bb5f053d6f561c1b`. Exact reviewed paths: `tests/test_same_agent_worktree.py`, `tests/test_install.py` and IMPLEMENTATION-SUMMARY. No tests rerun, edits, provider writes, children or commits.

**Fresh RED is valid:** the actual installed aggregate reaches the missing model-visible native continuation assertion before proposed files/verbs. Six tests report eight assertion failures, no setup/import/unknown-verb errors. Historical denial failures are distinct. Downstream real-Git/SIMULATED host steps have not executed and are not live movement proof. Both-host ordinary-note create/update controls are meaningful reported evidence.

Production remains **HOLD** for two bounded test-contract blockers:

- **CR-01:** simulated existing-session proof equates immutable historical session base with current HEAD. Capture actual pre-entry target HEAD separately; add committed source work to both ordinary phase/quick fixtures and preserve base/ownership while fresh reads observe that work.
- **CR-02:** actual editing aggregate does not receive the anchored original `CLAUDE_PROJECT_DIR` environment, although runtime/creation subprocesses do. Pass an explicit override through the real pipeline helper for every simulated Claude edit, including the rebuilt destination edit; verify the anchored variable differs from the moved default cwd.

Both findings map to existing issue98 boundaries, especially T-AW-03, without new identities. Corrections, refreshed receipts and bounded independent recheck precede production. No implementation or live acceptance verdict is given.

## Historical preparation-only RED gate

Reviewer role/model: code-reviewer, gpt-6.1-sol/high. Read-only inspection; no tests rerun, edits, provider writes or cleanup.

- Initial reviewed141497912e832ee418a78f7f01c7da2a8f273076 against26969d7: genuine installed aggregate RED, not missing/setup/unknown-verb failure.
- CR-01 BLOCKER required an external plain temporary PR-body/task-note control through both host aggregates, with actual fake bytes and unchanged worktree/preparation state.
- IN-01 INFO requested grounded Codex apply_patch/tool_input.command coverage rather than claiming it from only Write/file_path.
- Corrected reviewed38b7b1c4365561fb50d72d37f145053b243889e8: only tests/test_install.py and IMPLEMENTATION-SUMMARY.md changed; no production edits. **Clean; zero blockers/warnings/INFO.**
- Corrected recorded execution: Python3.13 `-m unittest discover -s tests -p test_install.py -k prewrite -v`; exit1, four tests,46.432s. Claude and Codex each fail the intended aggregate-denial assertion. In-repository scratchpad and external OS-temp controls pass on both host fixtures. Their actual fake mutations and unchanged state are asserted.
- The narrowed plain, unlinked OS-temp control grants no arbitrary external-write exemption. Other matrix families remain future implementation/GREEN evidence.

The test gate is released. PLAN/MATRIX alignment requires its separate bounded phase-checker verdict before production. This receipt gives no implementation, live-host or merge verdict. Findings map to existing planned issue98 boundaries, preserving threat identities.
