<step name="dispatch_monorepo_packages" condition="monorepo_workspaces is non-empty">
After Wave 2 collection, generate per-package READMEs for each monorepo workspace.

**Condition:** Only run this step if `monorepo_workspaces` from the init JSON is non-empty.

**Resolve workspace packages from glob patterns:**

```bash
# Expand workspace globs to actual package directories
for pattern in {monorepo_workspaces}; do
  ls -d $pattern 2>/dev/null
done
```

**For each resolved directory that contains a `package.json`:**

Determine mode:
- If `{package_dir}/README.md` exists: mode = `update`, read existing content
- Else: mode = `create`

Spawn a `gsd-doc-writer` agent with `run_in_background=true`:

```
Agent(
  subagent_type="gsd-doc-writer",
  model="{doc_writer_model}",
  run_in_background=true,
  description="Generate per-package README for {package_dir}",
  prompt="<doc_assignment>
type: readme
mode: {create|update}
scope: per_package
package_dir: {absolute path to package directory}
project_context: {INIT JSON with project_root set to package directory}
{existing_content: | (include full README.md content here if mode is update, else omit)}
</doc_assignment>

{AGENT_SKILLS}

Write {package_dir}/README.md directly. Return confirmation only — do not return doc content."
)
```

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling all per-package Agent() calls above with `run_in_background=true`, do NOT generate any package READMEs independently while the subagents are active. Wait for all agents to complete before proceeding. This prevents duplicate work and wasted context.

Collect confirmations by reading each package agent's `outputFile` once it reports completion — each `run_in_background=true` Agent call returns an `async_launched` result carrying an `outputFile` path (with `canReadOutputFile: true`). Note failures in the final report.

**Fallback when Task tool is unavailable:** Generate per-package READMEs sequentially inline after the `sequential_generation` step. For each package directory with a `package.json`, construct the equivalent `doc_assignment` block and generate the README following gsd-doc-writer instructions.

Continue to commit_docs.
</step>


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
