# Phase Argument Parsing

Parse and normalize phase arguments for commands that operate on phases.

## Extraction

From `$ARGUMENTS`:
- Extract phase number (first numeric argument)
- Extract flags (prefixed with `--`)
- Remaining text is description (for insert/add commands)

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

## Normalization

Use the runtime result rather than reimplementing phase parsing in shell. `find-phase`
returns `phase_number` in its normalized form and reports whether the phase exists:

```bash
PHASE_INFO=$(engineer_run query find-phase "$PHASE")
PHASE_NUMBER=$(printf '%s' "$PHASE_INFO" | engineer_run query json.get --field phase_number --raw)
```

For example, an integer phase `8` is reported as `08`; a phase `2.1` is reported as
`02.1`. If lookup fails, stop and report the CLI error rather than guessing a spelling.

## Validation

Use `roadmap get-phase` to validate phase exists:

```bash
PHASE_CHECK=$(engineer_run query roadmap.get-phase "${PHASE}" --pick found)
if [ "$PHASE_CHECK" = "false" ]; then
  echo "ERROR: Phase ${PHASE} not found in roadmap"
  exit 1
fi
```

## Directory Lookup

Use `find-phase` for directory lookup:

```bash
PHASE_DIR=$(engineer_run query find-phase "${PHASE}" --raw)
```
