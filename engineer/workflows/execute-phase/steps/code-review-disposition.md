Apply response_language to all user-facing prose; preserve code, paths and identifiers.

# Code review disposition — advisory runtime ledger

Read only from code-review-fix.md at record_disposition. Execute-phase owns a separate blocking frozen code_review_gate and never consumes this ledger as a waiver. Consume the validated PHASE_DIR and PHASE_NUMBER from initialization. Use the invoking workflow's identity-checked Python standard-library runtime.

The counts say how many findings there were; this sibling artifact records what happened to each one. REVIEW.md belongs to code-reviewer and is overwritten by re-review, so decisions live in the separate NN-REVIEW-DISPOSITION.md. Advisory means recording failure is visible and never substitutes for required fixes, checks, verification or acceptance.

```sh
engineer_run query review.disposition --phase "$PHASE_NUMBER" --phase-dir "$PHASE_DIR"
```

The verb validates the whole phase identifier before constructing any path, pads only its leading digit run as a string, and accepts the optional uppercase letter and any number of dotted digit axes. Examples: 3 -> 03, 3.1 -> 03.1, 23.1.2 -> 23.1.2, 3A -> 03A, 0008A.1 -> 0008A.1. Each digit component is limited to eight digits; the complete output filename also has a 255-byte limit. Empty, traversal, malformed, oversized or unavailable inputs yield a reported advisory skip without writing a guessed path.

Display review_status, review_counts and review_counts_ok from this result: print the severity breakdown only when all four counts are decimal numbers and mutually consistent. For a present review without a parseable status, say unparsed and counts unavailable; absent/clean/skipped reviews need no warning. A malformed count is never repaired by deleting internal whitespace or truncating at a colon. Only the closed leading frontmatter findings mapping owns these counts; critical and blocker are equivalent. ASCII whitespace trimming is deliberate and locale independent.

Display status, open/total, unparsed, every dropped decision and stale_fix entry, and message on skip. A dropped decision means the ID now names a different title; a mismatched fix title may reflect stale evidence or a retitled finding, and the runtime does not guess which. A declared finding with no recognized heading is explicitly unparsed, including a zero-row ledger when every heading is unrecognized.

The verb reads the final REVIEW-FIX.md then every exact REVIEW-FIX.iterN.md backup in descending numeric pass order. First applicable outcome wins. It returns consumed_passes with exact paths and SHA-256 digests plus review_digest. A caller holding that returned review digest may supply --review-digest DIGEST on a subsequent reconciliation to refuse intervening source drift. Consume and retain this packet before retiring any backup; the verb performs no cleanup. Its hashes bind the normalized UTF-8 report text that was actually joined, not a claim of verified repairs.

An unchanged semantic ledger retains its recorded timestamp and bytes. If commit_docs is true, commit only the returned exact path after status recorded and confirming a regular non-link file, using the canonical commit message/body. A skipped write is never followed by committing an unrelated existing path. The workflow owns publication; the writer itself only records the ledger.

## Port design notes and retained edge-case examples

The following detailed notes preserve the copied walker's full behavior and examples. The named JavaScript expressions identify the upstream algorithm for comparison; they are historical labels, not executable commands or required helpers. The working implementation is engineer/bin/lib/review_disposition.py through review.disposition above. No Node command is executed.
**Before `(function main() {`**

The runtime returns a structured result; the CLI prints it and exits normally. The upstream algorithm ran inside main() and returned rather than explicitly exiting. The script
prints its one-line verdict and then ends; with an explicit exit directly after console.log,
the exit can pre-empt the write when stdout is a pipe or socket (Node documents those writes
as asynchronous on POSIX), and the caller then sees an exit 0 with NO verdict line. A
hardening against that documented hazard, not a reproduced defect: the 'unchanged' branch was
the only one that exited explicitly, and the empty stdout that first pointed at it turned out to
be a reviewing sandbox's own. A function that returns lets the event loop drain stdout before
the process ends. Same exit status either way.

**Before `if (fs.existsSync(process.env.DISPOSITION_FILE) && !fs.lstatSync(process.env.DISPOSITION_FILE).isFile()) {`**

AN EXISTING LEDGER THAT IS NOT A REGULAR FILE IS NOT A LEDGER. Checked FIRST, before any read
or write of that path, and the ordering is the fix rather than a tidy-up:
  * writeFileSync FOLLOWS a symlink, so a planted link replaced the contents of whatever it
    pointed at -- outside the phase directory, link left intact so nothing looked wrong;
  * a FIFO at that path made readFileSync BLOCK FOREVER, which is the one behaviour a gate
    documented as advisory and non-blocking must never have;
  * and the unchanged-run fast path read the file before the check, so a symlink whose
    target already matched slipped through reporting 'unchanged'.
All three driven. lstatSync does not follow the link, which is why it is the right call.
NAMED RESIDUAL, not silently accepted: this is a check-then-write, so a symlink planted
between the lstat and the write still wins. Node exposes no portable O_NOFOLLOW write, and
an attacker who can write into the phase directory mid-run already has what the check would
protect. It narrows a real accident; it is not a security boundary, and the docs do not
claim one. A hard link likewise passes isFile() by construction.

**Before `let fence = null;`**

The OPEN fence's marker is remembered, not just the fact of being fenced. A bare toggle
treats every fence marker as interchangeable, so a ~~~ line inside a ` ` ` block CLOSES it
and the block's real close REOPENS one — which silently swaps a fenced example for the
real findings around it. Driven: a review quoting ~~~ inside a fenced example recorded
the EXAMPLE's id and dropped the real finding entirely. Per CommonMark, a fence closes
only on the same character, at least as long as the one that opened it.

**Before `const SECTION_SEV = [[/^##\s+Critical Issues\s*$/, 'critical'], [/^##\s+Warnings\s*$/, 'warning'], [/^##\s+Info\s*$/, 'info']];`**

SEVERITY COMES FROM THE SECTION FIRST, the recorded ledger value second, the id prefix
third (the full precedence is at sev(), below the identity check). The section heading is the
reviewer's OWN statement of a finding's severity -- code-reviewer.md emits findings under
'## Critical Issues' / '## Warnings' / '## Info' -- and this walker already visits every line,
so the signal was in hand and discarded. Deriving from the prefix alone means a reviewer who
mis-numbers a Critical as WR-04 while filing it under '## Critical Issues' gets a ledger row
reading 'warning', which then disagrees with the review it summarizes AND with the frontmatter
count line block 1 prints from findings.critical. The Severity column is the whole basis for
triaging the ledger, so it has to agree with the document it describes.
Matched WHOLE, exactly as the fix-report sections are: a prefix match would let a heading like
'## Critical Issues Verification' re-tier everything under it.

**Before `const declaredTotal = /^[0-9]+$/.test(process.env.REVIEW_TOTAL || '') ? Number(process.env.REVIEW_TOTAL) : null;`**

A review that reports nothing still has to reconcile an EXISTING ledger: its decided rows
and its untriaged rows are BOTH carried, marked. Exiting here would freeze a stale ledger
showing findings as open that the review no longer reports.
A fix report with no ledger is also something to record: a converged '--auto' run has neither,
and exiting here recorded nothing for a fully fixed phase.
A review that reports findings NONE of which this parser understood is also something to
record, and it is the case with the least evidence anywhere else. The shortfall is derived
HERE, above the guard, rather than at its old site beside the render: order is final from
the heading walk above and never grows again, so the value is the same either way -- but at
the old site it was computed AFTER this return had already fired, so it could not reach the
one exit that discards it. Partial shortfalls (some findings parsed, some not) always
reported, which is exactly why the total one read as covered.

**Before `const prior = new Map();`**

Prior rows: keep the disposition AND its source cell — the source is where a human writes
the reason a finding was deferred, and rewriting it would discard the very thing the
'set deferred by hand, with the reason' instruction asks for. The Source cell is the LAST
column, so it is captured through to the end of the line, less an optional trailing pipe:
a bare | inside it is prose, not a column break. The previous capture admitted a pipe only
when escaped, and the whole-line match then FAILED on a bare one -- a human who wrote
'waiting on team A | team B' as a deferral reason had the row not match at all, the finding
reset to open, and the reason destroyed: a triaged Critical rendered indistinguishable from
one never seen, off an ordinary typo in the one field this ledger asks a human to hand-edit.
The render below escapes a bare pipe on the next write, so the file converges to the escaped
form either way. The trailing pipe is optional so a hand-mangled row loses no decision.

**Before `const SEV_VOCAB = ['critical', 'warning', 'info'];`**

SEVERITY, READ BACK. The ledger has always WRITTEN a severity for every row -- in the table's
Severity cell and in the frontmatter's 'severity:' key -- and until this map existed nothing
read either back: the row regex discarded the cell as [^|]*, the frontmatter walk collected
only titles, and a CARRIED row was rebuilt through sev() from the id prefix, because
sectionSev holds only findings the CURRENT review reports. So a WR-04 the reviewer filed under
'## Critical Issues' was recorded 'critical', a human deferred it, and the next run -- the
review no longer reporting it -- silently re-recorded it 'warning'. The one artifact whose
purpose is remembering a finding's severity lost it on the second run, in the unsafe
direction. Driven by executing the shipped script twice (round 11).
The table cell is read first (it is the human-facing surface, and the one the disposition
already comes from); the frontmatter key is the fallback for a hand-mangled cell. Both are
ENUM-validated -- a value outside critical|warning|info is not a severity and is ignored, so
the row falls through to inference rather than carrying garbage (ADR-227, the same rule the
disposition column takes).

**Before `const m = l.match(/^\|\s*((?:CR|BL|WR|IN)-\d+)\s*\|\s*([^|]*?)\s*\|\s*(open|fixed|skipped|deferred)\s*\|\s*(.*?)\s*\|?\s*$/);`**

The disposition column is an ENUM, not 'any lowercase token'. ADR-227 requires a trust
boundary to validate semantic SHAPE, not merely type, and to coerce a failure to the
contract's safe default -- and this ledger is a trust boundary by construction, because
the rendered instruction tells a human to hand-edit it. Under the old ([a-z]+) capture a
single transposed character ('opne') was stored as a decision: it is not 'open', so it
beat the default, was excluded from the open: headline count, and was carried forward
forever. One typo and the ledger reported a phase fully triaged.
Note the asymmetry that made this a correctness bug rather than a style point: a typo
OUTSIDE [a-z] ('Deferred') already failed to match, lost the decision and reset the row
to open -- safe. A typo INSIDE [a-z] was unsafe. The parser failed open in the one
direction that matters. A row that does not match now yields no prior entry, so the row
falls back to 'open' -- the safe default, by the same path the capital-D case took.
The Severity cell is CAPTURED, not skipped: it is the value the carry-forward below has to
preserve, and skipping it (the previous [^|]*) is how a carried row lost its tier.

**Before `if (m) {`**

Strip the carried marker before storing: it is rendered from the carried flag, so
leaving it on the stored value would re-append it every run — the cell grows without
bound AND the file changes on every run, defeating the unchanged-run check below.
Strip AT MOST ONE trailing marker, unconditionally. Storing the cell verbatim looked
like the way to stop the strip eating human text, and it introduced a worse defect:
once the generated marker is stored it can never leave, so a carried finding that
REAPPEARS in a later review still renders 'not in the current review' -- a ledger that
is now factually wrong about its own contents. The residual ambiguity is irreducible
(a reason ending in exactly that phrase is indistinguishable from the marker) and it
costs nothing real: on a carried row the render puts the phrase straight back, and on a
current row the phrase was self-contradictory to begin with. The unbounded quantifier is
what had to go, not the strip itself.

**Before `const sameTitle = (a, b) => String(a === undefined ? '' : a).replace(/\s+/g, ' ').trim()`**

TITLE COMPARISON, and its FALSE-POSITIVE mode, which was previously unacknowledged.
The strict instinct is right -- ids are reused across re-reviews, so a stale REVIEW-FIX.md
must not mark a brand-new CR-01 as already fixed -- but code-fixer.md writes
'### {finding_id}: {title}' under no contract that the title is copied byte-for-byte from
REVIEW.md. A fixer that REFLOWS a long title produced a spurious stale note, left a
genuinely-fixed row 'open', and told the reader the fix report named a different finding.
Runs of whitespace are collapsed because re-spacing carries no information. The BOUND, stated
because it is easy to over-read this: a title WRAPPED across lines is NOT reconciled. A '###'
heading is one line by definition, so the continuation is a separate paragraph the heading
parser correctly never captures, and collapsing whitespace cannot reach across that boundary.
Not widened -- absorbing whatever follows a heading into the title would swallow arbitrary
prose and make this very check meaningless. Case changes and truncation stay strict too --
they are the shapes a genuinely different finding actually takes, and widening to them would
trade this false positive for the silent false NEGATIVE the strict match exists to prevent.
Residual, stated: a fixer that re-cases or truncates still produces a spurious note. That is
the safe direction (a visible note, not a silent wrong 'fixed'), and the note's wording below
no longer asserts which of the two it is.

**Before `if (h.id && sect && !applied.has(h.id)) {`**

First occurrence wins, so an id listed under BOTH sections is not decided by row order.
And the fix report must name the SAME finding: ids are reused across re-reviews, so a
stale REVIEW-FIX.md would otherwise mark a brand-new CR-01 as already fixed.
A title mismatch is the STALE-report case and must not pass silently: the id is
reused, the finding is not, and a reader who sees the row stay 'open' has no way to
tell that from 'the fix report never mentioned it'. Record it and say so below.

**Before `const sev = (id) => sectionSev.get(id) || (priorSev.has(id) && sameFinding(id) ? priorSev.get(id) : prefixSev(id));`**

SEVERITY PRECEDENCE: the current review's SECTION (the reviewer's own statement, this run),
then the severity this ledger RECORDED (an earlier reviewer's statement, persisted), then the
id PREFIX (an inference). A recorded value is inherited only while the id still names the
SAME finding -- the identity rule the disposition already obeys -- so a reused id starts from
its own review's section or its prefix, never from the finding it replaced. A carried row is
absent from the current review, so sameFinding() is true for it by construction and its
recorded severity is what it keeps. Defined here, below the identity check, because it
depends on it.

**Before `const carriedIds = [];`**

A prior finding the current review no longer reports is CARRIED, never dropped -- and that
now holds for UNTRIAGED rows too, which is the correction. Carrying only decided rows meant
an untriaged row for a dropped or renumbered finding disappeared without trace, and combined
with the reconciliation gap that left EVERY row untriaged, a re-review silently deleted the
whole ledger. The --auto loop rewrites REVIEW.md on every iteration, so it does not retain it
either: run 1 records CR-01 open, the re-review renumbers it to CR-02, and run 2's ledger
contains neither. That is #3829's complaint verbatim -- 'no trace of what happened to them' --
reproduced by the artifact built to prevent it, and 'nothing was decided about it' is exactly
the state #3829 says must leave a trace.
The carried marker is what keeps this honest rather than merely additive: the row does not
claim the finding is live, it records that it was seen and never triaged. Stated cost, since
it is real: a RENUMBERED finding appears twice until someone triages the old row, and a
carried untriaged row persists across runs until decided. Both are bounded by the phase's own
findings, both are legible from the marker, and both are strictly better than a silent delete.
Prior rows UNION ids a fix report decided that the review no longer reports: a decision the
ledger cannot render is a decision lost. Precedence matches row() -- applied beats recorded.

**Before `const reusedNote = reused.length ? ' (' + reused.length + ' recorded decision(s) DROPPED -- the id now names a different finding, so the decision no longer has a row: ' + reused.join(', ') + ')' : '';`**

Surfaced, not thrown: the gate is advisory. But a fix report naming a finding whose title
no longer matches is the one case where 'open' understates what is known, so it is stated.
The wording no longer ASSERTS a stale report. Both causes reach here -- a genuinely different
finding under a reused id, and a fixer that re-titled the same one -- and the step cannot tell
them apart, so it reports the observation rather than a conclusion it has not earned.
On the console too, for a reader who never opens the ledger.

**Before `if (rows.length === 0 && !unparsed && !fs.existsSync(process.env.DISPOSITION_FILE)) return;`**

RECONCILE THE TWO PARSERS. The counts come from REVIEW.md's frontmatter; the rows come from
heading matches against a CLOSED CR|BL|WR|IN alternation. A finding the heading parser cannot
match -- a fifth prefix, a missing ': ' separator, a '#### ' heading -- contributed no row, no
note and no diagnostic, and the ledger then declared 'open: 3 of 3' over a set strictly
smaller than the console line reported one paragraph earlier. Two findings recorded nowhere,
and neither artifact said so.
The earlier argument for the closed alternation -- that an unlisted prefix produces no row
rather than a MIS-CLASSIFIED one -- is the wrong trade under this repo's own fail-safe rule:
a dropped finding is demoted below every finding that parsed, and an unparseable finding is
precisely the one a human most needs to see. Surfaced, not thrown, exactly as the stale
fix-report case above is: the gate stays advisory and states the shortfall.
The !unparsed conjunct here is the SECOND of the two exits that discarded the shortfall, and
it is not redundant with the one above: that guard keys on order and stands down when a fix
report exists, so a run with a fix report and no parseable finding reaches THIS line with
rows.length 0. Both exits now decline to fire while a shortfall is outstanding, and the
result is a zero-row ledger carrying an unparsed key -- an honest record that the review
declared findings and none of them were understood, which is strictly better than the file
not existing. A genuinely clean review is untouched either way: a declared total of 0 is not
greater than order.length, so unparsed is 0 and both returns still fire.

**Before `const escapePipes = (t) => t.replace(/\\.|\|/g, (m) => (m === '|' ? '\\|' : m));`**

A bare | in a Source cell is escaped on render so the table stays a table. Scanned as PAIRS,
not by the preceding character: an escaped pair (backslash + anything) is kept verbatim and only
a pipe outside one is escaped. The previous form, /(^|[^\\])\|/g, CONSUMED the character before
the pipe, so adjacent bare pipes were escaped one per run (A||B -> A\||B -> A\|\|B, a third run
to converge) and an escaped backslash before a pipe (A\\|B) hid the pipe behind the wrong
parity and left it bare. Found by the round-3 adversarial pass, not by the property -- whose
generator then emitted at most one bare pipe, the one case the old form got right; it now
reaches adjacent pipes and both backslash parities, against an independent parity oracle.

**Before `fs.writeFileSync(process.env.DISPOSITION_FILE, render(new Date().toISOString()));`**

READ-MODIFY-WRITE, NO LOCK. The ledger is rendered whole from a read taken above, and nothing
serializes two writers: the historical step had two dispatchers (execute-phase's gate and
code-review-fix's record_disposition) plus a human the legend invites to hand-edit, so a
lost update is a real window, not a theoretical one. Same shape as #3780 (WINDOWS.md
append under parallel executors), which #4681 closed with a cross-process lock in
src/broken-windows.cts. NOT taken here: this is a shell-embedded script with no build
dependency on the compiled tree, and adopting the lock module is its own change. Residual,
stated in docs/features/code-review-pipeline.md; not reproduced as a lost update.


### Python port safety and ownership

The Python writer strengthens the historical regular-file fence: the phase directory and all input/output ancestors must remain inside the repository and contain no symlink or Windows reparse point. Existing output must be a regular file, never a directory, FIFO or link. It writes only the exact validated ledger through an atomic sibling temporary file and replacement, then removes only its own temporary file. Hard links are replaced rather than opened for truncation. No pass report, source review, directory or worktree is deleted.

The historical check-then-write and read-modify-write notes above describe the original Node implementation. The Python port revalidates the destination immediately before replacement, but it does not claim resistance to a concurrent attacker swapping ancestor directories. The coordinator must serialize ledger writers and human edits; it must retain backups on missing/degraded evidence. The only current dispatcher is code-review-fix record_disposition; execute-phase's frozen gate remains independent.