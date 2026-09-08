# Provider namespace and agent model defaults

## Authorized correction

The user corrected OpenAI's fresh installation destination to `.codex/` and requested explicit model defaults for every agent type for both OpenAI and Claude, with higher tiers for planning/review and lower-cost research/development. This extends the integrated bootstrap; it does not implement or approve PLAN-001's future engine tasks.

Base: `abb6b6b444aa78caab573c2f24873667f80a4530`. Local corrective branch: `chore/codex-namespace`; linked worktree: `.worktrees/codex-namespace` beneath the repository base.

## Delivered behavior

- Fresh `codex` and `chatgpt` installs use `.codex/`; Claude uses `.claude/`. Reusable `docs/` assets include agents, templates, workflows, tools, schemas, and empty lifecycle records.
- Existing native settings and native agent files survive installation. Existing managed/partial toolkit namespaces block a second registry. The CLI and validator retain legacy `.ai/` compatibility; source development records and immutable history remain in `.ai/`.
- `docs/defaults/AGENT_MODELS.json` is copied to the selected namespace's project-owned `project/agent-models.json`. It contains both provider maps, 22 role mappings, provider-specific effort settings, policy profile mappings, and dated official source URLs. Reinstallation preserves project overrides.
- New policy gate profiles are populated from the selected provider's defaults and remain `configured: false` until the actual invocation is verified. This metadata does not register native subagents or implement model dispatch.
- OpenAI defaults: Luna/medium for research, Terra/medium for operations, Terra/high for development, Sol/xhigh for escalated development, and Astra/xhigh for planning, review, and recovery. Claude defaults: Haiku 4.5 without effort for research, Sonnet 5 medium/high for operations/development, and Opus 5/high for planning/review/recovery. Opus implementation requires Fable 5.1/high review to preserve a higher review tier.
- This repository's source model record retains the user's Sol/xhigh implementation override. Source policy recommendations use Sol rank 3 and Astra rank 4, with gate verification still unset.

## Sources and review provenance

The official model and effort sources were fetched on 2026-09-07 local time and are linked in `docs/workflows/MODELS.md` and the model defaults JSON. Native Codex configuration and instruction discovery were checked against the official configuration and AGENTS.md documentation. Published availability is distinct from account/host access.

Implementation: `/root/codex_namespace_sol`, explicitly invoked as GPT-5.6 Sol (`gpt-5.6-sol`), extra high (`xhigh`). Coordinator wrote reusable guidance, default model configuration, its schema and focused tests, and source metadata.

Independent review: `/root/provider_defaults_review_astra`, explicitly invoked as GPT-6 Astra (`gpt-6-astra`), extra high (`xhigh`). Documentation/defaults/schema review and the final code review both passed. Two P2 findings were fixed and independently rechecked: gate rank validation now resolves custom profile names through `policy_profile_map`, and new installations require the model defaults record while legacy installations without the model schema remain compatible. The installer also detects a lone model configuration as a partial toolkit installation.

## Verification and integration

The implementer and independent reviewer each passed the final 24-test suite. The independent run took 25.683 seconds. Source foundation validation passed: 27 schemas, 121 artifacts, one plan, 39 tasks, 280 unordered pairs, three archive manifests, and 173 local links. Verification used Python 3.12.14 and jsonschema 4.26.0 in a temporary ignored environment. `git diff --check` passed.

The reviewer additionally installed the unchanged baseline toolkit in temporary projects in its original `.ai` and `.claude` modes, then used the current source CLI to create a plan and task and the current validator to check both. Each legacy project passed with 26 schemas, 12 artifacts, one plan, two tasks, and 40 links. Native configuration coexistence, customized model profiles, missing configuration, mapped review downgrade rejection, repeated installation, and failure recovery were verified.

Reviewed product fingerprint: `44576af405a515fcd0153f060b8236f3457a357eddab63b540a954c8e9f63f5b`, independently reproduced by the coordinator. Scope: all files under `docs/`, `src/`, `tests/`, and `schemas/`, plus root `README.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `SECURITY.md`, `.gitignore`, `.gitattributes`, and `pyproject.toml`; bytecode/caches excluded. Total: 119 files. Algorithm: sort repository-relative paths, append each path, NUL, hexadecimal SHA-256 of raw file bytes, and LF, then SHA-256 the concatenated UTF-8 records. Source `.ai` metadata was separately inspected for scope and consistency. Prior bootstrap review fingerprints remain historical evidence and do not approve these changed product files.

Integrated into `main` by fast-forward at `442ab5ae56cd1e69a342854c81bc972edd22af6b`. The merged product independently reproduced the reviewed 119-file fingerprint, and merged-main foundation validation passed with the counts above. The clean merged worktree was removed through Git; its merged branch and empty `.worktrees/` container were deleted. The temporary verification environment and empty `.ai/local/` directory were removed. Git then reported only the main worktree, a clean working tree, and no ignored or untracked scratch files. This final metadata-only checkpoint records those completed integration facts without changing the reviewed product.

PLAN-001 graph r3 and its 39 backlog tasks are unchanged and still have no current graph isolation approval. Historical records and failed candidate branches are preserved.
