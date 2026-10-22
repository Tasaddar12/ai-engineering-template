# Screenshot scope and capture scaffold

Read [coverage ownership and validation](../references/ui-screenshots.md). Replace
the example inputs below from the approved PLAN and consumer sources. Write scope
separately from the producer's capture manifest in the existing browser harness.

## Planned scope JSON

Fill revision, acceptance IDs, routes, states, procedures, resolved URLs and
viewport bounds from PLAN and source. For `local`, set `affected_routes` to every
affected route. For `shared` theme/layout/token/component changes, fill `routes`
with ALL dependent routes; every listed route requires capture.

```json
{
  "schema": 1,
  "revision": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "change_kind": "shared",
  "affected_routes": ["settings"],
  "routes": [
    {
      "route": "home",
      "url": "http://localhost:3000/",
      "criteria": ["A-01"],
      "states": {"default": "Open home with fixture account; wait for heading"},
      "viewports": {"wide": {"width": 1280, "height": 800}}
    },
    {
      "route": "settings",
      "url": "http://localhost:3000/settings",
      "criteria": ["A-02"],
      "states": {
        "default": "Load fixture settings; wait for form",
        "error": "Reject fixture save; wait for error banner"
      },
      "viewports": {
        "wide": {"width": 1280, "height": 800},
        "narrow": {"width": 360, "height": 800}
      }
    }
  ]
}
```

Include each required criterion × state × viewport cell. If scenarios need
different state/viewport sets, split route entries with distinct stable IDs.
Record exclusions in PLAN; retain required cells after capture failures. Use
resolved URLs with test query parameters. Exclude credentials and sensitive data.

## Single producer interface

Resolve the selected host's installed runtime directory. Set `runtime_directory`,
`scope_file`, `expected_revision`, `private_artifact_directory` and `manifest_file`
to actual consumer inputs. Implement `capture` with existing browser tools,
fixtures and screenshot API before running this scaffold:

```python
import json
import sys
from pathlib import Path

sys.path.insert(0, str(runtime_directory))  # actual installed runtime directory
from lib.ui_screenshots import produce, read_json

scope = read_json(scope_file)

def capture(requirement, target_path):
    # Implement with the consumer's EXISTING browser harness:
    # 1. Assert the served build/test checkout is requirement["revision"].
    # 2. Set exact width/height; navigate to requirement["url"].
    # 3. Execute the named state procedure with deterministic fixtures.
    # 4. Assert resolved URL/state/readiness; record actual failures by raising.
    # 5. Write the browser's screenshot bytes to target_path.
    raise NotImplementedError("Wire the actual consumer browser harness")

manifest = produce(scope, expected_revision, capture, private_artifact_directory)
Path(manifest_file).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
```

Save the producer's `schema`, `revision` and `captures`. Each capture includes
the requirement fields, `result`, `artifact`, `sha256` and optional `error`.
The producer calls `capture` once per required cell with a fresh filename and
hashes the written bytes. If capture fails, retain `result: failed` and its error;
continue remaining cells. Record success only for actual browser captures.

Save private scope, manifest and images outside Git. Use absolute artifact paths
or paths relative to the manifest directory. Give validators access to image bytes;
if bytes are inaccessible, keep the capture unverified. Publish raw images/logs
only when requested.
