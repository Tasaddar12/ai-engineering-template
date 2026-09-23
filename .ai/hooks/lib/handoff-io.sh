#!/usr/bin/env bash
# Handoff record IO shared by the context-handoff hook. Sourced, never executed.
#
# A handoff is the record a fresh subagent reads to pick up abandoned work. It
# is deliberately NOT a planning document: it is local, ephemeral, gitignored
# and deleted the moment it is consumed. The committed record of what a plan
# did remains its SUMMARY.md -- a handoff only says where the previous attempt
# stopped and what is left.
#
# Every function here fails OPEN. A hook that cannot read a config file, parse
# a transcript or write a marker must not block the tool call it rides on:
# losing a handoff costs a re-read, blocking the agent costs the session.

HANDOFF_SCHEMA=1

# Python does the structural work (YAML config, JSONL transcripts). Without it
# the hook degrades to silence rather than guessing -- which is the safe
# direction, and exactly why the interpreter is PROBED rather than merely
# located.
#
# `command -v python3` answering yes is not the same as an interpreter that
# runs. On Windows the name routinely resolves to a Microsoft Store
# execution-alias stub that prints nothing and exits, and a CI runner can put a
# python on PATH under a name this cascade did not try. Either way the old
# cascade bound HANDOFF_PY to something that produced no output, every function
# below returned empty, and the hook went quiet for a reason nothing reported:
# occupancy was never measured, no handoff was ever written, and the suite that
# would have caught it passed vacuously because the hook is meant to be silent
# when it cannot measure.
#
# `py` is the Windows launcher, which is present on machines where the bare
# names are not. The probe costs one process at source time, once.
if [[ -z "${_HOOK_PY+set}" ]]; then
  _HOOK_PY=""
  for _hook_candidate in python3 python py; do
    if command -v "$_hook_candidate" >/dev/null 2>&1        && [[ "$("$_hook_candidate" -c 'print(1)' 2>/dev/null)" == 1* ]]; then
      _HOOK_PY="$_hook_candidate"
      break
    fi
  done
  unset _hook_candidate
fi
HANDOFF_PY="$_HOOK_PY"

# A path spelled the way the interpreter can open it.
#
# Under Git Bash the shell and a native Windows python disagree about what a
# path is: bash resolves /tmp/x, and python resolves it against the current
# drive, where it does not exist. MSYS usually rewrites such an argument on the
# way to a native binary, but that conversion is a heuristic and the
# environment can switch it off -- and when it does not happen, `[[ -f ]]` says
# yes, open() says no, and the measurement comes back empty with nothing
# reported. cygpath is the authority where it exists; everywhere else the path
# is already native and passes straight through.
handoff_native_path() {
  [[ -n "${1-}" ]] || return 0
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -m -- "$1" 2>/dev/null || printf '%s' "$1"
  else
    printf '%s' "$1"
  fi
}

handoff_root() {
  git rev-parse --show-toplevel 2>/dev/null || printf '%s' "${CLAUDE_PROJECT_DIR:-$PWD}"
}

handoff_dir() {
  printf '%s/.planning/handoffs' "$(handoff_root)"
}

# A session id reaches the filesystem as a filename, so anything that could
# escape the directory disqualifies it entirely rather than being scrubbed --
# a scrubbed id can collide with a different session's real one.
handoff_slug() {
  case "$1" in
    ""|*[/\]*|*..*) return 1 ;;
  esac
  printf '%s' "$1"
}

_HANDOFF_CONFIG_PY='
import sys, re

path = sys.argv[1]
try:
    text = open(path, encoding="utf-8").read()
except Exception:
    text = ""

data = {}
try:
    import yaml
    loaded = yaml.safe_load(text) or {}
    if isinstance(loaded, dict):
        data = loaded
except Exception:
    data = {}


def dotted(node, key, default):
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node if isinstance(node, (int, float)) and not isinstance(node, bool) else default


def scanned(key, default):
    """Regex fallback for a PyYAML-less environment. Top-level or one-level nested."""
    parts = key.split(".")
    if len(parts) == 1:
        found = re.search(r"(?m)^%s:[ \t]*(\d+)[ \t]*$" % re.escape(parts[0]), text)
        return int(found.group(1)) if found else default
    block = re.search(r"(?ms)^%s:[ \t]*$\n(.*?)(?=^\S|\Z)" % re.escape(parts[0]), text)
    if not block:
        return default
    found = re.search(r"(?m)^[ \t]+%s:[ \t]*(\d+)[ \t]*$" % re.escape(parts[1]), block.group(1))
    return int(found.group(1)) if found else default


window = dotted(data, "context_window", None)
percent = dotted(data, "handoff.context_percent", None)
tokens = dotted(data, "handoff.context_tokens", None)
if window is None:
    window = scanned("context_window", 200000)
if percent is None:
    percent = scanned("handoff.context_percent", 60)
if tokens is None:
    tokens = scanned("handoff.context_tokens", 250000)

# Whichever comes first. A percentage of a small window is the binding limit on
# a 200k host; the absolute ceiling binds on a 1M one.
by_percent = int(float(window) * float(percent) / 100.0)
limit = min(by_percent, int(tokens))
# Binary stdout: text mode appends a CR on Windows, which rides into the
# last field the caller reads and breaks every numeric test against it.
sys.stdout.buffer.write(
    ("%d %d %d %d\n" % (limit, int(window), int(percent), int(tokens))).encode("utf-8"))
'

# Echoes: "<threshold_tokens> <context_window> <percent> <absolute_ceiling>"
handoff_limits() {
  [[ -n "$HANDOFF_PY" ]] || { printf '120000 200000 60 250000'; return 0; }
  "$HANDOFF_PY" -c "$_HANDOFF_CONFIG_PY" \
    "$(handoff_native_path "$(handoff_root)/.planning/config.yaml")" 2>/dev/null \
    || printf '120000 200000 60 250000'
}

_HANDOFF_USAGE_PY='
import sys, io, json

path = sys.argv[1]


def totals(node):
    """Every token total this record exposes, whatever host wrote it.

    Two shapes, matched STRUCTURALLY rather than by wrapper name:
      * Claude Code    -- a usage block carrying input_tokens and friends. The
                          four fields together are what /context reports, so
                          they are summed, not maxed.
      * Codex rollout  -- a TokenUsageRecord carrying thread_token_usage with a
                          total_tokens. The serde spelling of the wrapper has
                          changed upstream before; the inner field has not.
    """
    found = []
    if isinstance(node, dict):
        if isinstance(node.get("input_tokens"), (int, float)):
            found.append(
                (node.get("input_tokens") or 0)
                + (node.get("cache_creation_input_tokens") or 0)
                + (node.get("cache_read_input_tokens") or 0)
                + (node.get("output_tokens") or 0)
            )
        inner = node.get("thread_token_usage")
        if isinstance(inner, dict) and isinstance(inner.get("total_tokens"), (int, float)):
            found.append(inner["total_tokens"])
        for value in node.values():
            found.extend(totals(value))
    elif isinstance(node, list):
        for value in node:
            found.extend(totals(value))
    return found


# The LAST line that reports anything wins: occupancy is a current reading, not
# a running sum, and a compaction lowers it. Scanning forward and keeping the
# last match costs one pass and survives interleaved non-usage records.
latest = None
try:
    with io.open(path, "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                record = json.loads(line)
            except Exception:
                continue
            seen = [int(value) for value in totals(record) if value and value > 0]
            if seen:
                latest = max(seen)
except Exception:
    latest = None

sys.stdout.buffer.write(
    (("%d" % latest) if latest is not None else "").encode("utf-8") + b"\n")
'

# Echoes the transcript's latest token occupancy, or nothing when unavailable.
handoff_used_tokens() {
  [[ -n "$HANDOFF_PY" && -n "${1:-}" && -f "$1" ]] || return 0
  "$HANDOFF_PY" -c "$_HANDOFF_USAGE_PY" "$(handoff_native_path "$1")" 2>/dev/null || true
}


_HANDOFF_PLAN_PY='
import sys, io, json, re

# The plan a subagent was working on, recovered from its own transcript.
#
# Claude names the plan in the dispatch prompt, which worktree-guard.sh reads at
# PreToolUse and records to the active stack. Codex dispatches through
# SubagentStart/SubagentStop rather than through a tool call, so there is no
# PreToolUse to record -- but its SubagentStop hands over
# `agent_transcript_path`, and the prompt that named the plan is the first
# thing in it.
#
# Strings are matched AFTER JSON decoding, never against the raw line. A
# transcript spells a Windows path with escaped separators on the wire, and a
# regex run over that undecoded text captures the escapes as literal
# backslashes and yields a path that matches no file on disk.

PATTERN = re.compile("[A-Za-z0-9_." + chr(92) * 2 + "/-]*"
                     "[0-9]{2}(?:[.][0-9]+)?-[0-9]{2}-PLAN[.]md")


def strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            for item in strings(value):
                yield item
    elif isinstance(node, list):
        for value in node:
            for item in strings(value):
                yield item


found = ""
try:
    with io.open(sys.argv[1], "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line.startswith(("{", "[")):
                continue
            try:
                record = json.loads(line)
            except Exception:
                continue
            for text in strings(record):
                match = PATTERN.search(text)
                if match:
                    # The dispatch prompt is the earliest thing in the
                    # transcript, so the first match is the assigned plan and
                    # not one mentioned later in passing.
                    found = match.group(0).replace(chr(92), "/")
                    # Codex reports an absolute checkout path; the SUMMARY
                    # lookup downstream joins against cwd, so anything above
                    # .planning/ is cut rather than joined twice.
                    marker = ".planning/"
                    cut = found.find(marker)
                    if cut > 0:
                        found = found[cut:]
                    break
            if found:
                break
except Exception:
    found = ""

sys.stdout.buffer.write(found.encode("utf-8") + chr(10).encode("utf-8"))
'

# Echoes the plan path named in a subagent transcript, or nothing.
handoff_plan_in_transcript() {
  [[ -n "$HANDOFF_PY" && -n "${1:-}" && -f "$1" ]] || return 0
  "$HANDOFF_PY" -c "$_HANDOFF_PLAN_PY" "$(handoff_native_path "$1")" 2>/dev/null || true
}

# --- record writing -----------------------------------------------------------
#
# One Python process per record, not one per field. The obvious shape -- a
# printf per key with a json_str helper escaping each value -- spawns an
# interpreter thirteen times for a single handoff, which on Windows costs more
# than the hook's entire timeout budget. Keys and values go over argv instead
# and Python assembles, coerces and writes the file in one pass.

_HANDOFF_RECORD_PY='
import sys, os, json, datetime

path = sys.argv[1]
pairs = sys.argv[2:]

# Fields the orchestrator does arithmetic or comparisons on. An empty value
# becomes null rather than "" so a consumer can test it numerically.
NUMERIC = {"used_tokens", "threshold_tokens", "context_window", "context_percent"}
# Fields an empty value must not erase. An exit record knows no occupancy and
# a threshold record knows no plan; whichever is written second keeps what the
# first one learned. Git state is always the current reading, so it is not here.
KEEP_WHEN_EMPTY = NUMERIC | {"agent", "plan", "summary"}

previous = {}
try:
    with open(path, encoding="utf-8") as handle:
        loaded = json.load(handle)
    if isinstance(loaded, dict):
        previous = loaded
except Exception:
    previous = {}

# Start from the previous record, not from nothing. The agent adds its digest
# -- findings, files read, remaining work -- with `handoff.write` into this same
# file, and the hook refreshes it on every later tool use; rebuilding it from
# the hook fields alone would erase the digest one tool call after it was written.
record = dict(previous)
for index in range(0, len(pairs) - 1, 2):
    key, value = pairs[index], pairs[index + 1]
    if value == "" and key in KEEP_WHEN_EMPTY and previous.get(key) is not None:
        continue
    if key in NUMERIC:
        try:
            record[key] = int(value) if value != "" else None
        except ValueError:
            record[key] = None
    else:
        record[key] = value if value != "" else None

now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
record["schema"] = 1
record["status"] = "pending"
# A refreshed record keeps the moment the attempt first crossed the line. That
# is the timestamp that orders handoffs for the orchestrator; "updated_at" only
# says how current the numbers are.
record["created_at"] = previous.get("created_at") or now
record["updated_at"] = now

temporary = path + ".tmp"
try:
    with open(temporary, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temporary, path)
except Exception:
    try:
        os.unlink(temporary)
    except Exception:
        pass
'

# handoff_record <file> <key> <value> [<key> <value> ...]
handoff_record() {
  local file="$1"
  shift
  [[ -n "$HANDOFF_PY" ]] || return 0
  mkdir -p "${file%/*}" 2>/dev/null || return 0
  "$HANDOFF_PY" -c "$_HANDOFF_RECORD_PY" "$(handoff_native_path "$file")" "$@" 2>/dev/null
  return 0
}

_HANDOFF_ACTIVE_PY='
import sys, json

path, agent, plan, at = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
line = json.dumps({"agent": agent or None, "plan": plan or None, "at": at},
                  ensure_ascii=False)
try:
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(line + "\n")
except Exception:
    pass
'

# handoff_append_active <file> <agent> <plan>
handoff_append_active() {
  [[ -n "$HANDOFF_PY" ]] || return 0
  mkdir -p "${1%/*}" 2>/dev/null || return 0
  "$HANDOFF_PY" -c "$_HANDOFF_ACTIVE_PY" "$(handoff_native_path "$1")" "${2-}" "${3-}" \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')" 2>/dev/null
  return 0
}
