**Revert this phase's own requirement IDs out of `Complete` before rendering the gap report (#2388).** A shared requirement ID can already read `Complete` at this point (its first-declaring plan finished before this verification ran) — a `gaps_found` verdict must not leave that premature `Complete` sitting in REQUIREMENTS.md. Scoped strictly to `PHASE_REQ_IDS` (this phase's own citations from `init.execute-phase`), so another phase's `Complete` row is never touched:

```bash
if [ -n "${PHASE_REQ_IDS}" ]; then
  workflow_run query requirements.revert-phase ${PHASE_REQ_IDS} >/dev/null 2>&1 || true
  workflow_run query commit "docs(phase-{X}): revert premature Complete requirements after gaps found" --files .planning/REQUIREMENTS.md >/dev/null 2>&1 || true
fi
```


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
