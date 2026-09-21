# Worktree path safety

Guards for an executor that writes files during a wave. The root pin runs in
**every** mode, isolated or not. The remaining two guards apply only in a
worktree.

---

## Root pin — runs in every mode

A sequential executor gets no spawn-time working-directory guarantee. If its
process directory resolves to a different checkout of the same repository — a
sibling worktree, a second clone — it will derive that checkout as its root and
commit there, silently. The pin closes that by comparing the executor's actual
root against one the **orchestrator** already validated, never against anything
the executor derives for itself.

**Executor contract:** if your prompt contains a `<project_root_pin>` block, run
its guard before your first write and again before every commit, in the same
directory as that write or commit. On FATAL, halt and report — moving commits
between checkouts is an orchestrator or human decision, never agent self-repair.
If your prompt contains no such block, emit one warning line and continue with
the guards below. **Never bind `{PINNED_ROOT}` yourself:** if this file reaches
you with the placeholder intact it is reference prose, not your pin.

**Orchestrator contract (build time):** copy the guard into the dispatched
prompt inside a `<project_root_pin>` block, substituting `{PINNED_ROOT}` with
the validated root, single-quoted — wrap it in `'…'` and escape any embedded
`'` as `'\''`. A path that cannot be quoted that way halts the phase rather than
shipping a pin that could mis-parse.

The comparison is git-vs-git on both sides. `git -C` resolves the pinned path to
its own repository's canonical toplevel in git's path representation, so symlink
aliases, trailing slashes and Windows drive-letter spellings compare equal by
construction. Shell `pwd -P` normalization does **not** match git's emission on
Windows — do not reintroduce it.

```bash
# Run before the first write and before every commit.
PINNED_ROOT='{PINNED_ROOT}'   # orchestrator substitution; the only valid source
PIN_STAGE=''
PIN_DIAG=''
pin_fail() {
  echo "FATAL: executor root does not match the orchestrator-supplied root pin." >&2
  echo "  Pinned root: ${PINNED_ROOT:-<empty or unexpanded>}" >&2
  echo "  Actual root: ${ACTUAL_ROOT:-<none>}" >&2
  echo "  Guard stage: ${PIN_STAGE:-<unset>}" >&2
  if [ -n "$PIN_DIAG" ]; then echo "  Diagnostic: $PIN_DIAG" >&2; fi
  echo "  No writes or commits are permitted from this checkout. HALT and report." >&2
  exit 1
}
# The backslash comparator is generated at runtime: a backslash written twice in
# a script does not survive the Windows command-line round-trip into bash (the
# doubled form arrives halved), which would silently rewrite the drive-form arm.
BS=$(printf '\134')
if [ -z "$BS" ]; then
  PIN_STAGE=form-gate
  PIN_DIAG='backslash comparator generation returned empty'
  pin_fail
fi
case "$PINNED_ROOT" in
  ''|'{PINNED_ROOT}') PIN_STAGE=pin-unbound; pin_fail ;;  # never warn-and-proceed
  /*) ;;                                                  # absolute POSIX form
  [A-Za-z]:/*|[A-Za-z]:"$BS"*) ;;                         # Windows drive form
  *) PIN_STAGE=form-gate; pin_fail ;;                     # relative: not trustworthy
esac
ACTUAL_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$ACTUAL_ROOT" ]; then
  PIN_STAGE=actual-capture
  PIN_DIAG="git rev-parse --show-toplevel failed: $(git rev-parse --show-toplevel 2>&1 1>/dev/null)"
  pin_fail
fi
PINNED_TL=$(git -C "$PINNED_ROOT" rev-parse --show-toplevel 2>/dev/null)
if [ -z "$PINNED_TL" ]; then
  PIN_STAGE=pinned-capture
  PIN_DIAG="git -C <pinned> rev-parse --show-toplevel failed: $(git -C "$PINNED_ROOT" rev-parse --show-toplevel 2>&1 1>/dev/null)"
  pin_fail
fi
if [ "$ACTUAL_ROOT" != "$PINNED_TL" ]; then
  PIN_STAGE=root-mismatch
  PIN_DIAG="actual=${ACTUAL_ROOT} pinned=${PINNED_TL}"
  pin_fail
fi
```

Every FATAL names its guard stage, and any failed git capture reports git's own
stderr, so a platform failure self-describes instead of surfacing as a bare
`Actual root: <none>`.

---

## Directory-drift sentinel — worktree mode

A prior shell call may have changed directory out of the worktree into the main
repository. When that happens `[ -f .git ]` is false — the main repository's
`.git` is a directory — which silently skips every worktree guard. The sentinel
captures the spawn-time toplevel and detects drift before each commit.

```bash
if [ -f .git ]; then   # a linked worktree has a .git FILE, not a directory
  WT_GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
  case "$WT_GIT_DIR" in
    *.git/worktrees/*)
      SENTINEL="$WT_GIT_DIR/phase-spawn-toplevel"
      [ ! -f "$SENTINEL" ] && git rev-parse --show-toplevel > "$SENTINEL" 2>/dev/null
      EXPECTED_TL=$(cat "$SENTINEL" 2>/dev/null)
      ACTUAL_TL=$(git rev-parse --show-toplevel 2>/dev/null)
      if [ -n "$EXPECTED_TL" ] && [ "$ACTUAL_TL" != "$EXPECTED_TL" ]; then
        echo "FATAL: working directory drifted from the spawn-time worktree root." >&2
        echo "  Spawn-time: $EXPECTED_TL" >&2
        echo "  Current:    $ACTUAL_TL" >&2
        echo "RECOVERY: cd \"$EXPECTED_TL\" before staging, then re-run the commit." >&2
        exit 1
      fi
      ;;
  esac
fi
```

---

## Absolute-path guard — worktree mode

An absolute path built from the **orchestrator's** working directory resolves to
the main repository, not the worktree. The write lands in the wrong directory,
`git commit` in the worktree sees a clean tree, and the work is silently lost.

**Prefer relative paths for every edit.** Where an absolute path is unavoidable,
derive it from `git rev-parse --show-toplevel` run *inside* the worktree — never
from a directory captured in the orchestrator's context.

```bash
WT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ "${ABS_PATH#"$WT_ROOT"}" = "$ABS_PATH" ]; then
  echo "WARNING: $ABS_PATH is outside the worktree ($WT_ROOT)" >&2
  echo "Use a relative path, or recompute the absolute path from WT_ROOT." >&2
fi
```

Adapted from `gsd-core/references/worktree-path-safety.md`; see
[THIRD-PARTY-NOTICES](../THIRD-PARTY-NOTICES.md).
