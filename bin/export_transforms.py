"""Pure, source-backed translations for retained workflow shell adapters.

Only recognized operations are rewritten. This module neither runs code nor
writes exports. Unknown JavaScript stays intact for the installer's refusal gate.
"""
from pathlib import PurePosixPath
import re
import shlex


def _quote(value):
    return shlex.quote(str(value).replace("\\", "/"))


def _quoted_end(text, start):
    quote = text[start]
    index = start+1
    while index < len(text):
        if text[index] == "\\" and quote == '"':
            index += 2
        elif text[index] == quote:
            return index+1
        else:
            index += 1
    return None


def _substitution_end(text, start):
    """Find a shell substitution boundary without evaluating its contents."""
    depth, index = 1, start
    while index < len(text):
        char = text[index]
        if char in "\"'":
            end = _quoted_end(text, index)
            if end is None:
                return None
            index = end
            continue
        if char == "\\":
            index += 2
            continue
        if char == "#" and (index == start or text[index-1].isspace()):
            newline = text.find("\n", index)
            index = len(text) if newline < 0 else newline+1
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def _argument(text, start):
    index = start
    while index < len(text) and text[index] in " \t":
        index += 1
    if index >= len(text):
        return None, start
    if text[index] in "\"'":
        end = _quoted_end(text, index)
        return (text[index:end], end) if end else (None, start)
    match = re.match(r"[^\s;|<>())]+", text[index:])
    return (match[0], index+len(match[0])) if match else (None, start)


def _assignments(text, command):
    """Translate the few assignments whose operation spans several readers."""
    pattern = re.compile(r"(?m)^([ \t]*)([A-Z_]+)=\$\(")
    replacements = []
    for match in pattern.finditer(text):
        end = _substitution_end(text, match.end())
        if end is None:
            continue
        body, name = text[match.end():end], match[2]
        if not re.search(r"\bnode\s+-e\s", body):
            continue
        replacement = None
        if name == "DEPTH_PAYLOAD" and all(token in body for token in ("flagDepth", "configDepth", "overrides", "repoRoot")):
            replacement = "printf '%s\\n' \"${REVIEW_FILES[@]}\" | "+command("json.depth-input")+" --flag-depth \"$DEPTH_OVERRIDE\" --config-depth \"$CONFIG_DEPTH\" --overrides \"$DEPTH_OVERRIDES\""
        elif name == "DEPTH_FIELDS" and all(token in body for token in ("matchedRule", "invalidFlagDepth", "downgraded")):
            replacement = "printf '%s' \"$DEPTH_JSON\" | "+command("json.depth-fields")+" --raw"
        elif name == "EVIDENCE_LIST" and all(token in body for token in ("reviewPath", "selection", "results")):
            replacement = ("_review_evidence=$(printf '%s' \"$DISPATCH_JSON\" | "+command("review.evidence")+") || exit $?\n"
                           "printf '%s' \"$_review_evidence\" | "+command("json.get")+" --field failures >&2\n"
                           "printf '%s' \"$_review_evidence\" | "+command("json.lines")+" --field review_paths --raw")
        elif name == "REVIEWER_CONTRIBUTIONS" and all(token in body for token in ("activeHooks", "fragment.inline", "capability_review_rules")):
            replacement = ("_review_rules=$(printf '%s' \"$REVIEWER_HOOKS_JSON\" | "+command("review.contributions")+" --raw) || exit $?\n"
                           "if [ -n \"$_review_rules\" ]; then printf '<capability_review_rules>\\n%s\\n</capability_review_rules>\\n' \"$(printf '%s' \"$_review_rules\" | sed 's#</capability_review_rules>#<\\/capability_review_rules>#g')\"; fi")
        elif name == "HAS_STATUS" and "match[1]" in body and "status:" in body:
            variable = "FIX_REPORT_PATH" if "FIX_REPORT_PATH" in body else "REVIEW_PATH"
            replacement = ("if [ \"$("+command("review.disposition")+" --report \"$"+variable+"\" --pick has_status --raw)\" = true ]; then printf valid; else printf invalid; fi")
        elif name in ("FRONTMATTER", "FIX_FRONTMATTER") and "match[1]" in body:
            variable = "FIX_REPORT_PATH" if "FIX_REPORT_PATH" in body else "REVIEW_PATH"
            replacement = command("review.frontmatter")+" --report \"$"+variable+"\" --raw"
        if replacement is not None:
            replacements.append((match.start(), end+1, match[1]+name+"=$("+replacement+")"))
    for start, end, replacement in reversed(replacements):
        text = text[:start]+replacement+text[end:]
    return text


def _node_calls(text, command, source):
    """Recognize concrete JSON/frontmatter readers, not arbitrary JS programs."""
    pattern = re.compile(r"\bnode[ \t]+-[ep][ \t]+(?=[\"'])")
    replacements = []
    for match in pattern.finditer(text):
        line_start = text.rfind("\n", 0, match.start())+1
        if text[line_start:match.start()].lstrip().startswith("#"):
            continue
        start = match.end()
        end = _quoted_end(text, start)
        if end is None:
            continue
        script = text[start+1:end-1]
        replacement, consumed = None, end
        if "parseCodeReviewFlags" in script:
            replacement = command("review.flags")
        elif "resolveCodeReviewDepth" in script:
            replacement = command("review.depth")+" --stdin"
        elif "normalizeFallowReportFile" in script:
            replacement = command("review.normalize-structural")+" --input \"$FALLOW_JSON_PATH\" --output \"$FALLOW_NORMALIZED_PATH\""
        elif "JSON.stringify" in script and ".manifest" in script and "JSON.parse" in script:
            replacement = command("json.get")+" --field manifest"
        elif ".commits.map" in script and ".sha.slice(0,10)" in script:
            replacement = command("json.commits")+" --raw"
        elif "c[0].sha.slice(0,10)" in script:
            replacement = command("json.commits")+" --first --raw"
        elif "c[0].sha" in script and "JSON.parse" in script:
            replacement = command("json.get")+" --field commits.0.sha --default '\"\"' --raw"
        elif ".files.join(' ')" in script:
            replacement = command("json.lines")+" --field files --separator ' ' --raw"
        elif "v.status" in script and "v.reason" in script:
            replacement = command("json.status-reason")+" --raw"
        elif "orchestrator-worktree" in script and "j.exec.command" in script:
            replacement = command("json.exec-ready")+" --raw"
        elif "j.harnessFlag" in script:
            replacement = command("json.get")+" --field harnessFlag --default '\"\"' --raw"
        elif "fs.writeFileSync" in script and "orchestrator_root" in script and "worktrees:[]" in script:
            replacement = command("worktree.manifest")+" --action init --manifest \"$WAVE_WORKTREE_MANIFEST\" --root \"$ORCH_ROOT\""
        elif "orchestrator_root" in script and "process.env.MANIFEST" in script and "readFileSync" in script:
            replacement = command("worktree.manifest")+" --action root --manifest \"$WAVE_WORKTREE_MANIFEST\" --pick orchestrator_root --raw"
        elif "worktree_path" in script and "WAVE_WORKTREE_MANIFEST" in script and "readFileSync" in script:
            replacement = command("worktree.manifest")+" --action paths --manifest \"$WAVE_WORKTREE_MANIFEST\" --pick paths | "+command("json.lines")+" --raw"
        elif "Array.isArray(a)" in script and "a.some" in script and "<replace:" in script:
            argument, consumed = _argument(text, end)
            if argument:
                schema = "elements" if "ui-phase" in source else "requirements"
                replacement = command("json.validate")+" --schema "+schema+" --input "+argument
        elif "Array.isArray(r.items)" in script and "r.coverage" in script:
            replacement = command("json.validate")+" --schema coverage"
        elif "process.env.REVIEW_PATH" in script or "process.env.FIX_REPORT_PATH" in script:
            variable = "FIX_REPORT_PATH" if "process.env.FIX_REPORT_PATH" in script else "REVIEW_PATH"
            if "files_reviewed_list" in script:
                replacement = command("review.field")+" --report \"$"+variable+"\" --field files_reviewed_list --default '' --raw"
            elif "depth:" in script:
                replacement = command("review.field")+" --report \"$"+variable+"\" --field depth --default standard --raw"
            elif "status:" in script:
                replacement = command("review.field")+" --report \"$"+variable+"\" --field status --default unknown --raw"
        elif "section_manifest" in script and "PROJECT_MD_REVIEW=" in script:
            argument, consumed = _argument(text, end)
            if argument:
                replacement = ("if [ \"$("+command("json.has-section")+" --payload "+argument+" --section project-md-evolution-review --raw)\" = true ]; then printf 'PROJECT_MD_REVIEW=run\\n'; else printf 'PROJECT_MD_REVIEW=skip\\n'; fi")
        elif "section_manifest" in script and "process.exit" in script and "process.argv[2]" in script:
            payload, cursor = _argument(text, end)
            section, consumed = _argument(text, cursor)
            if payload and section:
                replacement = "[ \"$("+command("json.has-section")+" --payload "+payload+" --section "+section+" --raw)\" = true ]"
        elif "JSON.parse" in script and "process.argv[1]" in script and ("[process.argv[1]]" in script or "j[k]" in script):
            argument, consumed = _argument(text, end)
            if argument:
                if "entries.length" in script:
                    replacement = ("if [ "+argument+" = total ]; then "+command("json.length")+" --field entries --raw; else "+command("json.get")+" --field "+argument+" --raw; fi")
                elif "Array.isArray(v)" in script and ".join(" in script:
                    replacement = command("review.field")+" --stdin --field "+argument+" --default '' --raw"
                else:
                    replacement = command("json.get")+" --field "+argument+" --default '\"\"' --raw"
        elif "JSON.parse" in script and ".items.length" in script:
            replacement = command("json.length")+" --field items --raw"
        elif "JSON.parse" in script and ".coverage.applicable" in script:
            replacement = command("json.get")+" --field coverage.applicable --raw"
        elif "JSON.parse" in script and ".coverage.unclassified" in script:
            replacement = command("json.get")+" --field coverage.unclassified --raw"
        elif "Array.isArray(parsed.errors)" in script and "for (const err of errors)" in script:
            replacement = command("json.lines")+" --field errors --raw >&2"
        elif "JSON.parse" in script and len(script) < 1200 and not re.search(r"writeFile|copyFile|unlink|spawn|exec\(|fetch\(|for\s*\(", script):
            fields = ("fix", "all", "auto", "depth", "files", "concurrency", "custom_count", "verdict")
            field = next((field for field in fields if re.search(r"\."+field+r"\b", script)), None)
            if field and "readFileSync(process.env" not in script:
                replacement = command("json.get")+" --field "+field+" --raw"
        if replacement is not None:
            replacements.append((match.start(), consumed, replacement))
    for start, end, replacement in reversed(replacements):
        text = text[:start]+replacement+text[end:]
    return text


def _shell(body, command, source, runtime_path):
    if source.endswith("code-review-disposition.md"):
        # This exact operation has a dedicated fresh ledger implementation;
        # generic JSON projection cannot preserve identity/history semantics.
        ledger = (r'(?ms)^REVIEW_FILE="\$\{REVIEW_FILE\}" DISPOSITION_FILE="\$\{DISPOSITION_FILE\}" PADDED="\$\{PADDED\}" \\\n'
                  r'REVIEW_TOTAL="\$\{REVIEW_TOTAL\}" \\\n'
                  r'FIX_REPORT_FILE="\$\{FIX_REPORT_FILE\}" node -e "\n.*?^" \|\| echo "Code review disposition record skipped \(non-blocking\)\."')
        body = re.sub(ledger, lambda _: command("review.reconcile")+
                      ' --review-file "$REVIEW_FILE" --disposition-file "$DISPOSITION_FILE" --phase "$PADDED" --review-total "$REVIEW_TOTAL" --fix-report-file "$FIX_REPORT_FILE" || echo "Code review disposition record skipped (non-blocking)."', body)
    # Loader search/build fallbacks are superseded by the installed Python
    # operation. The input authoring/resolution loop remains byte-for-byte.
    if source.endswith(("spec-phase.md", "ui-phase.md", "specless-probe-fallback.md")):
        variable = "UI_PROBE_JS" if source.endswith("ui-phase.md") else "EDGE_PROBE_JS"
        pattern = r'(?ms)^_GSD_RT=[^\n]*\n'+variable+r'=\$\(for .*?^fi\n(?=\n# (?:Write the Requirements|Element extraction|THE ONE DIVERGENCE))'
        replacement = ('[ -f '+_quote(runtime_path)+' ] || { printf \'%s\\n\' \'ERROR: installed Python workflow runtime is missing; restore the pinned installation before probing.\' >&2; exit 1; }\n')
        body = re.sub(pattern, lambda _: replacement, body)
        if source.endswith("specless-probe-fallback.md"):
            body = re.sub(r'(?ms)^_GSD_RT=[^\n]*\n_gsd_lib\(\).*?^\[ -n "\$SPEC_SECTION_JS" \][^\n]*\n', lambda _: replacement, body)
            body = re.sub(r'''node "\$SPEC_SECTION_JS" "\$SPEC_FILE" (edges|prohibitions)[ \t]+2>/dev/null \| grep -q '\"supplied\":true' ''',
                          lambda m: '[ "$('+command("spec.section")+' "$SPEC_FILE" '+m[1]+' --pick supplied --raw)" = true ] ', body)
    # Remove only loader machinery for known equivalent Python operations.
    known = r"(?:code-review-flags|code-review-depth|fallow-runner)\.cjs"
    body = re.sub(r"(?ms)^[ \t]*# gsd-resolve-lib begin "+known+r"[^\n]*\n.*?^[ \t]*# gsd-resolve-lib end[^\n]*\n", "", body)
    body = re.sub(r'node "\$EDGE_PROBE_JS" "\$REQS_JSON"', lambda _: command("spec.edge-probe")+' "$REQS_JSON"', body)
    body = re.sub(r'node "\$UI_PROBE_JS" "\$ELEMENTS_JSON"', lambda _: command("spec.ui-probe")+' --input "$ELEMENTS_JSON"', body)
    # A source helper reads created/modified SUMMARY fields, never source prose.
    body = re.sub(r"(?ms)^([ \t]*)node - \"\$1\" 2>/dev/null <<'NODE'\n(?=[\s\S]*?KNOWN_EXTENSIONLESS_BUILD_FILES).*?^NODE\n",
                  lambda m: m[1]+command("review.summary-files")+' --report "$1" --raw 2>/dev/null\n', body)
    # A commits-only response is newline text. This reader needs the complete
    # scoped JSON packet in order to select its first captured commit.
    if source.endswith("completion-reconciliation.md"):
        body = body.replace('--commits-only --committed-since', '--committed-since')
    if source.endswith("executor-isolation-dispatch.md"):
        body = body.replace('--agent-id "$AGENT_ID" \\\n', '--agent-id "$AGENT_ID" \\\n  --plan "{plan_number}" \\\n')
        body = body.replace('[ "$USE_WORKTREES" = "false" ] && ISOLATION=none',
                            '[ "$USE_WORKTREES" != "false" ] || { printf \'%s\\n\' \'BLOCKED: workflow isolation is mandatory; no sequential shared-checkout fallback is permitted.\' >&2; exit 1; }')
        # A real base mismatch never degrades into writes in the primary lane.
        body = re.sub(r'(?ms)^if \[ "\$ISOLATION" != "none" \]; then\n  _SHOULD_DEGRADE=.*?^fi\n',
                      lambda _: ('BASE_CHECK=$('+command("worktree.base-check")+' --mode "$ISOLATION") || exit $?\n'
                                 '[ "$(printf \'%s\' "$BASE_CHECK" | '+command("json.get")+' --field ready --raw)" = true ] || { printf \'%s\\n\' "$BASE_CHECK" >&2; exit 1; }\n'), body)
    body = _assignments(body, command)
    return _node_calls(body, command, source)


def _step(text, name, replacement):
    pattern = re.compile(r'(?s)(<step name="'+re.escape(name)+r'"[^>]*>).*?(</step>)')
    return pattern.sub(lambda match: match[1]+"\n"+replacement.strip()+"\n"+match[2], text)


def _pinned_update(text, command, runtime_path):
    """Port the update mechanism while retaining its full backup/restore method."""
    update = "python -I "+_quote(PurePosixPath(runtime_path).parents[2]/"bin/update.py")
    text = text.replace("Check for Engineer updates via npm, display changelog for versions between installed and latest, obtain user confirmation, and execute clean installation with cache clearing.",
                        "Inspect a user-selected source revision, display its pinned Git changes and complete update plan, preserve custom files, obtain any still-required approval, and apply the exact reviewed transaction with recoverable backups.")
    text = re.sub(r'`update-context` reproduces the previous detection cascade.*?Branch coverage lives in `tests/update-context\.test\.cjs`\.',
                  'The installed Python `update-context` reads actual manifest provenance and returns its exact source, revision, host, scope and target. Multiple matching installations remain ambiguous until an actual target is selected. An absent or malformed manifest cannot establish an update target.', text, flags=re.S)
    text = _step(text, "parse_update_channel", '''Select a concrete source and revision from the user's request. A channel name is not an immutable revision. Preserve any update authorization already given; ask only for genuinely missing source/ref inputs. Do not install or query an unpinned package.

```bash
IFS= read -rd '' GSD_ARGS <<'GSD_ARGS_END' || true
$ARGUMENTS
GSD_ARGS_END
GSD_ARGS=${GSD_ARGS%$'\\n'}
UPDATE_SOURCE="${UPDATE_SOURCE:-$(UC_SOURCE)}"
: "${UPDATE_SOURCE:?Specify the local source repository from the actual request or installed provenance}"
: "${UPDATE_REF:?Specify the actual user-selected commit, branch or tag to resolve once}"
UPDATE_TARGET="$(UC_TARGET)"
UPDATE_HOST="$(UC_HOST)"
case "$INSTALL_SCOPE" in LOCAL|local) UPDATE_SCOPE=--local ;; GLOBAL|global) UPDATE_SCOPE=--global ;; *) printf '%s\\n' 'BLOCKED: installation scope is unresolved' >&2; exit 1 ;; esac
TEXT_MODE=$(UC_TEXT_MODE) || exit $?
```

The source repository must already exist locally. Do not fetch, choose a different repository, infer a release channel or move an unrelated checkout. The next step resolves the selected ref to a full immutable SHA before preview or mutation.'''.replace("UC_SOURCE", command("json.get")+' --payload "$UC" --field source_path --raw').replace("UC_TARGET", command("json.get")+' --payload "$UC" --field target --raw').replace("UC_HOST", command("json.get")+' --payload "$UC" --field host --raw').replace("UC_TEXT_MODE", command("config-get")+' workflow.text_mode --raw'))
    text = _step(text, "check_latest_version", '''Resolve and capture the selected revision. The installed revision comes from the actual installation manifest, not a guessed package version.

```bash
UPDATE_PIN=$(git -C "$UPDATE_SOURCE" rev-parse --verify "$UPDATE_REF^{commit}") || exit $?
case "$UPDATE_PIN" in ''|*[!0-9a-fA-F]*) printf '%s\\n' 'BLOCKED: selected ref did not resolve to a commit' >&2; exit 1 ;; esac
[ "${#UPDATE_PIN}" -eq 40 ] || { printf '%s\\n' 'BLOCKED: expected a full source commit SHA' >&2; exit 1; }
LATEST_VERSION="$UPDATE_PIN"
CHANNEL_LABEL="selected pinned revision"
UPDATE_CHANGES=$(__CHANGES__ --source "$UPDATE_SOURCE" --from "$INSTALLED_VERSION" --ref "$UPDATE_PIN") || exit $?
printf '%s\\n' "$UPDATE_CHANGES"
```

Failure to resolve either source revision stops the update. Preserve the provider/Git diagnostic and the installed files. No package manager fallback, network fetch or latest-version substitution is allowed.'''.replace("__CHANGES__", command("update.changes")))
    text = _step(text, "compare_versions", '''Compare the actual installed source SHA with the selected immutable SHA. Semver ordering cannot establish whether a custom source checkout should be replaced.

```bash
if [ "$INSTALLED_VERSION" = "$UPDATE_PIN" ]; then
  printf '%s\\n' "The installed source revision already equals $UPDATE_PIN."
  printf '%s\\n' 'No update was applied. Use an explicit reviewed repair plan if the installed files need repair.'
  exit 0
fi
printf 'Installed revision: %s\\nSelected revision: %s\\n' "$INSTALLED_VERSION" "$UPDATE_PIN"
```

Continue only toward this selected pin. An older or divergent pin is not silently changed to another revision; show the exact changes and preserve the user's actual choice.''')
    # Replace the obsolete changelog-fetch/extractor operation, not the complete
    # confirmation, custom backup or post-update restoration methods around it.
    preview = '''1. Display the complete pinned Git changes and exact planned file transaction before any update.
2. Write the immutable preview using the installed Python updater:

```bash
CHANGELOG_PREVIEW="$UPDATE_CHANGES"
UPDATE_PLAN=$(mktemp "${TMPDIR:-/tmp}/engineer-update-plan-XXXXXX.json") || exit $?
UPDATE_PLAN_JSON=$(__UPDATER__ --source "$UPDATE_SOURCE" --ref "$UPDATE_PIN" --target "$UPDATE_TARGET" --host "$UPDATE_HOST" "$UPDATE_SCOPE" --plan "$UPDATE_PLAN") || exit $?
REVIEWED_PLAN_SHA256=$(__GET__ --payload "$UPDATE_PLAN_JSON" --field reviewed_plan_sha256 --raw) || exit $?
printf '%s\\n' "$UPDATE_PLAN_JSON"
printf 'Exact reviewed plan: %s\\nPlan SHA256: %s\\n' "$UPDATE_PLAN" "$REVIEWED_PLAN_SHA256"
```

Inspect every conflict, migration finding, managed write, preserved custom path and backup action. A preview with unresolved findings is blocked; do not edit the plan to hide them. Approval applies only to these exact reviewed plan bytes. If inputs or target files change, generate and review a fresh plan.

3. Display preview and ask for confirmation, using `$CHANGELOG_PREVIEW` from the extract step above:'''.replace("__UPDATER__", update).replace("__GET__", command("json.get"))
    text = re.sub(r'(?s)1\. Fetch changelog from GitHub raw URL.*?3\. Display preview and ask for confirmation, using `\$CHANGELOG_PREVIEW` from the extract step above:', lambda _: preview, text)
    text = text.replace('⚠️  **Note:** The installer performs a clean install of Engineer folders:\n- `commands/` will be wiped and replaced\n- `gsd-core/` will be wiped and replaced\n- `agents/gsd-*` files will be replaced',
                        '⚠️  **Note:** The installer applies only the exact reviewed transaction. Unmanaged files and conflicting local edits are preserved; no directory wipe or blanket replacement is permitted. Managed changes receive byte-preserving transaction backups with a rollback journal.')
    text = text.replace("If you've modified any Engineer files directly, they'll be automatically backed up to `gsd-local-patches/` and can be reapplied with `/update --reapply` after the update.",
                        "The preview identifies locally modified managed files. Preserve them or explicitly select reviewed conflict resolutions; exact original bytes remain in the transaction backup. Never overwrite an unreviewed local change.")
    text = text.replace("in `gsd-file-manifest.json` — i.e., files the user added themselves that the\ninstaller does not know about and will delete during the wipe.",
                        "in the installed `engineer-install/manifest.json` — files the user added themselves. The updater preserves these unmanaged paths; the additional backup below protects the explicitly previewed custom files.")
    text = text.replace("reliably with Node.js `path.relative()`.", "with the installed Python path/ownership checks.")
    text = text.replace('CUSTOM_JSON=$(engineer_run query detect-custom-files --config-dir "$RUNTIME_DIR" 2>/dev/null)',
                        'CUSTOM_JSON=$(engineer_run query detect-custom-files --config-dir "$RUNTIME_DIR") || exit $?')
    text = text.replace('RESTORE_JSON=$(engineer_run query restore-custom-files --config-dir "$GSD_DIR" 2>/dev/null)',
                        'RESTORE_JSON=$(engineer_run query restore-custom-files --config-dir "$GSD_DIR") || exit $?')
    text = text.replace('BACKUP_DIR="$RUNTIME_DIR/gsd-user-files-backup"', 'BACKUP_DIR="$RUNTIME_DIR/engineer-user-files-backup"')
    text = re.sub(r"(?ms)^node - \"\$RUNTIME_DIR\" \"\$BACKUP_DIR\" \"\$CUSTOM_JSON\" <<'JSEOF'\n.*?^JSEOF$",
                  lambda _: command("custom-files.backup")+' --config-dir "$RUNTIME_DIR" --custom-json "$CUSTOM_JSON" --backup-dir "$BACKUP_DIR" || exit $? ', text)
    text = text.replace("gsd-user-files-backup/", "engineer-user-files-backup/")
    text = text.replace("before the wipe", "before applying the reviewed transaction")
    text = text.replace("installer wipes the directories", "reviewed updater applies its managed writes")
    text = text.replace("`text_mode` from init JSON is `true`", "`TEXT_MODE` from the actual configuration is `true`")
    text = _step(text, "run_update", '''Apply only the exact reviewed plan after the existing update authorization or explicit answer covers this pin and its concrete transaction. Do not request approval again solely because this workflow reached the apply step.

```bash
: "${UPDATE_PLAN:?The complete pinned preview must exist before apply}"
: "${REVIEWED_PLAN_SHA256:?The SHA256 of the exact reviewed plan bytes is required}"
UPDATE_RESULT=$(__UPDATER__ --apply "$UPDATE_PLAN" --reviewed-plan-sha256 "$REVIEWED_PLAN_SHA256") || exit $?
printf '%s\\n' "$UPDATE_RESULT"
UPDATE_BACKUP=$(__GET__ --payload "$UPDATE_RESULT" --field backup --raw) || exit $?
```

The updater rechecks the source pin, exporter digest, target hashes, manifest and exact reviewed bytes. Any drift stops mutation. It journals original bytes and file modes before writes and rolls back a failed transaction. Preserve its error and backup path if recovery is needed; do not retry an uncertain transaction blindly.

Do not clear unrelated cache files, install a package, wipe managed directories or run a second installer. The returned verification field remains not-executed: successful installation is not evidence of runtime correctness.'''.replace("__UPDATER__", update).replace("__GET__", command("json.get")))
    text = _step(text, "display_result", '''Report only the actual update result: installed source revision, target, host, changed paths, preserved local files and returned backup directory. Name any blocked or deferred paths and execution checks that remain unrun.

```bash
printf 'Updated source: %s\\nTarget: %s\\nBackup: %s\\n' "$UPDATE_PIN" "$UPDATE_TARGET" "$UPDATE_BACKUP"
```

Ask the user to restart the host when required to load changed commands. The previously displayed pinned Git changes are the change record; do not invent a release version or use a moving changelog URL as evidence.''')
    # Preserve the full restore preview/selection procedure and its untrusted
    # filename handling, adding the actual snapshot token and exact selections.
    text = text.replace('restore-custom-files --config-dir "$GSD_DIR" --apply',
                        'restore-custom-files --config-dir "$GSD_DIR" --preview-token "$RESTORE_PREVIEW_TOKEN" --apply "${RESTORE_SELECTION_ARGS[@]}"')
    text = text.replace('RESTORE_DIR=$(json_field backup_dir)',
                        'RESTORE_PREVIEW_TOKEN=$(json_field preview_token)\nRESTORE_DIR=$(json_field backup_dir)')
    text = text.replace('**If the user chooses to restore:**',
                        '**If the user chooses to restore:** Read the exact eligible paths from the displayed preview. Set `RESTORE_SELECTION_ARGS` as a Bash array containing one `--select` and its unchanged path per explicitly selected eligible entry. Do not infer additional selections, restore blocked entries or replace files that appeared after preview. Keep `RESTORE_PREVIEW_TOKEN` bound to these exact current snapshots.')
    text = _step(text, "check_local_patches", '''Inspect the returned transaction backup rather than an obsolete package patch directory. Its journal records exact original bytes, modes and target-relative paths.

```bash
printf 'Preserved transaction backup: %s\\n' "$UPDATE_BACKUP"
```

Do not automatically reapply locally modified managed files over the new pin. Compare the actual source, backed-up bytes and updated contract; prepare exact reviewed resolutions. The user may keep the backup without changing the installed result.

If the exact transaction must be rolled back, first inspect its journal, ownership and current target state. With actual rollback authority, call the same pinned updater using the returned backup path:

```bash
__UPDATER__ --target "$UPDATE_TARGET" --host "$UPDATE_HOST" --rollback "$UPDATE_BACKUP"
```

Rollback validates target ownership and refuses drift. Preserve the backup and diagnostic when that check fails. It never authorizes deleting unrelated files or replacing later user changes.'''.replace("__UPDATER__", update))
    text = text.replace("Latest version checked via npm", "User-selected source ref captured as a full immutable Git SHA")
    text = text.replace("Changelog fetched and displayed BEFORE update", "Pinned changes and complete reviewed transaction displayed BEFORE update")
    text = text.replace("Clean install warning shown", "Exact managed writes, conflicts, preserved paths and recoverable backups shown")
    text = text.replace("latest-version", "selected-revision")
    text = text.replace("**Latest:**", "**Selected revision:**")
    text = text.replace('run `npx -y --package=@opengsd/gsd-core@latest -- gsd-core --global`',
                        'use the pinned Python installer with explicit source, ref, target, host and scope')
    return text


def transform(text, source_name, runtime_path):
    """Return full text with recognized retained shell adapters translated."""
    source = source_name.replace("\\", "/")
    runtime_path = runtime_path.replace("\\", "/")
    if not source.endswith((".md", ".txt", ".sh")):
        return text
    crlf = "\r\n" in text and text.count("\r\n") == text.count("\n")
    if crlf:
        text = text.replace("\r\n", "\n")
    command = lambda verb: "python -I "+_quote(runtime_path)+" query "+verb
    # Operative examples in commands/skills share these exact source contracts.
    if source.endswith("engineer/workflows/update.md"):
        text = _pinned_update(text, command, runtime_path)
    if source.endswith("engineer/workflows/execute-phase.md"):
        text = text.replace('worktree.record-agent --manifest "$WAVE_WORKTREE_MANIFEST" --agent-id',
                            'worktree.record-agent --manifest "$WAVE_WORKTREE_MANIFEST" --plan "{plan_id}" --terminal-receipt "$NATIVE_TERMINAL_RECEIPT" --agent-id')
        anchor = 'After each `Agent()` returns, parse executor-returned worktree metadata'
        text = text.replace(anchor,
                            'For a native harness worker, obtain and persist the actual host terminal receipt before recording completion: source `native-host`, actual Claude/Codex host, agent ID, absolute worktree path, branch, captured head, actual complete/completed/stopped status and exact repository-relative SUMMARY path. Bind `NATIVE_TERMINAL_RECEIPT` to that real packet file. A narration, timeout, guessed PID or `--completed` flag is not a receipt. If the host cannot supply one, stop integration and preserve the checkout; use the orchestrator process backend for subsequent dispatch rather than inventing evidence. '+anchor)
    if source.endswith("engineer/workflows/quick-batch/steps/worktree-dispatch.md"):
        text = text.replace('worktree.create --manifest "$QUICK_BATCH_WORKTREE_MANIFEST" --agent-id',
                            'worktree.create --manifest "$QUICK_BATCH_WORKTREE_MANIFEST" --plan "${quick_id}" --agent-id')
    if source.endswith(".sh"):
        result = _shell(text, command, source, runtime_path)
        return result.replace("\n", "\r\n") if crlf else result
    fence = re.compile(r"(?ms)^([ \t]*)```(bash|sh|shell|zsh)[ \t]*\n(.*?)^\1```[ \t]*$")
    def block(match):
        return match[1]+"```"+match[2]+"\n"+_shell(match[3], command, source, runtime_path)+match[1]+"```"
    result = fence.sub(block, text)
    return result.replace("\n", "\r\n") if crlf else result
