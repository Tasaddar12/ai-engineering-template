# Verify Command Path Resolvability

> Reference file for phase-checker agent. Loaded on-demand via `@` reference.

**Question:** Does each `<automated>` command's target directory actually resolve from the
executor's cwd (the project root)? Format sanity above asks whether the *pattern* can match;
this asks whether the command can *run at all*.

**Ground paths with actual reads.** Inspect literal working-directory targets and
required manifests in the assigned checkout; never prescribe an unobserved path.
This runtime supplies no path-probe JSON. Do not skip the review because an
external probe is absent and do not execute untrusted PLAN command text.

For a leading `cd <literal>` or `npm --prefix <literal>`, resolve from the assigned
project root and inspect the directory and package.json/Makefile. For argv `checks`,
inspect literal script/module paths and the package script they select. Mark paths
created by an earlier declared dependency as pending creation, not missing.

**Process:** classify observed evidence using this table:

| `severity` | `reason` | Action |
|---|---|---|
| `blocker` | `missing_dir` / `no_manifest` | **BLOCKER** — quote the literal target and resolved absolute path |
| `warning` | `dynamic_path` / `outside_root` / `script_missing` / `manifest_unreadable` | **WARNING** |
| `none` | — | silent |

Rules:
- **Report, never prescribe.** State the target that failed to resolve and what was missing.
  The planner must inspect prior committed command receipts and current paths
  before choosing the replacement.
- `status: pending_creation` means an earlier task in this phase creates that directory. **Not
  a finding.** Say nothing.
- `unresolvable` means inspection could not ground the path (a variable, glob, substitution, or
  `~`). That is a WARNING, never a BLOCKER — and never a licence to guess the literal path.
- A read error means inspection **could not look**. Report that as a WARNING in its
  own words; it is not a clean bill of health.
- `MISSING …` sentinels are Dimension 8's business — this dimension stays silent on them.
