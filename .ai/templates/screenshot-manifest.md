# Screenshot scope and capture scaffold

Use this scaffold in the consumer project's existing browser test harness. Read
[coverage ownership and validation](../references/ui-screenshots.md). This is a
fixture-shaped format example, not a claim about a real application or capture.
Keep the scope separate from the producer's output so omitted captures stay visible.

## Planned scope JSON

Replace the revision, complete dependent route inventory, acceptance IDs, states,
procedures, URLs and viewport bounds from the approved PLAN and inspected sources.
For `local`, `affected_routes` selects changed routes. For `shared` (theme, layout,
tokens or shared components), every route in `routes` requires capture; populate it
with ALL dependent routes, including routes unaffected by the local screen edit.

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

Each selected route expands criteria × states × viewports. Use only applicable
combinations: split route entries with distinct stable IDs when scenarios need
different viewport/state sets. Explain exclusions in the PLAN; never omit required
coverage because a capture failed. Use exact resolved URLs, including test query
parameters. Keep credentials and sensitive fixture values out of evidence.

## Single producer interface

Adapt this Python shape inside the consumer harness; resolve the installed runtime
path for the selected host, rather than importing an invented production package.
The callback uses the consumer's real browser tools, fixture setup and screenshot
API. No browser dependency is bundled in this workflow template.

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

The producer invokes the callback once per required criterion/route/state/viewport,
uses a fresh artifact filename, computes SHA-256 from the written bytes and records
`result: captured` or `result: failed` with the error. It continues after individual
failures. The output contains `schema`, `revision` and `captures`; each capture
contains all requirement fields plus `result`, `artifact`, `sha256` and an optional
`error`. Do not manufacture successful records for unavailable browser sessions.

Save scope, manifest and images outside Git when private. Absolute local paths and
paths relative to the manifest directory are valid artifact references. Consumers
need access to those bytes to validate the digest; a private inaccessible reference
stays unverified. Publication of raw images or logs is never required.
