"""Pure, source-backed translations for retained workflow shell adapters.

Only recognized operations are rewritten. This module neither runs code nor
writes exports. Unknown JavaScript stays intact for the installer's refusal gate.
"""
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
            replacement = command("json.get")+" --field errors --raw >&2"
        elif "JSON.parse" in script and len(script) < 1200 and not re.search(r"writeFile|copyFile|unlink|spawn|exec\(|fetch\(|for\s*\(", script):
            fields = ("fix", "all", "auto", "depth", "files", "concurrency", "custom_count", "verdict", "ok")
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
        pattern = r'(?ms)^_ENGINEER_RT=[^\n]*\n'+variable+r'=\$\(for .*?^fi\n(?=\n# (?:Write the Requirements|Element extraction|THE ONE DIVERGENCE))'
        replacement = ('[ -f '+_quote(runtime_path)+' ] || { printf \'%s\\n\' \'ERROR: installed Python workflow runtime is missing; restore the pinned installation before probing.\' >&2; exit 1; }\n')
        body = re.sub(pattern, lambda _: replacement, body)
        if source.endswith("specless-probe-fallback.md"):
            body = re.sub(r'(?ms)^_ENGINEER_RT=[^\n]*\n_engineer_lib(?:\(\))? \{.*?^\[ -n "\$SPEC_SECTION_JS" \][^\n]*\n', lambda _: replacement, body)
            body = re.sub(r'''node "\$SPEC_SECTION_JS" "\$SPEC_FILE" (edges|prohibitions)[ \t]+2>/dev/null \| grep -q '\"supplied\":true' ''',
                          lambda m: '[ "$('+command("spec.section")+' "$SPEC_FILE" '+m[1]+' --pick supplied --raw)" = true ] ', body)
    # Remove only loader machinery for known equivalent Python operations.
    known = r"(?:code-review-flags|code-review-depth|fallow-runner)\.cjs"
    body = re.sub(r"(?ms)^[ \t]*# engineer-resolve-lib begin "+known+r"[^\n]*\n.*?^[ \t]*# engineer-resolve-lib end[^\n]*\n", "", body)
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
        body = body.replace('--agent-id "$AGENT_ID" \\\n', '--agent-id "$AGENT_ID" \\\n  --plan "${plan_id:?Set plan_id from the selected plan record}" \\\n')
        body = body.replace('[ "$USE_WORKTREES" = "false" ] && ISOLATION=none',
                            '[ "$USE_WORKTREES" != "false" ] || { printf \'%s\\n\' \'BLOCKED: workflow isolation is mandatory; no sequential shared-checkout fallback is permitted.\' >&2; exit 1; }')
        # A real base mismatch never degrades into writes in the primary lane.
        body = re.sub(r'(?ms)^if \[ "\$ISOLATION" != "none" \]; then\n  _SHOULD_DEGRADE=.*?^fi\n',
                      lambda _: ('BASE_CHECK=$('+command("worktree.base-check")+' --mode "$ISOLATION") || exit $?\n'
                                 '[ "$(printf \'%s\' "$BASE_CHECK" | '+command("json.get")+' --field ready --raw)" = true ] || { printf \'%s\\n\' "$BASE_CHECK" >&2; exit 1; }\n'), body)
    body = _assignments(body, command)
    return _node_calls(body, command, source)


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
    if source.endswith("engineer/workflows/execute-phase.md"):
        text = text.replace('worktree.record-agent --manifest "$WAVE_WORKTREE_MANIFEST" --agent-id',
                            'worktree.record-agent --manifest "$WAVE_WORKTREE_MANIFEST" --plan "${plan_id:?Set plan_id from the selected plan record}" --terminal-receipt "$NATIVE_TERMINAL_RECEIPT" --agent-id')
        anchor = 'After each `Agent()` returns, parse executor-returned worktree metadata'
        text = text.replace(anchor,
                            'For a native harness worker, obtain and persist the actual host terminal receipt before recording completion: source `native-host`, actual Claude/Codex host, agent ID, absolute worktree path, branch, captured head, actual complete/completed/stopped status and exact repository-relative SUMMARY path. Bind `NATIVE_TERMINAL_RECEIPT` to that real packet file. A narration, timeout, guessed PID or `--completed` flag is not a receipt. If the host cannot supply one, stop integration and preserve the checkout; use the orchestrator process backend for subsequent dispatch rather than inventing evidence. '+anchor)
    if source.endswith("engineer/workflows/quick-batch/steps/worktree-dispatch.md"):
        text = text.replace('worktree.create --manifest "$QUICK_BATCH_WORKTREE_MANIFEST" --agent-id',
                            'worktree.create --manifest "$QUICK_BATCH_WORKTREE_MANIFEST" --plan "${quick_id}" --agent-id')
    if source.endswith("engineer/workflows/quick-batch/steps/batch-init.md"):
        text = text.replace('QB_CREATE_JSON=$(engineer_run quick-batch create --file "$TASK_FILE" --base-revision "$(git rev-parse HEAD)" --raw)',
                            'QB_CREATE_JSON=$(engineer_run quick-batch create --file "$TASK_FILE" --base-revision "$(git rev-parse HEAD)" $VALIDATE_PARAM $RESEARCH_PARAM --raw)\nQB_CREATE_RC=$?')
        text = text.replace('```bash\nQB_CREATE_RC=$?\n', '```bash\n')
    if source.endswith(".sh"):
        result = _shell(text, command, source, runtime_path)
        return result.replace("\n", "\r\n") if crlf else result
    fence = re.compile(r"(?ms)^([ \t]*)```(bash|sh|shell|zsh)[ \t]*\n(.*?)^\1```[ \t]*$")
    def block(match):
        return match[1]+"```"+match[2]+"\n"+_shell(match[3], command, source, runtime_path)+match[1]+"```"
    result = fence.sub(block, text)
    return result.replace("\n", "\r\n") if crlf else result
