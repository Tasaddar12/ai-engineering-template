---
phase: maintenance-issue87-auto-worktree
revision: ef325b62c0df6efcf603d72cfae55b8269a3052e
diff_base: 77b5668f2003bea60127d87e8785469286abafb3
status: issues_found
issue_refs: [87, 98]
---

# Independent review batch 1

All reviewers inspected the same clean frozen revision. No reviewer ran tests,
edited files, installed tools, published, committed or dispatched children.
This coordinator record preserves the joined findings and their evidence.
Source review: code-reviewer, gpt-6.1-sol/high, deep, 22 files; three BLOCKERs,
zero warnings. Integration: integration-checker, gpt-6-luna/medium.
Documentation: doc-verifier, gpt-6-luna/medium. Acceptance: verifier,
gpt-6.1-sol/high; [VERIFICATION](VERIFICATION.md) records gaps_found.

## CR-01: BLOCKER — native provider output uses the process locale

`prewrite.py:640` calls `print(native_create(payload))` without configuring
stdout. Creation and the created journal are already durable at `:586-593`.
`worktree-location.sh:55-58` forwards the output/status to the native host.
Legacy Windows stdout emits a non-UTF-8 path for representable accented text,
or raises UnicodeEncodeError for characters outside the codec. The host can
receive a corrupted path or failure after a checkout was created.

The consumer decodes the path as UTF-8 (`test_same_agent_worktree.py:94-98`),
but fixtures force PYTHONIOENCODING=utf-8 (`:254-260`; `test_install.py:697-703`).
Input is correctly binary/UTF-8 (`prewrite.py:626-629`); Git text is explicitly
UTF-8 (`:45-46`). This is the new output boundary, distinct from the deferred
generic Windows Workspace/Git locale issue.

Required: explicit UTF-8 one-path-line output and appropriate diagnostics;
legacy-codec/nonrepresentable-Unicode subprocess RED/GREEN using the actual
provider. Preserve created state; never blindly create again. AW-06/T-AW-03.

## CR-02: BLOCKER — four initializers route the shell before native entry

| Workflow | Initial locator-selected cd | Later native branch |
|---|---|---|
| discuss-phase | 159-166 | 224-234 |
| plan-phase | 75-82 | 115-124 |
| execute-phase | 124-131 | 166-175 |
| verify-work | 84-91 | 120-129 |

For an existing ordinary phase session, phase.locate selects its worktree.
The initializer prescribes cd and init there before open_session reaches the
new native branch. `workflow_request` requires the actual root to equal the
primary checkout (`prewrite.py:304-307`). Persistent shell-cwd semantics cause
prewrite-root refusal; treating shell selection as already-isolated skips the
required native movement. Command-local cd leaves contradictory context and
still violates the approved before-shell sequence.

The existing fixture manually bootstraps from primary
(`test_same_agent_worktree.py:502-517`); the six-consumer check only tests
strings (`:475-480`). Integration-checker and verifier independently confirmed
the failure. New-phase, quick and ship routes are not implicated by this
specific ordering defect.

Required: positive Claude bootstrap after read-only locator facts, before the
first session cd/destination initialization; native entry/default proof/Git
confirmation, then fresh destination inputs. Retain ordinary shell consumers.
Cover all four complete prescribed orderings. AW-01/02/06, T-AW-03.

## CR-03: BLOCKER — failed Git discovery grants the temp-note exemption

`prewrite.py:464-477` turns every nonzero rev-parse --show-toplevel result into
repository=None, then treats that as evidence for an external OS-temp note.
A real external temp repository with malformed .git/config or ownership
refusal passes plain-path checks, fails discovery and receives the exemption
without identity/ticket. Plain-path checks cover links, not repository metadata.
Existing nested-repository tests cover successful discovery only.

Required: distinguish established non-repository locations from discovery
failure/uncertainty and refuse the latter. Real external malformed-config
repository RED/GREEN must deny synchronously and preserve target bytes;
legitimate plain nongit temp create/update remains allowed. AW-03/05, T-AW-01.

## DOC-01: required correction — Python adapter wording

Initial four-document review counted 41 checked claims with no failures and
four explicit live-host conditions unverified. Its follow-up supersedes that
clean result: `.ai/hooks/README.md:88-90` says no Python hook adapter exists,
but `source-prewrite.sh:16` invokes `prewrite.py hook --host`, whose main
dispatches the adapter (`:631-644`). Narrow the wording to registered shell
entry scripts using a Python decision adapter. Preserve nearby host-folder and
Windows-launcher guidance. The other reviewed guide claims remain supported.

`worktree-sessions.md:51-53` correctly requires entry before shell routing;
repair CR-02 rather than weakening that contract. RULES review was limited to
Hooks and validation; other sections were unchanged.

## Integration and acceptance boundaries

The installed role/CLAUDE exports, advisory-first editing group, synchronous
source adapter, ticket, native callback, session adoption and six consumers
connect in source. `prewrite.confirm` reports host_binding_verified:false;
Git facts do not authenticate host movement, permissions or loaded context.

AW-01/04 live behavior remains unverified. AW-03/05/06 fail on the defects above.
AW-02 conditional gates, AW-07 bounded provider lifecycle and AW-08 evidence
discipline were verified at their declared boundaries. No actual native host
was available; the fixture explicitly supplies rebinding and later-turn state.

Original-six overlapping hunks were inspected against their frozen heads;
no obvious semantic incompatibility was found, but no actual combined-97
tree was built or tested in this batch. Earlier combined-originals evidence
does not prove composition with PR97. Advisory script and .planning are
byte-unchanged from main. No acceptance override, merge or issue closure.

## Correction assignment

After the whole batch joined, runtime created code-05 and docfix worktrees at
the reviewed revision. Coder owns the three source/test corrections; doc-writer
owns only README wording and DOCUMENTATION-SUMMARY. Their paths are disjoint.
Require genuine new RED/GREEN and affected independent rechecks after integration.
