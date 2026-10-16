---
phase: maintenance-issue87-auto-worktree
researched: "2026-10-16"
input_revision: b3cefa0c6436ddd5f606b5a34523c8e269a5ceac
status: complete
requirements: [ISSUE87]
issue_refs: [87, 98]
---

# Codex enforcement capability evidence

Repository researcher: gpt-6.1-sol/high. This is capability evidence before implementation, not a GREEN result for the proposed generated adapter.

## Installed runtime

The existing Windows installation reports `codex-cli 0.162.0-alpha.17.2`. Its feature output reports hooks and worktrees stable/enabled. No installation, account credential copy, external model request or existing desktop task mutation was performed.

The installed app-server generated its experimental JSON schema successfully. Its 170 request methods include `hooks/list`, with no worktree handoff endpoint. `TurnStartParams.cwd` explicitly applies to this and subsequent turns; active-turn `TurnSteerParams` cannot change cwd. An authenticated controlling host can use persistent same-thread defaults, but hook JSON alone supplies no controller.

## Actual native startup probe

A fresh temporary Git fixture had committed HEAD 084ce4c7b5d2dad367a2358f49d73fc6184f9b7a. Native `codex exec --worktree --json -C <fixture> --sandbox read-only -m probe87` exited zero using one canned loopback response. Git registered a second checkout under the isolated temporary CODEX_HOME, detached at that same HEAD. Both the actual outgoing environment context and persisted session metadata named that destination as cwd and workspace root.

This proves native destination defaults for a new run. It does not register an ordinary phase/quick unit and does not move an existing active caller. Detached linked trees must not receive a blanket exception.

## Actual synchronous hook probe

With an isolated temporary CODEX_HOME, sanitized child environment and vetted temporary hook configuration, a local canned Responses provider emitted an exec_command call. Codex dispatched PreToolUse as canonical tool_name Bash with tool_input.command. The actual hook router returned `Command blocked by PreToolUse hook: PROBE87_NATIVE_DENIAL`; the next provider request contained the denial as function_call_output. The command did not execute. SessionStart also executed. CLI exit was zero and two local canned responses were consumed.

The probe used an invocation-only native trust bypass solely for its vetted temporary fixture. This is not a production trust policy. Earlier attempts did not capture hooks and received a separate machine-policy denial; their different inherited environment and Windows quoting confound the cause. They are not passing hook evidence. An incidental featured-plugin cache request received 401; subsequent fixtures should disable plugins.

Host-local evidence is retained under the temporary codex87-capability-5b752dbfe8894db38c2dd65872b1417f directory: generated schemas, startup-worktree stdout/request capture, sanitized-hook stdout/stderr, sanitized-mock-requests.json and hook-live-capture.jsonl. These files contain no copied account credentials and are not public deliverable links. Implementation must produce its own actual generated-adapter evidence.

## Supported design boundary

Generate a launcher which selects an existing runtime-owned phase/quick unit before starting native Codex with its validated destination and invocation-scoped hooks enabled. Preserve global user settings, honor managed policy and reviewed hook trust, reject conflicting overrides and validate installed destination inputs. Add synchronous broad supported-tool guards plus startup/pre-prompt checks. Keep task notes and the advisory guard unchanged.

Official sources support local-tool denial and project hook configuration, but describe exceptions and fail-open conditions. Existing write_stdin sessions are not re-hooked; specialized paths can opt out; hook errors, malformed outputs and timeouts can fail open. The result is a scoped guardrail, not a complete security boundary.

The native idle `/worktree` command can continue the current conversation, while CLI `--worktree` starts a new/forked run. Neither establishes automatic in-flight movement by a hook. A separate authenticated host controller would be needed for that integration.

## Follow-up native trust and effective feature evidence

After the first runtime slice, an isolated temporary native CLI review trusted a known hook through the supported review UI. A separate app-server read reported enabled=true, trustStatus=trusted and no errors/warnings. No bypass, model turn or private trust-store edit was used. CLI exit1 followed intentional Ctrl+C after approval; it is not a model-run pass. The native UI also exposed “Trust all and continue”; the observed fixture contained one hook. B must review its actual generated definitions in its own destination and temporary home.

The same trusted fixture with temporary user features.hooks=false produced:

| Invocation | config/read config.features.hooks | Native features list | hooks/list |
|---|---|---|---|
| --enable hooks | true | hooks stable true | Enabled/trusted, same definition hash |
| --disable hooks | false | hooks stable false | Empty |

The config/read origin was sessionFlags, so the read includes invocation overrides and can check effective enabling without rewriting stored user=false. Both native processes exited0; no thread, turn or model call occurred. The temporary config was restored byte-for-byte. Disabled execution retaining enabled/trusted catalog metadata was not reproduced. The supported configRequirements/read response has nullable requirements and a featureRequirements boolean map; both actual reads returned requirements=null, so managed override behavior was not exercised.

Receipts and exact sources remain in the capability directory: hooks-feature-differential.py, hooks-feature-differential-results.json, feature-enable/disable full RPC/config/hooks/requirements outputs, and interactive-trust/native-control-receipt.json plus trust-approval-receipt.json. These prove capability only; generated-adapter and positive production-launch acceptance remain pending B.

## References

- [Hooks and trust](https://learn.chatgpt.com/docs/hooks)
- [Developer commands and worktree modes](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
- [App-server protocol and persistent turn defaults](https://learn.chatgpt.com/docs/app-server)
- [Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
- Current repository source boundary: .ai/install.py, .ai/runtime/lib/prewrite.py and .ai/references/same-agent-worktree.md at the input revision.
