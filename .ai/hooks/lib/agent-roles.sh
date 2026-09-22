#!/usr/bin/env bash
# Agent role classification shared by the hooks. Sourced, never executed.
#
# Subagents that execute a plan and write files. Every other role (researcher,
# phase-preparer, codebase-mapper, verifier, code-reviewer, doc-verifier,
# phase-checker, integration-checker) needs no worktree of its own and leaves
# no half-finished plan behind, so the isolation guard never acts on one and
# the handoff hook writes no exit record for one.
#
# This lives here rather than in either hook because both of them need the same
# answer and they reach it from opposite directions: worktree-guard.sh sees a
# dispatch before it runs, context-handoff.sh sees a subagent after it stops. A
# role added to one copy and not the other is a silent hole in whichever half
# was missed.
WRITE_CAPABLE_AGENTS="coder doc-writer debugger"

# Roles whose whole output is one assigned artifact -- RESEARCH.md, a codebase
# map, a phase's plans -- rather than a plan executed to a SUMMARY. They are
# deliberately NOT write-capable above: that list is also the isolation
# guard's, and these roles work in the orchestrator's session checkout.
#
# What sets them apart is what a context limit should make them do. A coder
# stopped mid-slice hands the rest of the plan on. An artifact role that stops
# has produced nothing, so the limit tells it to converge instead: write the
# artifact from what it already has and return it as partial.
ARTIFACT_AGENTS="researcher codebase-mapper phase-preparer"

# Roles that check work that already exists and report on it.
REVIEW_AGENTS="verifier code-reviewer doc-verifier phase-checker integration-checker"

# True when $1 is a role that writes files.
agent_writes_files() {
  case " $WRITE_CAPABLE_AGENTS " in
    *" ${1-} "*) return 0 ;;
    *) return 1 ;;
  esac
}

# True when $1 is a role whose output is a single assigned artifact.
agent_writes_artifact() {
  case " $ARTIFACT_AGENTS " in
    *" ${1-} "*) return 0 ;;
    *) return 1 ;;
  esac
}

# The kind of stop a context limit should ask of role $1:
#   plan      executes a plan to a SUMMARY; hands the remainder on
#   artifact  owns one artifact; converges on it and returns it as partial
#   review    reports on existing work; reports what it reached
#   unknown   no role this template defines -- the root session, a host that
#             does not say which subagent is calling, or a foreign agent
# A plugin-scoped name (`plugin:name:role`) is classified by its last segment.
agent_stop_kind() {
  local role="${1-}"
  role="${role##*:}"
  if [[ -n "$role" ]] && agent_writes_files "$role"; then
    printf 'plan'
  elif [[ -n "$role" ]] && agent_writes_artifact "$role"; then
    printf 'artifact'
  elif [[ -n "$role" && " $REVIEW_AGENTS " == *" $role "* ]]; then
    printf 'review'
  else
    printf 'unknown'
  fi
}
