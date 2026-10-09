# Scout usage contract

- **MUST dispatch `scout`** before unknown-location repository discovery or file/symbol
  search, and for requested inventories, extraction, classification, transformations
  or structured summaries of code, docs, logs or supplied output, even at known paths.
- Use the configured cheap scout model: resolve `scout` through `resolve-agent` for
  the selected host; pass its model and effort inline, omitting `inherit`.
- Give a bounded question, checkout/revision, relevant inputs (including dirty content),
  search scope and requested output. Require concise answers with path:line or input
  citations, inspected revision/scope, uncertainty and missing evidence.
- Reuse evidence when question, revision, scope and inputs match; batch compatible
  requests. Join results before using them, verify consequential citations, and ask
  only for uncovered or stale evidence. Do not repeat covered searches or add a scout
  for every read.
- The owning agent keeps reasoning, design, authoring and correctness decisions;
  directly inspect already-known source needed for those decisions or verification.
- Scouts are read-only leaves: propose transformations; never edit, run tests or
  project code, commit, write SUMMARY files, decide acceptance or spawn children.
- If nested spawning is unavailable, return the bounded request and resume point to
  the coordinator for dispatch. If it cannot dispatch either, report missing evidence
  and block only dependent work; do not silently perform required scout work yourself.
