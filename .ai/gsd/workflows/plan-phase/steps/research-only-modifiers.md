### 5.0. Research-Only Modifiers (`--view`, `--research`)

**Skip if:** `RESEARCH_ONLY` is `false`.

Three branches in research-only mode (`--research-phase <N>`):

1. **`--view`**: print `RESEARCH.md` to stdout, no spawn, exit. If `RESEARCH.md` is missing, error with: `--view requires an existing RESEARCH.md; drop --view to spawn the researcher.`
2. **`--research`** (force-refresh): re-spawn researcher unconditionally — fall through to "Spawn gsd-phase-researcher" below.
3. **Neither flag AND `has_research=true`:** auto-use the existing research and exit cleanly — do not prompt, do not re-spawn. Emit `RESEARCH.md already exists for Phase ${PHASE}, using it. To force-refresh, re-invoke with --research; to print, re-invoke with --view. Path: ${research_path}` then exit. The explicit-flag escape hatches cover any deviation; this matches §5.1's promptless auto-use of existing research, removing the §5.0/§5.1 inconsistency (#159).

```bash
if [[ "$VIEW_ONLY" == "true" ]]; then
  [[ -f "$research_path" ]] || { echo "Error: --view requires an existing RESEARCH.md (Phase ${PHASE}). Drop --view to spawn the researcher."; exit 1; }
  cat "$research_path"; exit 0
fi
```


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

The complete upstream body above is retained from GSD-Core at
`c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977`; only recorded reference substitutions
and explicit local conflict corrections have been made. See
`.ai/gsd/PROVENANCE.json` for exact source hashes and changes.

Read `.ai/gsd/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/gsd-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The upstream `config.json`, `/gsd:*` commands, tool
names, hooks, and Node CLI examples describe GSD's system; this import does not
install or activate that system. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
