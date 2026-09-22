#!/usr/bin/env bash
# Agent role classification shared by the hooks. Sourced, never executed.
#
# Subagents that write files. A read-only role (researcher, verifier,
# code-reviewer, doc-verifier, codebase-mapper, phase-checker,
# integration-checker) has nothing to isolate and leaves no half-finished plan
# behind, so neither the isolation guard nor the handoff hook acts on one.
#
# This lives here rather than in either hook because both of them need the same
# answer and they reach it from opposite directions: worktree-guard.sh sees a
# dispatch before it runs, context-handoff.sh sees a subagent after it stops. A
# role added to one copy and not the other is a silent hole in whichever half
# was missed.
WRITE_CAPABLE_AGENTS="coder doc-writer debugger"

# True when $1 is a role that writes files.
agent_writes_files() {
  case " $WRITE_CAPABLE_AGENTS " in
    *" ${1-} "*) return 0 ;;
    *) return 1 ;;
  esac
}
