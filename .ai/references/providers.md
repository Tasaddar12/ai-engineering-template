# Provider identity

The runtime resolves the origin before provider calls. GitHub remains the default
for `github.com`; `gitlab.com` is also recognized. Other GitLab hosts require an
explicit mapping in `.planning/config.yaml`:

```yaml
delivery:
  provider: auto # auto, github or gitlab; an explicit choice must match origin
  gitlab_hosts:
    gitlab.example.test: https://gitlab.example.test:8443
```

Mapping keys are lowercase origin hostnames. Values are credential-free HTTPS
web bases without a path. HTTPS origins must match the configured authority.
SSH origins use the mapped web/API port, independently of their SSH transport
port. Supported forms include `git@host:group/subgroup/project.git`,
`ssh://git@host:2222/group/subgroup/project.git`, and
`https://host:8443/group/subgroup/project.git`.

Unknown hosts, mismatched providers, credentials, query/fragment components,
encoded or traversing project paths and unsupported URL shapes fail before CLI
execution. GitHub retains its two-component project path and no-port rule.

`lib.providers.resolve(workspace, cwd=None)` returns a dictionary containing
`provider`, `host` (web authority), `project`, `remote`, `web_url` and `repository`
(web authority/project). Resolution is offline.
`item_number(target, url, kind='issues')` validates exact project ownership;
GitLab uses `/-/issues/IID` and `/-/merge_requests/IID`.

TODO publication uses authenticated `glab api` calls pinned to the resolved host
and URL-encoded full project path. Preview includes all issue states and related
MR context. The existing reviewed publication state machine owns creation,
reuse, readback, linkage and recovery. Completion performs a fresh closed-status
read only when explicitly requested. No remote close/reopen, issue-body updates
or polling are performed. Diagnostics stay local and generic errors preserve
pending TODO context. Authenticate `glab` separately; runtime does not change
credentials.
