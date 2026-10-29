# Tag a multi-repository milestone

Use a per-repository release map when `git.repo_tagging` is `per_repo` and the
project config contains `sub_repos`. The Engineer milestone version records the
planning milestone; each repository can use its own release tag.

Create a JSON map as an array, or as an object with a `repositories` array. Each
entry must name a configured sub-repository and tag:

```json
{
  "repositories": [
    {"repo": "backend", "tag": "v2.4.0", "ref": "HEAD", "message": "Backend 2.4.0"},
    {"repo": "frontend", "tag": "v3.1.0", "ref": "HEAD"}
  ]
}
```

`ref` defaults to `HEAD`; `message` defaults to `Release <tag>`. A null, false,
or empty `tag` skips that entry. The configured `git.create_tag: false` setting
also skips tag creation while retaining the map for the milestone archive.

Validate the complete map before writing any tag:

```bash
engineer_run query milestone.release-tags --map release-map.json --dry-run
```

Review the resolved commits and statuses. After one explicit confirmation of the
listed tags, run:

```bash
engineer_run query milestone.release-tags --map release-map.json
```

All configured repositories and refs are checked before the first tag is made.
Tags are annotated, local, and idempotent when the existing tag points to the
same commit. A tag already pointing elsewhere stops the operation. The result
reports `pushed: false`; the runtime never pushes. Ask separately before any
push, naming the repository, remote and tags to publish.

Archive the parsed map value with milestone completion by supplying
`--release-map release-map.json` to `milestone.complete`. The archived file is
`.planning/milestones/<version>-RELEASE-MAP.json`.
