<purpose>
Inspect a user-selected pinned source revision, display its complete changes and file transaction, preserve custom files, and apply only the reviewed update with backups and rollback.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>
**If `response_language` is configured:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be presented in that language. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated.

<step name="get_installed_version">
Read the actual pinned installation manifest. Derive `PREFERRED_CONFIG_DIR` from the invoking `execution_context` path when it identifies an installed namespace, and infer `PREFERRED_RUNTIME` only from an actual `.claude` or `.codex` namespace. Leave either empty if unavailable.

```bash
_engineer_identity_ok() {
  [ -f "$1" ] || return 1
  [ "$(sh "$1" query runtime-identity --pick packageName --raw 2>/dev/null)" = "engineer-runtime" ]
}
_engineer_select() {
  for _engineer_candidate do
    if _engineer_identity_ok "$_engineer_candidate"; then
      ENGINEER_RUN="$_engineer_candidate"
      return 0
    fi
  done
  return 1
}
if [ -n "${ENGINEER_RUN:-}" ]; then
  _engineer_identity_ok "$ENGINEER_RUN" || {
    printf '%s\n' "ERROR: ENGINEER_RUN does not identify engineer-runtime: $ENGINEER_RUN" >&2
    exit 1
  }
else
  _engineer_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
  _engineer_runtime_root=${RUNTIME_DIR:-$_engineer_root}
  _engineer_path_candidate=$(command -v engineer_run 2>/dev/null || true)
  _engineer_select \
    "$_engineer_root/engineer/bin/engineer_run" \
    "$_engineer_runtime_root/engineer/bin/engineer_run" \
    "$_engineer_root/.claude/engineer/bin/engineer_run" \
    "$_engineer_root/.codex/engineer/bin/engineer_run" \
    "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/engineer/bin/engineer_run" \
    "${CODEX_HOME:-$HOME/.codex}/engineer/bin/engineer_run" \
    "$_engineer_path_candidate" || {
    printf '%s\n' 'ERROR: No engineer-runtime launcher was found. Install the Claude or Codex workflow runtime or set ENGINEER_RUN.' >&2
    exit 1
  }
fi
export ENGINEER_RUN
engineer_run() {
  sh "$ENGINEER_RUN" "$@"
}
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  _engineer_path_escaped=$(printf '%s' "${ENGINEER_RUN%/*}" | sed 's/[\\`"$]/\\&/g')
  printf 'export PATH="%s:$PATH"\n' "$_engineer_path_escaped" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true
fi
UC_ARGS=()
[ -z "${PREFERRED_CONFIG_DIR:-}" ] || UC_ARGS+=(--config-dir "$PREFERRED_CONFIG_DIR")
[ -z "${PREFERRED_RUNTIME:-}" ] || UC_ARGS+=(--runtime "$PREFERRED_RUNTIME")
UC=$(engineer_run query update-context "${UC_ARGS[@]}") || exit $?
  uc_field() {
  engineer_run query json.get --payload "$UC" --field "$1" --raw
  }
[ "$(uc_field resolved)" = true ] || { printf '%s\n' "$UC" >&2; exit 1; }
INSTALLED_VERSION=$(uc_field installedVersion) || exit $?
INSTALL_SCOPE=$(uc_field scope) || exit $?
TARGET_RUNTIME=$(uc_field runtime) || exit $?
ENGINEER_DIR=$(uc_field config_dir) || exit $?
UPDATE_TARGET=$(uc_field target) || exit $?
RUNTIME_DIR="$ENGINEER_DIR"
UPDATER="$RUNTIME_DIR/bin/update.py"
[ -f "$UPDATER" ] || { printf '%s\n' 'ERROR: pinned Python updater is missing; preserve this installation and restore the selected source.' >&2; exit 1; }
printf '%s\n' "$INSTALLED_VERSION" "$INSTALL_SCOPE" "$TARGET_RUNTIME" "$ENGINEER_DIR"
```

An absent, malformed or ambiguous manifest cannot establish an update target. Preserve the diagnostic and stop. Select an actual config directory when multiple installations match; do not guess a runtime, source, version or target. `update-context` owns this manifest projection.
</step>

<step name="parse_update_channel">
Select the existing local source repository and exact ref from the user's request or actual installed provenance. Preserve authorization already given; ask only for missing source/ref inputs. Do not choose a package or moving release channel.

```bash
UPDATE_SOURCE="${UPDATE_SOURCE:-$(uc_field source_path)}"
: "${UPDATE_SOURCE:?Select the actual local source repository}"
: "${UPDATE_REF:?Select the actual user-requested commit, branch or tag}"
UPDATE_HOST="$TARGET_RUNTIME"
case "$INSTALL_SCOPE" in
  LOCAL|local) UPDATE_SCOPE=--local ;;
  GLOBAL|global) UPDATE_SCOPE=--global ;;
  *) printf '%s\n' 'ERROR: installed scope is unresolved' >&2; exit 1 ;;
esac
TEXT_MODE=$(engineer_run query config-get workflow.text_mode --raw) || exit $?
```

The selected repository must already exist. Do not fetch, substitute a source or move an unrelated checkout. The next step captures the requested ref as an immutable SHA before any target mutation.
</step>

<step name="check_latest_version">
Resolve and capture the selected source revision. The installed revision comes from the actual manifest, not an inferred package version.

```bash
UPDATE_PIN=$(git -C "$UPDATE_SOURCE" rev-parse --verify "$UPDATE_REF^{commit}") || exit $?
case "$UPDATE_PIN" in ''|*[!0-9a-fA-F]*) printf '%s\n' 'ERROR: selected ref did not resolve to a commit' >&2; exit 1 ;; esac
[ "${#UPDATE_PIN}" -eq 40 ] || { printf '%s\n' 'ERROR: expected a full source commit SHA' >&2; exit 1; }
UPDATE_CHANGES=$(engineer_run query update.changes --source "$UPDATE_SOURCE" --from "$INSTALLED_VERSION" --ref "$UPDATE_PIN") || exit $?
printf '%s\n' "$UPDATE_CHANGES"
```

Failure to resolve either revision stops the update. Preserve the source and installed files; never replace an unresolved pin with a package-manager fallback or another revision.
</step>

<step name="compare_versions">
Compare the actual installed source SHA with the selected immutable SHA. Semver ordering cannot establish whether a custom checkout should be replaced.

```bash
if [ "$INSTALLED_VERSION" = "$UPDATE_PIN" ]; then
  printf '%s\n' "The installed source revision already equals $UPDATE_PIN."
  printf '%s\n' 'No update was applied. Use an explicit reviewed repair plan if the installed files need repair.'
  exit 0
fi
printf 'Installed revision: %s\nSelected revision: %s\n' "$INSTALLED_VERSION" "$UPDATE_PIN"
```

Continue only toward this selected pin. Display the exact changes for an older or divergent selection; never silently change the user's chosen revision.
</step>

<step name="show_changes_and_confirm">
Display the complete pinned Git changes and exact file transaction before any update.

```bash
CHANGELOG_PREVIEW="$UPDATE_CHANGES"
UPDATE_PLAN=$(mktemp "${TMPDIR:-/tmp}/engineer-update-plan-XXXXXX.json") || exit $?
UPDATE_PLAN_JSON=$(python -I "$UPDATER" --source "$UPDATE_SOURCE" --ref "$UPDATE_PIN" --target "$UPDATE_TARGET" --host "$UPDATE_HOST" "$UPDATE_SCOPE" --plan "$UPDATE_PLAN") || exit $?
REVIEWED_PLAN_SHA256=$(engineer_run query json.get --payload "$UPDATE_PLAN_JSON" --field reviewed_plan_sha256 --raw) || exit $?
printf '%s\n' "$UPDATE_PLAN_JSON"
printf 'Exact reviewed plan: %s\nPlan SHA256: %s\n' "$UPDATE_PLAN" "$REVIEWED_PLAN_SHA256"
```

Inspect every conflict, migration finding, managed write, preserved custom path and backup action. Unresolved findings block apply. Do not edit the plan to hide them. Approval applies only to the exact reviewed plan bytes. If inputs or target files change, generate and review a fresh plan. Do not ask again for authorization already supplied for this exact transaction.

Display the complete preview and obtain any still-required authorization for this exact transaction:

```
## Engineer Update Available

**Installed:** {INSTALLED_VERSION}
**Selected revision:** {UPDATE_PIN}

### What's New

---

{CHANGELOG_PREVIEW}

---

The updater applies only the exact reviewed transaction. Unmanaged files and conflicting local edits are preserved. Managed changes receive byte-preserving backups and a rollback journal.

(Paths are relative to detected runtime install location:
global: `~/.claude/` or `~/.codex/`
local: `./.claude/` or `./.codex/`)

Your custom files in other locations are preserved:
- Custom commands not in `commands/` ✓
- Custom agents not prefixed with `engineer-` ✓
- Custom hooks ✓
- Your CLAUDE.md files ✓

The preview identifies locally modified managed files. Preserve them or explicitly select reviewed conflict resolutions; original bytes remain in the transaction backup.
```

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `TEXT_MODE` from the actual configuration is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex) where `AskUserQuestion` is not available.
Use AskUserQuestion:
- Question: "Proceed with update?"
- Options:
  - "Yes, update now"
  - "No, cancel"

**If user cancels:** Exit.
</step>


<step name="run_update">
Apply only the exact reviewed plan once the existing update authorization or explicit answer covers this pin and transaction.

```bash
: "${UPDATE_PLAN:?The complete pinned preview must exist before apply}"
: "${REVIEWED_PLAN_SHA256:?The SHA256 of the exact reviewed plan bytes is required}"
UPDATE_RESULT=$(python -I "$UPDATER" --apply "$UPDATE_PLAN" --reviewed-plan-sha256 "$REVIEWED_PLAN_SHA256") || exit $?
printf '%s\n' "$UPDATE_RESULT"
UPDATE_BACKUP=$(engineer_run query json.get --payload "$UPDATE_RESULT" --field backup --raw) || exit $?
```

The updater rechecks the source pin, exporter digest, target hashes, manifest and exact reviewed bytes. Any drift stops mutation. It journals original bytes and file modes before writes and rolls back a failed transaction. Preserve its error and backup path if recovery is needed; do not retry an uncertain transaction blindly.

Do not clear unrelated cache files, install a package, wipe managed directories or run a second installer. Successful installation does not establish runtime correctness; execution checks remain not executed.
</step>

<step name="display_result">
Report the actual update result: installed source revision, target, host, changed paths, preserved local files and returned backup directory. Identify blocked or deferred paths and unrun checks.

```bash
printf 'Updated source: %s\nTarget: %s\nBackup: %s\n' "$UPDATE_PIN" "$UPDATE_TARGET" "$UPDATE_BACKUP"
```

Ask the user to restart the host when needed to load changed commands. The complete pinned Git changes displayed before apply are the change record; do not invent a release version or use a moving changelog URL as evidence.
</step>


<step name="check_local_patches">
Inspect the returned transaction backup. Its journal records exact original bytes, modes and target-relative paths.

```bash
printf 'Preserved transaction backup: %s\n' "$UPDATE_BACKUP"
```

Do not automatically reapply locally modified managed files over the selected pin. Compare actual source, backed-up bytes and updated contracts; prepare exact reviewed resolutions. The user may keep the backup without changing the installation.

If rollback is required, first inspect the journal, ownership and current target state. With actual rollback authority, call the same pinned updater using the returned backup path:

```bash
python -I "$UPDATER" --target "$UPDATE_TARGET" --host "$UPDATE_HOST" --rollback "$UPDATE_BACKUP"
```

Rollback validates target ownership and refuses drift. Preserve its backup and diagnostic on failure; it cannot authorize deleting unrelated files or replacing later user changes.
</step>
</process>

<success_criteria>
- [ ] Installed version read correctly
- [ ] Selected source ref captured as a full immutable Git SHA
- [ ] Update skipped if already current
- [ ] Pinned changes and complete reviewed transaction displayed BEFORE update
- [ ] Exact writes, conflicts, preserved paths and recoverable backups shown
- [ ] User confirmation obtained
- [ ] Update executed successfully
- [ ] Restart reminder shown
</success_criteria>
