# Phase Argument Parsing

Parse and normalize phase arguments for commands that operate on phases.

## Extraction

From `$ARGUMENTS`:
- Extract the phase token according to the command's argument contract.
- Extract flags (prefixed with `--`) independently of the phase token.
- Remaining text is a description for add/insert operations.

## Using engineer_run

The `find-phase` command handles normalization and validation in one step:

```bash
PHASE_INFO=$(engineer_run query find-phase "${PHASE}")
```

Returns JSON with:
- `found`: true/false
- `directory`: Full path to phase directory
- `phase_number`: Normalized number (e.g., "06", "06.1")
- `phase_name`: Name portion (e.g., "foundation")
- `plans`: Array of PLAN.md files
- `summaries`: Array of SUMMARY.md files

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
