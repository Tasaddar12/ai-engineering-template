# Verify Command Path Resolvability (#2401)

> Reference file for gsd-plan-checker agent. Loaded on-demand via `@` reference.

**Question:** Does each `<automated>` command's target directory actually resolve from the
executor's cwd (the project root)? Format sanity above asks whether the *pattern* can match;
this asks whether the command can *run at all*.

**Do not hand-reason the filesystem.** #2401 is precisely the failure of doing so: this
checker flagged a bad `cd ../../frontend` (correct), then prescribed two successively-wrong
replacement paths — the second citing a `package.json` that did not exist. Consume the
deterministic probe result, never re-derive it yourself.

`.ai/gsd/workflows/plan-phase.md` already runs the probe **before** spawning this checker and
interpolates the result into the verification prompt as `{VERIFY_PATHS}`, inside a
`<verify_command_path_probe>` block. This dimension reads that already-supplied JSON — it never
invokes `gsd_run check verify-command-paths` itself. If `{VERIFY_PATHS}` is absent from the
prompt, treat this dimension as silent (nothing to check) rather than trying to run the probe.

The probe never executes command text (PLAN.md is untrusted, LLM-authored). It recognizes two
grounded forms — a leading `cd <literal>` chain and `npm --prefix <literal>` — and refuses to
guess at anything else.

**Process:** for each row in `.commands`, act on `severity` only:

| `severity` | `reason` | Action |
|---|---|---|
| `blocker` | `missing_dir` / `no_manifest` | **BLOCKER** — quote `rawTarget` and `target` verbatim |
| `warning` | `dynamic_path` / `outside_root` / `script_missing` / `manifest_unreadable` | **WARNING** |
| `none` | — | silent |

Rules:
- **Report, never prescribe.** State the target that failed to resolve and what was missing.
  Choosing the replacement is the planner's job — it now receives the prior phase's proven
  commands (see `prior_verify_commands` in the planning context).
- `status: pending_creation` means an earlier task in this phase creates that directory. **Not
  a finding.** Say nothing.
- `unresolvable` means the probe could not ground the path (a variable, glob, substitution, or
  `~`). That is a WARNING, never a BLOCKER — and never a licence to guess the literal path.
- A non-empty `readError` means the probe **could not look**. Report that as a WARNING in its
  own words; it is not a clean bill of health.
- `MISSING …` sentinels are Dimension 8's business — this dimension stays silent on them.


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
