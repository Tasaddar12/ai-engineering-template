# Closed-Phase Gate (#3569)

The init JSON includes `phase_status` — one of `Pending | Planned | In Progress | Executed | Complete | Needs Review`. `Complete` means the phase has all summaries AND a `VERIFICATION.md` with `status: passed`. Replanning a closed phase silently rewrites plan docs that no longer match the shipped code, so the workflow must hard-stop here unless the operator explicitly overrides.

Parse `phase_status` from the init JSON, then:

```bash
FORCE_REPLAN=false
if [[ "$ARGUMENTS" =~ (^|[[:space:]])--force([[:space:]]|$) ]]; then
  FORCE_REPLAN=true
fi

if [ "${phase_status}" = "Complete" ]; then
  if [[ "$ARGUMENTS" =~ (^|[[:space:]])--reviews([[:space:]]|$) ]]; then
    # --reviews on a closed phase is never legitimate — concerns belong in a
    # new phase or issue against the closed phase's commits.
    cat <<EOF >&2
Phase ${phase_number} (${phase_name}) is already CLOSED (VERIFICATION status: passed).
/gsd:plan-phase --reviews cannot replan a closed phase. If the review surfaced
real concerns, open a follow-up phase or file an issue against the closed
phase's commits. There is no --force override for --reviews on a closed phase.
EOF
    exit 1
  fi
  if [ "$FORCE_REPLAN" != "true" ]; then
    cat <<EOF >&2
Phase ${phase_number} (${phase_name}) is already CLOSED (VERIFICATION status: passed).
Replanning a closed phase will overwrite plan docs that no longer match the
shipped code. If you intentionally want to replan over closed work, re-run
with: /gsd:plan-phase ${phase_number} --force

Otherwise, to view what shipped, see: ${verification_path}
EOF
    exit 1
  fi
  # FORCE_REPLAN=true: continue, but emit a banner so the operator sees the
  # decision in the transcript and in any committed plan docs.
  echo "WARNING: Replanning CLOSED phase ${phase_number} under --force. Verify the closeout was wrong before committing new plan docs." >&2
fi
```

The gate fires only on `Complete`. `Executed` and `Needs Review` are not gated — those states mean planning was finished but verification did not pass, and replanning is a legitimate next step.


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
