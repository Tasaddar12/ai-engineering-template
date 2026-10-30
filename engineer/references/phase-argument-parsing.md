# Phase Argument Parsing

Parse and normalize phase arguments for commands that operate on phases.

## Extraction

From `$ARGUMENTS`:
- Extract the phase token according to the command's argument contract.
- Extract flags (prefixed with `--`) independently of the phase token.
- Remaining text is a description for add/insert operations.

## Canonical lookup

Use `find-phase` to normalize the phase identifier, validate the roadmap entry, and locate its directory in one call:

```bash
PHASE_INFO=$(engineer_run query find-phase "${PHASE}" --raw)
```

The result includes the found status, directory, phase number/name, plans, and summaries. Prefer this runtime lookup to hand-written normalization or filesystem globs.

## Validation

Fail clearly when `found` is false:

```bash
PHASE_CHECK=$(engineer_run query find-phase "${PHASE}" --pick found)
if [ "$PHASE_CHECK" = "false" ]; then
  echo "ERROR: Phase ${PHASE} not found"
  exit 1
fi
```

## Directory lookup

Read the canonical directory from the same resolver:

```bash
PHASE_DIR=$(engineer_run query find-phase "${PHASE}" --pick directory)
```
