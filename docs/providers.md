# Provider setup

The installed `.ai/framework.yaml` leaves providers disabled. Enable a provider deliberately, keep credentials outside the project, and configure the matching external-action authority in `.ai/constraints/permissions.yaml`. Codex dispatch needs provider execution authority; the shipped Codex entry also requires credentials and paid-service authority. Existing account authentication is used without storing tokens in project files.

On Linux, set `providers.codex.configured: true`, choose the installed Codex executable, and list the binary/tool runtime directories in `read_only_runtime`. The two `permissions_profiles` values are names for dynamically generated, restricted profiles. The framework supplies the profile definitions and disables network access and alternate tools inside agent execution.

Windows uses the Linux Codex binary through WSL. Add this mapping under `providers.codex`, set `executable` to its absolute Linux path, and list the corresponding Windows runtime directories under `read_only_runtime`:

```yaml
confinement:
  mechanism: wsl
  launcher: wsl
  distribution: Ubuntu-24.04
  mount_root: /mnt
```

The configured Linux executable must be inside one of those translated runtime directories. Native Windows confinement is explicitly unsupported. The shipped command policy includes the WSL provider launcher.

Assignments currently need existing directory scopes. Exact file-only Codex write grants are rejected; the follow-up is recorded in `.ai/bugs/open/BUG-002.md`. A Linux generic command bridge can instead use the configured bubblewrap adapter, with explicit request, response and worktree arguments.

Agent definitions under `.ai/agents` carry their own provider, model, reasoning and permissions. The default implementation roles use GPT-5.6 Sol with xhigh reasoning; critical review uses GPT-6 Astra with xhigh reasoning.
