@.ai/library/references/response-language-directive.md

# sync-skills — Cross-Runtime Workflow Skill Sync

**Command:** `/workflow-sync-skills`

Sync managed `workflow-*` skill directories from one canonical runtime's skills root to one or more destination runtime skills roots. Keeps multi-runtime installs aligned after a `workflow-update` on one runtime.

---

## Arguments

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--from <runtime>` | Yes | *(none)* | Source runtime — the canonical runtime to copy from |
| `--to <runtime\|all>` | Yes | *(none)* | Destination runtime or `all` supported runtimes. **Must equal `--from`** — cross-runtime sync is refused (#3025: skill content/layout is runtime-specific and produced by the installer's per-runtime converters; use the installer for a different runtime). |
| `--dry-run` | No | *on by default* | Preview changes without writing anything |
| `--apply` | No | *off* | Execute the diff (overrides dry-run) |

If neither `--dry-run` nor `--apply` is specified, dry-run is the default.

**Supported runtime names:** `antigravity`, `augment`, `claude`, `cline`, `codebuddy`, `codex`, `copilot`, `cursor`, `grok`, `hermes`, `kilo`, `kimi`, `kimi-code`, `opencode`, `pi`, `qwen`, `trae`, `windsurf`, `zcode` — the full capability registry runtime set (`workflow-core/bin/lib/capability-registry.cjs`'s `runtimes`) plus `grok` (a live, dedicated `~/.agents`-layout resolution branch in `getGlobalConfigDir` predating the capability registry — overridable via `GROK_AGENTS_HOME`), excluding `vscode`: it is `installSurface: 'none'` (#2103) and `getGlobalSkillsBase('vscode')` returns `null`, so a skills-root sync to/from it always aborts at Step 2's resolution guard — there is nowhere on disk to sync to.

---

## Step 1: Parse Arguments

```bash
FROM_RUNTIME=""
TO_RUNTIMES=()
IS_APPLY=false

# Parse --from
if [[ "$@" == *"--from"* ]]; then
  FROM_RUNTIME=$(echo "$@" | sed -E 's/.*--from[[:space:]]+([^[:space:]]+).*/\1/')
fi

# Parse --to
if [[ "$@" == *"--to all"* ]]; then
  TO_RUNTIMES=(antigravity augment claude cline codebuddy codex copilot cursor grok hermes kilo kimi kimi-code opencode pi qwen trae windsurf zcode)
elif [[ "$@" == *"--to"* ]]; then
  TO_RUNTIMES=( $(echo "$@" | sed -E 's/.*--to[[:space:]]+([^[:space:]]+).*/\1/') )
fi

# Parse --apply
if [[ "$@" == *"--apply"* ]]; then
  IS_APPLY=true
fi
```

**Validation:**
- If `--from` is missing or unrecognized: print error and exit
- If `--to` is missing or unrecognized: print error and exit
- If `--from` == `--to` (single destination): print `[no-op: source and destination are the same runtime]` and exit
- If any `--to` destination differs from `--from` (cross-runtime): REFUSE with the installer pointer below and exit. sync only supports identity sync — see the guard.
- If `--from` or any `--to` value is not a runtime-id shape (`^[a-z0-9][a-z0-9-]*$`): REFUSE and exit — runtime ids are lowercase alphanumeric (+ hyphen); this rejects shell metacharacters before any interpolation (see security guard).

**#3025 — Runtime-id shape validation (security: run BEFORE any interpolation):**

`--from`/`--to` are interpolated into later `echo`/heredoc/`[[ ]]` contexts. Reject any value that is not a runtime-id shape BEFORE it reaches them, so a hostile value (e.g. `--to '$(cmd)'`, captured wholesale by the parser) cannot execute via command substitution in an error message.

```bash
# #3025 (security): runtime ids are lowercase alphanumeric (+ hyphen). Reject
# anything else BEFORE any echo/heredoc/[[ ]] so a hostile --from/--to value
# cannot execute via command substitution in a later error message.
is_runtime_id() { [[ "$1" =~ ^[a-z0-9][a-z0-9-]*$ ]]; }
if ! is_runtime_id "$FROM_RUNTIME"; then
  echo "error: invalid --from runtime id (not lowercase alphanumeric): '$FROM_RUNTIME'" >&2
  exit 1
fi
for DEST in "${TO_RUNTIMES[@]}"; do
  if ! is_runtime_id "$DEST"; then
    echo "error: invalid --to runtime id (not lowercase alphanumeric): '$DEST'" >&2
    exit 1
  fi
done
```

**#3025 — Cross-runtime refuse guard (run BEFORE Step 2 resolution / Step 5 copy):**

Skill content and directory layout are runtime-specific. The installer applies per-runtime
converters, adapter headers, brand swaps, and layout rules at install time, and two runtimes
(`grok`, `gemini`) resolve to ANOTHER runtime's skills root. A verbatim copy from one runtime's
skills root therefore produces content the installer would never have written for the destination,
and can damage a runtime the user never named. Every cross-runtime pair is unsafe (content and/or
layout and/or aliasing); only identity (`--from` == `--to`) is safe. Refuse cross-runtime and point
the user at the installer — the only path that produces correctly converted skills.

```bash
# #3025: refuse cross-runtime skill sync before any resolution or copy.
for DEST in "${TO_RUNTIMES[@]}"; do
  if [[ "$DEST" != "$FROM_RUNTIME" ]]; then
    cat >&2 <<EOF
error: cross-runtime skill sync is not supported (--from $FROM_RUNTIME --to $DEST).
       Skill content and directory layout are runtime-specific: the installer applies
       per-runtime converters, adapter headers, brand swaps, and layout rules that a
       verbatim copy cannot reproduce, and some runtimes share another runtime's skills
       root — so a cross-runtime sync can damage a runtime you did not name.
       To install correctly-converted skills for the '$DEST' runtime, run the Workflow
       installer for that runtime (not sync):
         npx -y @openworkflow/workflow-core@latest --global --<runtime>
       (grok and gemini have no dedicated installer flag — they alias the codex and
       claude skills roots respectively, which is itself why sync refuses them.)
       sync only supports identity sync, where --from and --to are the same runtime.
EOF
    exit 1
  fi
done
```

---

## Step 2: Resolve Skills Roots

Resolve paths via `workflow_run query skills-root` — this reuses the single authoritative path table via the shipped `workflow-tools` binary (#3024: the installer entry point is not shipped in installed trees, but `workflow-tools` is):

```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
SRC_SKILLS_ROOT=$(workflow_run query skills-root "$FROM_RUNTIME" --raw)
if [ $? -ne 0 ] || [ -z "$SRC_SKILLS_ROOT" ]; then
  echo "error: failed to resolve skills root for runtime '$FROM_RUNTIME' (workflow_run query skills-root $FROM_RUNTIME --raw)" >&2
  exit 1
fi

for DEST_RUNTIME in "${TO_RUNTIMES[@]}"; do
  RESOLVED_DEST_ROOT=$(workflow_run query skills-root "$DEST_RUNTIME" --raw)
  if [ $? -ne 0 ] || [ -z "$RESOLVED_DEST_ROOT" ]; then
    echo "error: failed to resolve skills root for runtime '$DEST_RUNTIME' (workflow_run query skills-root $DEST_RUNTIME --raw)" >&2
    exit 1
  fi
done
```

This loop validates every destination in `TO_RUNTIMES` up front — a bad runtime id anywhere in a multi-destination `--to` aborts here, before Step 3 or Step 5 touch anything. The resolved value itself is not retained: each of Steps 3 and 5 re-resolves `DEST_ROOT` for the specific `$DEST_RUNTIME` it is currently processing (see those steps), so `$DEST_ROOT` is always unambiguously scoped to one destination and never threaded through a shared array.

**Guard:** If the source skills root does not exist, print:
```
error: source skills root not found: <path>
       Is Workflow installed globally for the '<runtime>' runtime?
       Run: npx -y @openworkflow/workflow-core@latest --global --<runtime>
```
Then exit.

**Guard:** If resolving the skills root for the source OR any destination runtime fails (`workflow_run query skills-root <runtime> --raw` exits non-zero or prints nothing — see Step 2's bash), print:
```
error: failed to resolve skills root for runtime '<runtime>'
       command: workflow_run query skills-root <runtime> --raw
       Is '<runtime>' a registered runtime id? See supported runtime names above.
```
Then exit. Never proceed to Step 3 or Step 5 with an empty or unresolved root — an empty `$DEST_ROOT` turns `rm -rf "$DEST_ROOT/$SKILL"` into `rm -rf "/$SKILL"`.

**Guard:** If `--to` contains the same runtime as `--from`, skip that destination silently.

---

## Step 3: Compute Diff Per Destination

For each destination runtime:

```bash
# Bind the destination root for this iteration's destination runtime. Already
# validated to resolve successfully in Step 2's eager-validation loop;
# re-resolving here (rather than reading back a shared array) keeps this
# value unambiguously scoped to the destination currently being processed.
DEST_ROOT=$(workflow_run query skills-root "$DEST_RUNTIME" --raw)
if [ $? -ne 0 ] || [ -z "$DEST_ROOT" ]; then
  echo "error: failed to resolve skills root for runtime '$DEST_RUNTIME' (workflow_run query skills-root $DEST_RUNTIME --raw)" >&2
  exit 1
fi

# List workflow-* subdirectories in source
SRC_SKILLS=$(ls -1 "$SRC_SKILLS_ROOT" 2>/dev/null | grep '^workflow-')

# List workflow-* subdirectories in destination (may not exist yet)
DST_SKILLS=$(ls -1 "$DEST_ROOT" 2>/dev/null | grep '^workflow-')

# Diff:
# CREATE  — in SRC but not in DST
# UPDATE  — in both; content differs (compare recursively via checksums)
# REMOVE  — in DST but not in SRC (stale Workflow skill no longer in source)
# SKIP    — in both; content identical (already up to date)
```

**Non-Workflow preservation:** Only `workflow-*` entries are ever created, updated, or removed. Entries in the destination that do not start with `workflow-` are never touched.

---

## Step 4: Print Diff Report

Always print the report, regardless of `--apply` or `--dry-run`:

```
sync source: <runtime> (<src_skills_root>)
sync targets: <dest1>, <dest2>

== <dest1> (<dest1_skills_root>) ==
CREATE: workflow-help
UPDATE: workflow-update
REMOVE: workflow-old-command
SKIP:   workflow-plan-phase (up to date)
(N changes)

== <dest2> (<dest2_skills_root>) ==
CREATE: workflow-help
(N changes)

dry-run only. use --apply to execute.    ← omit this line if --apply
```

If a destination root does not exist and `--apply` is true, print `CREATE DIR: <path>` before its entries.

If all destinations are already up to date:
```
All destinations are up to date. No changes needed.
```

---

## Step 5: Execute (only when --apply)

If `--dry-run` (or no flag): skip this step entirely and exit after printing the report.

For each destination with changes:

```bash
# Bind DEST_ROOT for this iteration's destination (see Step 3's identical
# re-resolution note — Step 2 already validated this resolves successfully).
DEST_ROOT=$(workflow_run query skills-root "$DEST_RUNTIME" --raw)

[[ "$SRC_SKILLS_ROOT" == /* ]] || { echo "error: SRC_SKILLS_ROOT is empty or not absolute: '$SRC_SKILLS_ROOT'" >&2; exit 1; }
[[ "$DEST_ROOT" == /* ]] || { echo "error: DEST_ROOT is empty or not absolute: '$DEST_ROOT'" >&2; exit 1; }

mkdir -p "$DEST_ROOT"

# #3025: cross-runtime sync is refused in Step 1's guard (skill content/layout is
# runtime-specific; a verbatim copy corrupts destinations and can alias another
# runtime's root). This loop is therefore reached only for IDENTITY sync, where
# every skill is SKIP (source == destination) and the create/update lists are
# empty. If per-runtime conversion is ever wired in, this is where it would go;
# until then the cp -r must never run for a destination != source.

# Rewrapped through unquoted command substitution (workflow-core#4109): a bare
# `$VAR` word-splits under bash but not zsh, collapsing every element onto
# one iteration there.
for SKILL in $(printf '%s' "$CREATE_LIST") $(printf '%s' "$UPDATE_LIST"); do
  rm -rf "$DEST_ROOT/$SKILL"
  cp -r "$SRC_SKILLS_ROOT/$SKILL" "$DEST_ROOT/$SKILL"
done

# Rewrapped through unquoted command substitution (workflow-core#4109): a bare
# `$VAR` word-splits under bash but not zsh, collapsing every element onto
# one iteration there.
for SKILL in $(printf '%s' "$REMOVE_LIST"); do
  rm -rf "$DEST_ROOT/$SKILL"
done
```

**Idempotency:** Running `--apply` a second time with no intervening changes must report zero changes (all entries are SKIP).

**Atomicity:** Each skill directory is replaced as a unit (remove then copy). Partial updates of individual files within a skill are not performed — the whole directory is replaced.

After executing all destinations:

```
Sync complete: <N> skills synced to <M> runtime(s).
```

---

## Safety Rules

1. **Only `workflow-*` directories** are created, updated, or removed. Any directory not starting with `workflow-` in a destination root is untouched.
2. **Dry-run is the default.** `--apply` must be passed explicitly to write anything.
3. **Source root must exist.** Never create the source root; it must have been created by a prior `workflow-update` or installer run.
4. **No cross-runtime content transformation.** Sync copies files verbatim. It does not apply runtime-specific content transformations (those happen at install time). If a runtime requires transformed content (e.g. Augment's format differs), the developer should run the installer for that runtime instead of using sync.

---

## Limitations

- Sync copies files verbatim and does not apply runtime-specific content transformations. **Cross-runtime sync is refused** (#3025): skill content and layout are runtime-specific, and some runtimes alias another runtime's skills root, so a verbatim cross-runtime copy corrupts the destination (and can damage a runtime you did not name). Only identity sync (`--from` == `--to`) is supported. To install skills for a different runtime, run the Workflow installer for that runtime (`npx -y @openworkflow/workflow-core@latest --global --<runtime>`).
- Cross-project skills (`.agents/skills/`) are out of scope — this command only touches global runtime skills roots.
- Bidirectional sync is not supported. Choose one canonical source with `--from`.


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

This complete authoring guide retains its source content, examples, and methods.
Only recorded namespace/reference substitutions and explicit local conflict
corrections have been made. Source attribution and exact original hashes are
isolated in `.ai/library/THIRD-PARTY-NOTICES.md` and `PROVENANCE.json`.

Read `.ai/library/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/template-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The retained `config.json`, `/workflow:*` commands, tool
names, hooks, and Node CLI examples describe supporting source capabilities;
this import does not install or activate them. Source catalog pointers in examples
identify provenance, not executable command arguments. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
