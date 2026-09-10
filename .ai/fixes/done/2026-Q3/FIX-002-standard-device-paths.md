---
tier: plan
authority: agent
id: FIX-002
title: Confinement hook rejects standard process device paths
found: 2026-09-10
found_by: user
severity: major
violates: none
links: []
deferred_until: none
---

# FIX-002: Confinement hook rejects standard process device paths

## Symptom

The confinement hook denies ordinary device I/O such as redirects to
`/dev/null`, `/dev/zero`, `/dev/stdout`, `/dev/stdin`, `/dev/stderr`, numeric
paths under `/dev/fd/`, and `/dev/tty` when the checkout is elsewhere.

## Root cause

`inside()` in `.ai/hooks/worktree-confine.sh` treats every absolute path as
a regular filesystem destination and recognizes only the checkout, shared
Git directory and scratch directory.

## The change

Recognize standard stream device paths and numeric process file descriptors
before applying the existing checkout boundary checks.

## Proof

`test_standard_devices_are_allowed` in `tests/test_worktree_confine.py`
passes each standard device and numeric descriptor to the actual Bash hook
through both a file-tool request and a shell redirect request. The test sends
JSON only; it does not execute the device I/O commands.

Before the hook change at base `1f3f6d6cbb4a98c95809e5328648da8007ed01ca`,
`python -B -m unittest discover -s tests -p test_worktree_confine.py -v`
reported 13 false denials:

```text
Ran 5 tests in 22.734s
FAILED (failures=13)
```

After the hook change, the same command returned:

```text
Ran 5 tests in 34.131s
OK
```

`test_device_exemption_keeps_normal_paths_confined` checks that device-name
prefixes, nonnumeric descriptors, descriptor child paths, case mismatches,
ordinary outside paths and traversal away from a device are still denied.

## Contract

The user explicitly requires standard device paths, including the stream
aliases, `/dev/fd/*` and `/dev/tty`, to be accepted. Ordinary paths outside
the worktree remain subject to confinement. No documentation or contract
correction is required.

- Related documentation/contract INTAKE: none
