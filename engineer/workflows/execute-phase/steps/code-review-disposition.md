Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

# `code_review_gate` — report the review and record a per-finding disposition

Read and executed by the `code_review_gate` step of `execute-phase/steps/verify-phase-goal.md` (the shared verification action `execute-phase.md`'s `verify_phase_goal` runs), immediately after code review
returns. It consumes `PHASE_DIR` and `PHASE_NUMBER` and derives everything else.

It lives here rather than inline in the parent because `execute-phase.md` sits against two size
ceilings — the XL hard cap in `tests/workflow-size-budget.test.cjs` and the frozen ADR-857
pre-phase-6 ceiling in `tests/claude-orchestration.test.cjs` — and both are red lines to be kept
under, not budgets to spend.

**What it is for.** The counts the gate prints say how many findings there were, not what happened
to any of them. Without a record, the phase directory carries no answer to *what happened to CR-01*
and a phase can reach `phase.complete` with a Critical standing and no trace it was ever seen.

**Why a sibling artifact rather than a section inside REVIEW.md.** `--auto`'s re-review loop
rewrites REVIEW.md on every iteration, so a ledger kept inside it would not survive the next pass;
and REVIEW.md has a single writer, `code-reviewer`, which this step is not.

**Advisory — it never blocks.** Every failure path reports and steps over.

**Check results using deterministic path (not glob):**
```bash
# PADDED must survive a DOTTED phase number, of ANY segment count. This step is dispatched from
# exactly TWO places: `execute-phase.md` (`code_review_gate`) and `code-review-fix.md`
# (`record_disposition`). Only the second validates anything -- `code-review-fix.md`'s PADDED_PHASE validator anchors
# `^[0-9]+[A-Z]?(\.[0-9]+)*$`, an unbounded `*` widened by and a letter axis widened by, so it accepts `03.1`, `23.1.2` AND `12A`.
# `execute-phase.md` applies NO shape gate at all, so this fence is not mirroring an upstream
# guarantee; it IS the guarantee. (`code-review.md`'s own PADDED_PHASE validator is identical but never
# dispatches this step. It was cited here as a caller for several rounds and is not one.) And
# `printf "%02d"` cannot format one: bash prints `invalid number` and exits 1, which under
# `set -euo pipefail` aborts this step on its FIRST line -- the loudest possible failure from
# the gate that promises never to block, and it takes the whole phase's review reporting with
# it. Pad the integer part only and carry the sub-number verbatim, so 3.1 -> 03.1, 23.1.2 ->
# 23.1.2 and 3 -> 03. The segment count is deliberately NOT bounded here: the canonical
# grammar in `engineer_run query find-phase` (`PHASE_NUMBER_TOKEN_SOURCE`, ) is unbounded in segments,
# and widened the one dispatcher that validates to match it on that axis, so a guard
# narrower than that dispatcher means no ledger for a phase id the dispatcher already accepted.
# On failure NO path is built and the fence refuses by name: advisory means advisory, and it
# also means never probing a path assembled out of a value we just rejected.
# VALIDATE, THEN FORMAT -- never format and fall back on failure. `printf "%02d" abc` writes
# `00` to stdout BEFORE it fails, so a `$(printf ... || printf %s ...)` fallback CONCATENATES
# the two and yields `00abc`; `08` fails the same way as invalid octal, giving `0008.1` for a
# legitimate `08.1`. Both were driven. `${PHASE_NUMBER:-}` because an UNSET input must not trip
# `set -u` in a step that promises not to abort. Those printf failures are why this block VALIDATES
# instead of formatting; the pad itself performs NO arithmetic since round 14 (see the
# `case "${#_dig}"` line below), so it has no octal hazard to guard and needs no `10#`. `10#`
# survives in this step only where it still belongs -- on the severity COUNTS, which really are
# numbers being added.
# VALIDATE THE WHOLE VALUE, then format -- and on failure build NO path at all.
# Carrying an unusable value verbatim was the first draft and it was worse than the bug it
# replaced: PHASE_NUMBER is interpolated into a file path, so `../../etc/passwd` produced
# `${PHASE_DIR}/../../etc/passwd-REVIEW.md`, where the old `printf "%02d"` had at least
# mangled it to `00`. `code-review-fix.md`'s PADDED_PHASE validator already checks `^[0-9]+[A-Z]?(\.[0-9]+)*$` against its
# own PADDED_PHASE -- the padded form, not the raw PHASE_NUMBER this step is handed -- while
# `execute-phase.md` validates nothing at all; this step has two call sites and validates for
# itself rather than trusting either. Anything else yields an EMPTY PADDED and the blocks
# below refuse to build a path from it.
# PHASE_DIR is checked for NON-EMPTINESS ONLY. Both inputs come from the caller's init query, so
# neither is raw user input; only PHASE_NUMBER has a SHAPE (`^[0-9]+[A-Z]?(\.[0-9]+)*$`) to check
# against. A filesystem path admits `..` and symlinked parents alike, so a shape
# check here rejects working setups and proves nothing. Residual: PHASE_DIR may itself be a symlink
# and the ledger is written through it -- left alone, and not a security boundary.
_pd="${PHASE_DIR:-}"
_pn="${PHASE_NUMBER:-}"
_ok=1
[ -n "$_pd" ] || _ok=0
case "$_pn" in
  ''|*[!0-9.A-Z]*) _ok=0 ;;   # empty, or any character outside [0-9.A-Z] -- this is the traversal fence
  .*|*.)           _ok=0 ;;   # leading or trailing dot
  *..*)            _ok=0 ;;   # EMPTY SEGMENT. The three arms plus the letter-axis block below
                              # accept exactly digits[LETTER](.digits)* -- byte-congruent with the
                              # callers' ^[0-9]+[A-Z]?(\.[0-9]+)*$ -- rather than merely wider than
                              # the retired `*.*.*` arity bound, which masked `1..2` by accident.
esac
# THE LETTER AXIS. The canonical grammar (`engineer_run query find-phase`) is digits, an OPTIONAL single uppercase
# letter, then dotted digit segments -- `12A`, `3A`, `23A.1.2`. widened the six
# shell/markdown mirrors to it after this branch was cut, and its lint ratchet then flagged this
# step as the one letterless mirror left. The character class above admits the letter; these
# arms pin WHERE it may sit -- only as the last character of the integer part, at most once --
# so `23a`, `A23`, `2A3`, `23AB` and `23.1A` are all refused.
if [ "$_ok" = "1" ]; then
  _int="${_pn%%.*}"
  case "$_pn" in *.*) _sub=".${_pn#*.}" ;; *) _sub="" ;; esac
  _let="${_int##*[0-9]}"                              # what trails the last digit: '' or the letter
  _dig="${_int%"$_let"}"
  case "$_dig" in ''|*[!0-9]*) _ok=0 ;; esac          # the integer part must be digits first
  case "$_let" in ''|[A-Z]) ;; *) _ok=0 ;; esac        # at most ONE letter, uppercase
  case "$_sub" in *[!0-9.]*) _ok=0 ;; esac            # no letter in any later segment
fi
# LENGTH-BOUND EACH COMPONENT SEPARATELY -- and the REASON changed at round 14, so read this rather
# than inherit it. It used to be integer overflow: the pad ran `$((10#$_int))`, bash integers wrap at
# 2^64, and a 54-digit value yielded -7908320945662590977 SILENTLY as the padded phase. The pad is a
# string pad now and converts nothing, so that overflow is unreachable and its rationale is dead.
# WHAT THE BOUND STILL DOES, stated narrowly because the obvious wider claim is FALSE: it bounds each
# SEGMENT, and NOTHING here bounds the COMPOSITE. Every segment is joined into ONE filename
# component and depth is unbounded, so a per-segment bound does not enforce a filename limit --
# driven at round 14: thirty 8-digit segments yield a 278-character PADDED and a 294-character name
# against a NAME_MAX of 255. That is a real residual of this validator, it predates the pad change,
# and it is named here rather than papered over with a filesystem rationale the bound does not
# deliver. The bound belongs on the INTEGER PART: applied to the whole value it rejected
# `12345678.1`, whose integer part is a legal 8 digits, while accepting `1.123456` -- an accidental
# bound on the composite that was both too strict and too loose. Every later segment is bounded too,
# on the same narrow reading.
# THE LOOP IS THE POINT, and it is what makes the heading above TRUE. The earlier form bounded
# `${_pn#*.}` -- the WHOLE tail after the first dot -- which is one component only while the id
# has at most two. Once N-segment ids are accepted (see the shape arms), that form rejects
# `1.1234567.1`, whose every component is a legal 7-or-fewer digits, purely because the tail
# measures 9 characters. That is the composite bound this comment already called "too strict",
# surviving one level up. Walk the segments instead, so the rule is per-component in fact and
# not only in the heading. The loop terminates on any string the shape arms admit: each pass
# strips a leading `<seg>.`, and the no-dot pass clears $_rest.
if [ "$_ok" = "1" ]; then
  _rest="$_pn"
  while [ -n "$_rest" ]; do
    case "$_rest" in
      *.*) _seg="${_rest%%.*}"; _rest="${_rest#*.}" ;;
      *)   _seg="$_rest";       _rest="" ;;
    esac
    # The bound is on the DIGITS: a letter suffix is one character the digit bound has no
    # stake in, so `12345678A` is within it exactly as `12345678` is.
    case "${_seg%[A-Z]}" in ?????????*) _ok=0 ;; esac
  done
fi
if [ "$_ok" = "1" ]; then
  # padStart(2,'0'), EXACTLY, and as a STRING -- the canonical normalizer left-pads the digit run to a
  # MINIMUM of two and otherwise preserves it, so arithmetic is the wrong tool. `printf "%02d"
  # "$((10#$_dig))"` agreed on `8`/`08`/`09` and silently DISAGREED on every longer leading-zero run:
  # `008` -> `08`, `0008A` -> `08A`, resolving a REVIEW.md path init never writes. Driven at round 14
  # by the property that asserts agreement with `normalizePhaseName` over generated ids; the 13-shape
  # matrix that preceded it sampled no run longer than two and could not see it. Dropping the
  # arithmetic also RETIRES the octal hazard `10#` existed to work around, rather than guarding it.
  # The letter and any dot segments ride along verbatim, as the canonical padder does: `3A` -> `03A`.
  case "${#_dig}" in 1) PADDED="0${_dig}${_let}${_sub}" ;; *) PADDED="${_dig}${_let}${_sub}" ;; esac
else
  PADDED=""
fi
# REFUSE BEFORE BUILDING ANY PATH. An unusable input yields an empty PADDED above, and the
# earlier placement -- after the assignments -- meant a rejected value still had
# `${_pd}/-REVIEW.md` assembled and stat'ed before the refusal fired. Nothing is constructed
# from a value we have already rejected.
if [ -z "$PADDED" ]; then
  echo "Code review reporting skipped (unusable phase number or directory: '${PHASE_NUMBER:-}')"
  return 0 2>/dev/null || exit 0
fi
REVIEW_FILE="${_pd}/${PADDED}-REVIEW.md"
DISPOSITION_FILE="${_pd}/${PADDED}-REVIEW-DISPOSITION.md"
# Extract ONLY the leading frontmatter block: `sed -n '/^---$/,/^---$/p'` re-opens its range
# on a body `---` and runs to EOF, which leaks body lines into the scan. That leak is benign
# for a key the frontmatter always carries (the first match still wins) but NOT for an
# optional one — a review with no `findings:` block and a body `total:` line would otherwise
# report the body's number as the count. Stop at the closing delimiter instead, and strip CR
# first so a CRLF-authored review neither breaks the delimiter match nor injects a carriage
# return into the message below (DEFECT.FRONTMATTER-SCALAR-BROAD-GREP).
# Buffered, and emitted only if the CLOSING delimiter was actually seen: an unterminated
# frontmatter block would otherwise run to EOF and hand the whole review body to the reads below,
# defeating the scoping entirely.
# Guarded and `|| true`: this step is advisory, so a REVIEW.md that is missing, a directory, or
# otherwise unreadable must leave the counts empty and let execution continue — never abort the
# step under `set -e`/`pipefail`.
# REVIEW_READ records that the file was actually OPENED, separately from what it yielded. An
# absent or unreadable review and a present-but-unparseable one both leave every value below
# empty, and the reporting arm used to treat the two identically -- silence -- so a REVIEW.md
# with three criticals and an unterminated frontmatter read exactly like a clean review. A
# malformed report must not read as a clean one; the arm below tells them apart on this flag.
REVIEW_FM=""
REVIEW_READ=0
if [ -f "$REVIEW_FILE" ] && [ -r "$REVIEW_FILE" ]; then
  REVIEW_READ=1
  REVIEW_FM=$(tr -d '\r' < "$REVIEW_FILE" 2>/dev/null | LC_ALL=C awk 'NR==1{if($0!="---") exit; next} /^---$/{closed=1; exit} {buf = buf $0 "\n"} END{if (closed) printf "%s", buf}' || true)
fi
# `|| true` on every read: under `pipefail` a non-matching `grep` exits 1, and an assignment
# whose command substitution fails aborts the step under `set -e`. An advisory gate must survive
# a REVIEW.md with no frontmatter at all.
# STATUS TAKES THE SAME PARSER AS THE COUNTS, and it is the read where truncation costs most. Under
# `cut -d: -f2` the valid YAML scalar `status: clean:junk` arrived as the bare `clean` -- so an
# unusable status SILENTLY took the clean arm, suppressing both the report and the ledger. `-f2-`
# keeps the whole scalar, `clean:junk` matches no arm, and the step reports. Found by the round's
# fourth adversarial pass as a sibling of the count-parser class, in the same file.
REVIEW_STATUS=$(echo "$REVIEW_FM" | LC_ALL=C grep -m1 "^status:" | cut -d: -f2- | LC_ALL=C sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' || true)
# The counts belong to the `findings:` MAPPING, not merely to the frontmatter, and the scoping now
# goes all the way there. `^[[:space:]]*total:` matches any indented key anywhere in the block, so
# a top-level key later named `total:`, `info:` or `critical:` was picked up ahead of the nested
# one — the extensive comment above is about scoping the frontmatter, and the scoping stopped one
# level short of the mapping the values actually live in. `status:` was never exposed: it is
# anchored to column 0 because it IS top-level.
# The awk selects the `findings:` block and stops at the next column-0 key, so the reads below can
# only see keys nested under it. Block 2 derives REVIEW_TOTAL through the same filter.
# `blocker:` is the documented tier-equivalent of `critical:` (code-reviewer.md § "Label
# equivalence") — accept either, exactly as code-review.md's present_results already does.
REVIEW_FINDINGS_FM=$(echo "$REVIEW_FM" | LC_ALL=C awk '/^findings:[[:space:]]*$/{f=1; next} f&&/^[^[:space:]]/{exit} f' || true)
REVIEW_CRITICAL=$(echo "$REVIEW_FINDINGS_FM" | LC_ALL=C grep -E -m1 "^[[:space:]]*(critical|blocker):" | cut -d: -f2- | LC_ALL=C sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' || true)
REVIEW_WARNING=$(echo "$REVIEW_FINDINGS_FM" | LC_ALL=C grep -E -m1 "^[[:space:]]*warning:" | cut -d: -f2- | LC_ALL=C sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' || true)
REVIEW_INFO=$(echo "$REVIEW_FINDINGS_FM" | LC_ALL=C grep -E -m1 "^[[:space:]]*info:" | cut -d: -f2- | LC_ALL=C sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' || true)
REVIEW_TOTAL=$(echo "$REVIEW_FINDINGS_FM" | LC_ALL=C grep -E -m1 "^[[:space:]]*total:" | cut -d: -f2- | LC_ALL=C sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' || true)
# ONE PARSER FOR THE WHOLE STEP. These reads used `cut -d: -f2 | tr -d ' '`, which repairs a
# malformed scalar into a number twice over: `tr -d` deletes INTERNAL spaces (`1 0` -> `10`) and
# `-f2` keeps only the SECOND FIELD (`1: junk` -> `1`). Block 2 was tightened first, which left the
# two fences disagreeing about the same bytes -- driven: `critical: 1 0` made this block print
# `10 findings -- 10 critical` while the ledger recorded three rows and no shortfall. A console line
# and a ledger contradicting each other is the exact confusion this PR exists to remove, so the fix
# is one parser rather than a disclosed divergence. `-f2-` keeps the whole scalar; only the ends are
# trimmed. A repaired number is not a number.
# LC_ALL=C ON EVERY `grep`/`sed` IN THESE READS, and it is load-bearing rather than cosmetic: the
# POSIX classes are LOCALE-DEFINED, and glibc's C.UTF-8 puts U+2003 (and U+1680, U+2000-U+200A,
# U+205F, U+3000) in BOTH [[:space:]] and [[:blank:]], where C and en_US.UTF-8 put them in neither.
# Unpinned, `status: clean<U+2003>` trimmed to `clean` under one locale and stayed unusable under
# another -- the same silent suppression as the `clean:junk` truncation, reachable only on some
# machines. Pinned to C the class is exactly {space, tab, NL, VT, FF, CR}, which is what the mirror
# in tests/code-review-pipeline-regression.test.cjs spells out literally, so the two agree by
# construction rather than by coincidence of locale.
# The breakdown is reportable only when ALL FOUR counts are numbers. Deciding on REVIEW_TOTAL
# alone would still emit `6 findings —  critical` for a review carrying a total and nothing else.
REVIEW_COUNTS_OK=1
for _c in "$REVIEW_TOTAL" "$REVIEW_CRITICAL" "$REVIEW_WARNING" "$REVIEW_INFO"; do
  # Length-bounded as well as digit-only: bash integers wrap at 2^64, so a 20-digit count
  # arrives at the sum below as 0 and an inconsistent breakdown passes. No real review
  # reports nine digits of findings.
  case "$_c" in ''|*[!0-9]*) REVIEW_COUNTS_OK=0 ;; ?????????*) REVIEW_COUNTS_OK=0 ;; esac
done
# Numeric is necessary and not sufficient. `total: 0` beside `critical: 1` is four valid numbers
# that render the self-contradicting line `0 findings — 1 critical, 0 warning, 0 info`. An
# inconsistent breakdown is unavailable for the same reason a partial one is: half-true is worse
# than withheld, and the countless form is already the documented fallback.
# `10#` on every operand: bash infers the base from a leading zero, so a review reporting
# `critical: 08` makes $(( )) fail with "value too great for base". The CONSEQUENCE stated here
# used to be "takes the whole advisory step down under `set -e`", and that is WRONG: the
# arithmetic sits inside an `if` condition, a TESTED context, where `set -e` is inert. What
# actually happens is that the consistency check is SKIPPED -- which the regression suite
# already records. Skipping it is still the wrong outcome for a check whose whole job is
# refusing a half-true breakdown, so `10#` stays; only the account of what it prevents is
# corrected. The values are already digit-only by the loop above.
if [ "$REVIEW_COUNTS_OK" = "1" ] \
   && [ "$((10#$REVIEW_CRITICAL + 10#$REVIEW_WARNING + 10#$REVIEW_INFO))" -ne "$((10#$REVIEW_TOTAL))" ]; then
  REVIEW_COUNTS_OK=0
fi
# EMIT — inside the fence, on every reporting arm. Until this block existed, the fence computed six
# values and printed none of them, and the prose below then asked the agent to display four of them.
# The shell exits at the closing fence and the agent sees only stdout, so those values were
# unobtainable: the message could not be rendered, and the whole block was decorative. That is the
# rule block 2 states about itself — a prose-only gate on a value no later block can see is not a
# gate — applied to the block that is this step's primary deliverable rather than only to its
# sibling. The status arm is re-derived here, not left to the reader, for the same reason.
case "$REVIEW_STATUS" in
  '')
    # NO STATUS is not NO REVIEW. When the file was read and yielded no status -- unterminated
    # frontmatter, no frontmatter, no `status:` key, a zero-byte file -- the review is
    # UNPARSEABLE, and saying nothing would make it indistinguishable from a clean one. State it,
    # without the breakdown (there is none to trust) and without the --fix suggestion (nothing
    # here proves there are findings to fix). An absent or unreadable review stays silent: there
    # is nothing to describe, and guessing is the failure the guard above exists to prevent.
    if [ "$REVIEW_READ" = "1" ]; then
      echo "Code review status unparsed: REVIEW.md is present but its frontmatter has no parseable status; severity counts unavailable."
    fi
    ;;
  clean|skipped) ;;   # nothing to report; block 2 still reconciles an existing ledger
  *)
    if [ "$REVIEW_COUNTS_OK" = "1" ]; then
      echo "Code review: ${REVIEW_TOTAL} findings — ${REVIEW_CRITICAL} critical, ${REVIEW_WARNING} warning, ${REVIEW_INFO} info."
    else
      # A REVIEW.md written without a `findings:` block has no counts to report, and any count that
      # is empty, non-numeric, over-long or inconsistent makes the whole breakdown unavailable
      # rather than half-filled. Half-true is worse than withheld.
      echo "Code review found issues."
    fi
    echo "Consider running: /code-review ${PHASE_NUMBER:-} --fix"
    ;;
esac
```

**Display that block's stdout verbatim.** It prints the severity breakdown when all four counts are
numeric and mutually consistent, and the countless form otherwise; on a clean, skipped or absent
review it prints nothing and there is nothing to display. Do not re-derive any of it — a number the
shell computed and did not print is gone once the fence closes, which is precisely the defect this
arm exists to close.

**Record a per-finding disposition.** The counts say how many findings there were, not what
happened to any of them. On the same condition as the message above — REVIEW_STATUS not "clean",
not "skipped" and not empty — write `${DISPOSITION_FILE}`: one row per finding ID, defaulting to
`open`, reconciling `fixed`/`skipped` from REVIEW-FIX.md and preserving any disposition already
recorded, its stated reason included. It is a sibling artifact because `--auto` rewrites
REVIEW.md every iteration and `code-reviewer` is its single writer. Advisory like the rest of
the step — never blocks:

## Design notes for the disposition adapter

The runtime implementation is `engineer/bin/lib/review_ledger.py`, invoked through
`engineer_run query review.reconcile`. The notes below preserve the rationale for the
ledger guarantees: parsing only structural findings, validating existing destinations,
preserving history, avoiding timestamp-only rewrites, and detecting input drift. They
originated with an embedded JavaScript prototype; the installed Python adapter now owns
those behaviors.

**Before `(function main() {`**

EVERYTHING BELOW RUNS INSIDE main() AND LEAVES BY return, NEVER an explicit exit call. The script
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
the row falls through to inference rather than carrying garbage (the same rule the
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
contains neither. That is 's complaint verbatim -- 'no trace of what happened to them' --
reproduced by the artifact built to prevent it, and 'nothing was decided about it' is exactly
the state says must leave a trace.
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
The!unparsed conjunct here is the SECOND of the two exits that discarded the shortfall, and
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

The Python adapter holds the runtime planning lock across its read/validate/write transaction
(`engineer/bin/lib/review_ledger.py` and `engineer/bin/lib/core.py`). This serializes the gate,
fix workflow, and any concurrent runtime writer so their ledger updates cannot overwrite one another.

```bash
# Each fenced block runs in a FRESH shell, so block 1's PADDED/REVIEW_FILE/DISPOSITION_FILE are NOT
# live here — re-derive them from the two inputs this step consumes (`PHASE_DIR`, `PHASE_NUMBER`).
# Inheriting them is not merely stale, it is EMPTY, and the failure is silent rather than loud:
# the runtime adapter rejects an empty review path, the trailing `|| echo` swallows it
# as a non-blocking skip, and no ledger is written at all. The shim preamble below is re-emitted
# for the same reason, and these three belong beside it.
# PADDED must survive a DOTTED phase number, of ANY segment count. This step is dispatched from
# exactly TWO places: `execute-phase.md` (`code_review_gate`) and `code-review-fix.md`
# (`record_disposition`). Only the second validates anything -- `code-review-fix.md`'s PADDED_PHASE validator anchors
# `^[0-9]+[A-Z]?(\.[0-9]+)*$`, an unbounded `*` widened by and a letter axis widened by, so it accepts `03.1`, `23.1.2` AND `12A`.
# `execute-phase.md` applies NO shape gate at all, so this fence is not mirroring an upstream
# guarantee; it IS the guarantee. (`code-review.md`'s own PADDED_PHASE validator is identical but never
# dispatches this step. It was cited here as a caller for several rounds and is not one.) And
# `printf "%02d"` cannot format one: bash prints `invalid number` and exits 1, which under
# `set -euo pipefail` aborts this step on its FIRST line -- the loudest possible failure from
# the gate that promises never to block, and it takes the whole phase's review reporting with
# it. Pad the integer part only and carry the sub-number verbatim, so 3.1 -> 03.1, 23.1.2 ->
# 23.1.2 and 3 -> 03. The segment count is deliberately NOT bounded here: the canonical
# grammar in `engineer_run query find-phase` (`PHASE_NUMBER_TOKEN_SOURCE`, ) is unbounded in segments,
# and widened the one dispatcher that validates to match it on that axis, so a guard
# narrower than that dispatcher means no ledger for a phase id the dispatcher already accepted.
# On failure NO path is built and the fence refuses by name: advisory means advisory, and it
# also means never probing a path assembled out of a value we just rejected.
# VALIDATE, THEN FORMAT -- never format and fall back on failure. `printf "%02d" abc` writes
# `00` to stdout BEFORE it fails, so a `$(printf ... || printf %s ...)` fallback CONCATENATES
# the two and yields `00abc`; `08` fails the same way as invalid octal, giving `0008.1` for a
# legitimate `08.1`. Both were driven. `${PHASE_NUMBER:-}` because an UNSET input must not trip
# `set -u` in a step that promises not to abort. Those printf failures are why this block VALIDATES
# instead of formatting; the pad itself performs NO arithmetic since round 14 (see the
# `case "${#_dig}"` line below), so it has no octal hazard to guard and needs no `10#`. `10#`
# survives in this step only where it still belongs -- on the severity COUNTS, which really are
# numbers being added.
# VALIDATE THE WHOLE VALUE, then format -- and on failure build NO path at all.
# Carrying an unusable value verbatim was the first draft and it was worse than the bug it
# replaced: PHASE_NUMBER is interpolated into a file path, so `../../etc/passwd` produced
# `${PHASE_DIR}/../../etc/passwd-REVIEW.md`, where the old `printf "%02d"` had at least
# mangled it to `00`. `code-review-fix.md`'s PADDED_PHASE validator already checks `^[0-9]+[A-Z]?(\.[0-9]+)*$` against its
# own PADDED_PHASE -- the padded form, not the raw PHASE_NUMBER this step is handed -- while
# `execute-phase.md` validates nothing at all; this step has two call sites and validates for
# itself rather than trusting either. Anything else yields an EMPTY PADDED and the blocks
# below refuse to build a path from it.
# PHASE_DIR is checked for NON-EMPTINESS ONLY. Both inputs come from the caller's init query, so
# neither is raw user input; only PHASE_NUMBER has a SHAPE (`^[0-9]+[A-Z]?(\.[0-9]+)*$`) to check
# against. A filesystem path admits `..` and symlinked parents alike, so a shape
# check here rejects working setups and proves nothing. Residual: PHASE_DIR may itself be a symlink
# and the ledger is written through it -- left alone, and not a security boundary.
_pd="${PHASE_DIR:-}"
_pn="${PHASE_NUMBER:-}"
_ok=1
[ -n "$_pd" ] || _ok=0
case "$_pn" in
  ''|*[!0-9.A-Z]*) _ok=0 ;;   # empty, or any character outside [0-9.A-Z] -- this is the traversal fence
  .*|*.)           _ok=0 ;;   # leading or trailing dot
  *..*)            _ok=0 ;;   # EMPTY SEGMENT. The three arms plus the letter-axis block below
                              # accept exactly digits[LETTER](.digits)* -- byte-congruent with the
                              # callers' ^[0-9]+[A-Z]?(\.[0-9]+)*$ -- rather than merely wider than
                              # the retired `*.*.*` arity bound, which masked `1..2` by accident.
esac
# THE LETTER AXIS. The canonical grammar (`engineer_run query find-phase`) is digits, an OPTIONAL single uppercase
# letter, then dotted digit segments -- `12A`, `3A`, `23A.1.2`. widened the six
# shell/markdown mirrors to it after this branch was cut, and its lint ratchet then flagged this
# step as the one letterless mirror left. The character class above admits the letter; these
# arms pin WHERE it may sit -- only as the last character of the integer part, at most once --
# so `23a`, `A23`, `2A3`, `23AB` and `23.1A` are all refused.
if [ "$_ok" = "1" ]; then
  _int="${_pn%%.*}"
  case "$_pn" in *.*) _sub=".${_pn#*.}" ;; *) _sub="" ;; esac
  _let="${_int##*[0-9]}"                              # what trails the last digit: '' or the letter
  _dig="${_int%"$_let"}"
  case "$_dig" in ''|*[!0-9]*) _ok=0 ;; esac          # the integer part must be digits first
  case "$_let" in ''|[A-Z]) ;; *) _ok=0 ;; esac        # at most ONE letter, uppercase
  case "$_sub" in *[!0-9.]*) _ok=0 ;; esac            # no letter in any later segment
fi
# LENGTH-BOUND EACH COMPONENT SEPARATELY -- and the REASON changed at round 14, so read this rather
# than inherit it. It used to be integer overflow: the pad ran `$((10#$_int))`, bash integers wrap at
# 2^64, and a 54-digit value yielded -7908320945662590977 SILENTLY as the padded phase. The pad is a
# string pad now and converts nothing, so that overflow is unreachable and its rationale is dead.
# WHAT THE BOUND STILL DOES, stated narrowly because the obvious wider claim is FALSE: it bounds each
# SEGMENT, and NOTHING here bounds the COMPOSITE. Every segment is joined into ONE filename
# component and depth is unbounded, so a per-segment bound does not enforce a filename limit --
# driven at round 14: thirty 8-digit segments yield a 278-character PADDED and a 294-character name
# against a NAME_MAX of 255. That is a real residual of this validator, it predates the pad change,
# and it is named here rather than papered over with a filesystem rationale the bound does not
# deliver. The bound belongs on the INTEGER PART: applied to the whole value it rejected
# `12345678.1`, whose integer part is a legal 8 digits, while accepting `1.123456` -- an accidental
# bound on the composite that was both too strict and too loose. Every later segment is bounded too,
# on the same narrow reading.
# THE LOOP IS THE POINT, and it is what makes the heading above TRUE. The earlier form bounded
# `${_pn#*.}` -- the WHOLE tail after the first dot -- which is one component only while the id
# has at most two. Once N-segment ids are accepted (see the shape arms), that form rejects
# `1.1234567.1`, whose every component is a legal 7-or-fewer digits, purely because the tail
# measures 9 characters. That is the composite bound this comment already called "too strict",
# surviving one level up. Walk the segments instead, so the rule is per-component in fact and
# not only in the heading. The loop terminates on any string the shape arms admit: each pass
# strips a leading `<seg>.`, and the no-dot pass clears $_rest.
if [ "$_ok" = "1" ]; then
  _rest="$_pn"
  while [ -n "$_rest" ]; do
    case "$_rest" in
      *.*) _seg="${_rest%%.*}"; _rest="${_rest#*.}" ;;
      *)   _seg="$_rest";       _rest="" ;;
    esac
    # The bound is on the DIGITS: a letter suffix is one character the digit bound has no
    # stake in, so `12345678A` is within it exactly as `12345678` is.
    case "${_seg%[A-Z]}" in ?????????*) _ok=0 ;; esac
  done
fi
if [ "$_ok" = "1" ]; then
  # padStart(2,'0'), EXACTLY, and as a STRING -- the canonical normalizer left-pads the digit run to a
  # MINIMUM of two and otherwise preserves it, so arithmetic is the wrong tool. `printf "%02d"
  # "$((10#$_dig))"` agreed on `8`/`08`/`09` and silently DISAGREED on every longer leading-zero run:
  # `008` -> `08`, `0008A` -> `08A`, resolving a REVIEW.md path init never writes. Driven at round 14
  # by the property that asserts agreement with `normalizePhaseName` over generated ids; the 13-shape
  # matrix that preceded it sampled no run longer than two and could not see it. Dropping the
  # arithmetic also RETIRES the octal hazard `10#` existed to work around, rather than guarding it.
  # The letter and any dot segments ride along verbatim, as the canonical padder does: `3A` -> `03A`.
  case "${#_dig}" in 1) PADDED="0${_dig}${_let}${_sub}" ;; *) PADDED="${_dig}${_let}${_sub}" ;; esac
else
  PADDED=""
fi
# REFUSE BEFORE BUILDING ANY PATH. An unusable input yields an empty PADDED above, and the
# earlier placement -- after the assignments -- meant a rejected value still had
# `${_pd}/-REVIEW.md` assembled and stat'ed before the refusal fired. Nothing is constructed
# from a value we have already rejected.
if [ -z "$PADDED" ]; then
  echo "Code review disposition skipped (unusable phase number or directory: '${PHASE_NUMBER:-}')"
  return 0 2>/dev/null || exit 0
fi
REVIEW_FILE="${_pd}/${PADDED}-REVIEW.md"
DISPOSITION_FILE="${_pd}/${PADDED}-REVIEW-DISPOSITION.md"
# The condition stated above this block is re-derived HERE rather than left to the reader. Block 1
# computes REVIEW_STATUS and emits nothing, and its shell is gone, so nothing downstream can act on
# it: a prose-only gate on a value no later block can see is not a gate. Without this, a clean
# re-review rewrites an existing ledger it was never meant to touch.
REVIEW_STATUS=""
REVIEW_TOTAL=""
REVIEW_READ=0   # block 1's distinction, re-derived here: read-but-unparseable is not absent
if [ -f "$REVIEW_FILE" ] && [ -r "$REVIEW_FILE" ]; then
  REVIEW_READ=1
  _FM=$(tr -d '\r' < "$REVIEW_FILE" 2>/dev/null | LC_ALL=C awk 'NR==1{if($0!="---") exit; next} /^---$/{closed=1; exit} {buf = buf $0 "\n"} END{if (closed) printf "%s", buf}' || true)
  REVIEW_STATUS=$(echo "$_FM" | LC_ALL=C grep -m1 "^status:" | cut -d: -f2- | LC_ALL=C sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' || true)
  # The frontmatter total is carried into the script so the two parsers in this step can be
  # RECONCILED. The counts come from the frontmatter; the rows come from `### <ID>:` heading
  # matches against a closed CR|BL|WR|IN alternation. They are two independent numbers produced
  # one paragraph apart, and nothing compared them: a finding the heading parser cannot match
  # contributed no row, no note and no diagnostic, and the ledger then asserted `open: 3 of 3`
  # over a set strictly smaller than the console line had just reported. Anchored inside the
  # `findings:` mapping — see the anchoring note in block 1 — and digit-only, because a
  # non-numeric total is not a number to reconcile against.
  _FINDINGS_FM=$(echo "$_FM" | LC_ALL=C awk '/^findings:[[:space:]]*$/{f=1; next} f&&/^[^[:space:]]/{exit} f' || true)
  # ONE PARSER FOR EVERY COUNT THIS BLOCK READS, and both halves of it are load-bearing.
  # `-f2-` keeps everything AFTER the first colon: `-f2` alone takes only the SECOND FIELD, so the
  # malformed `critical: 1: junk` arrives as the perfectly numeric `1`. And the ends are trimmed
  # rather than `tr -d ' '`-ed, which would delete INTERNAL spaces and turn `1 0` into `10`.
  # Both quirks are long-standing in the sibling reads and both were INERT here until this block
  # began reconciling; each one repairs a malformed scalar into a number that then decides whether a
  # shortfall is reported. An adversarial pass drove both: `critical: 1: junk` wrongly suppressed a
  # real `unparsed: 2`, and a LENIENT total beside a STRICT severity was worse still -- `critical: 5 0`
  # with `total: 1 0` repaired only the total, rejected the severity, skipped the contradiction check
  # and INVENTED `unparsed: 7`. A field is either trustworthy or it is not; parsing one leniently and
  # its sibling strictly is the shape that fabricates.
  REVIEW_TOTAL=$(echo "$_FINDINGS_FM" | LC_ALL=C grep -E -m1 "^[[:space:]]*total:" | cut -d: -f2- | LC_ALL=C sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' || true)
  case "$REVIEW_TOTAL" in ''|*[!0-9]*) REVIEW_TOTAL="" ;; ?????????*) REVIEW_TOTAL="" ;; esac
  # ONE FIELD, ONE TRUST MODEL, ACROSS BOTH FENCES. Block 1 withholds the whole breakdown unless the
  # four counts are numeric AND `critical + warning + info == total`; this fence used to bound `total`
  # for digits and length only and then hand it to the `unparsed:` reconciliation, so a REVIEW.md whose
  # `findings:` block is internally inconsistent (`total: 10` beside `critical: 1, warning: 1, info: 1`)
  # made block 1 print the countless form -- breakdown suppressed as untrustworthy -- while this block
  # still computed an `unparsed:` shortfall from that same untrusted number. It fails in the SAFE
  # direction (over-reports a possible gap rather than hiding one), which is why it is not a blocker;
  # it is still two trust models for one field, one fence apart, and the weaker one is downstream.
  # `blocker:` is the documented tier-equivalent of `critical:` (code-reviewer.md 'Label
  # equivalence') -- the same alternation block 1 reads, because a mirror that drops it would diverge
  # on exactly the reviews that use it.
  # TRIM THE ENDS, NEVER `tr -d ' '`, AND THE DIFFERENCE DECIDES A SUPPRESSION. `tr -d` deletes
  # INTERNAL spaces too, so a malformed `critical: 1 0` would arrive as the perfectly numeric `10`.
  # Every read in this step now takes the end-trim instead -- the sibling reads were moved off `tr -d`
  # in the same round, so this is no longer a divergence between blocks -- and the reason it matters
  # HERE is that a value which LOOKS numeric can satisfy the sum test and SUPPRESS a real
  # `unparsed:` shortfall. Suppression is the new
  # behaviour, so the admission test for it is strict -- an internal space survives the trim, fails the
  # digit `case` below, and the shortfall is reported. Fail-safe in the only direction that matters:
  # when the frontmatter is malformed we decline to suppress, rather than trusting a repaired number.
  _c_crit=$(echo "$_FINDINGS_FM" | LC_ALL=C grep -E -m1 "^[[:space:]]*(critical|blocker):" | cut -d: -f2- | LC_ALL=C sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' || true)
  _c_warn=$(echo "$_FINDINGS_FM" | LC_ALL=C grep -E -m1 "^[[:space:]]*warning:" | cut -d: -f2- | LC_ALL=C sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' || true)
  _c_info=$(echo "$_FINDINGS_FM" | LC_ALL=C grep -E -m1 "^[[:space:]]*info:" | cut -d: -f2- | LC_ALL=C sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' || true)
  # THE CHECK IS NARROWER THAN BLOCK 1'S, DELIBERATELY, AND THE DIFFERENCE IS NOT AN OVERSIGHT.
  # Block 1 withholds on `REVIEW_COUNTS_OK`, which demands ALL FOUR counts be numeric -- because it
  # DISPLAYS all four, and `6 findings --  critical` is the half-filled line that rule exists to
  # prevent. This fence displays none of them: it uses `total` alone, to reconcile against the number
  # of headings the row parser matched. So the all-four rule does not port. Applied verbatim here it
  # would blank `total` on a REVIEW.md carrying `total: 5` and no severity keys -- a review whose total
  # is perfectly usable -- and SILENTLY DROP an `unparsed:` shortfall this step reports correctly today.
  # That trades a safe-direction over-report for a silent under-report, which is the wrong way round
  # and is the exact failure class the `unparsed:` key was added to close.
  # What DOES port is the CONTRADICTION: when the three severities are all present and numeric and do
  # not sum to `total`, the frontmatter disagrees with itself and `total` is not a number to reconcile
  # against. Block 1 already suppresses its breakdown on that input; this fence now declines to compute
  # a shortfall from it. Absent counts are not a contradiction -- there is nothing to disagree.
  # AN ABSENT SEVERITY STILL BOUNDS THE SUM FROM BELOW, and that is enough to prove a contradiction
  # in one direction. Counts are non-negative, so a missing one can only ADD: if the severities that
  # ARE present and numeric already sum to MORE than `total`, the block disagrees with itself whatever
  # the missing value is. Requiring all three before comparing missed that -- driven by an adversarial
  # pass: `critical: 4`, `warning: 4`, no `info:`, `total: 5` reconciled against a total the present
  # counts had already refuted. So the comparison is two-armed: EQUALITY when all three are known,
  # and a LOWER BOUND when they are not. `_p_sum` accumulates only the present-and-numeric ones.
  _sum_ok=1; _p_sum=0
  for _c in "$_c_crit" "$_c_warn" "$_c_info"; do
    # Present AND numeric AND within the same length bound the total carries -- `10#` below needs
    # digits, and bash integers wrap at 2^64.
    case "$_c" in
      ''|*[!0-9]*) _sum_ok=0 ;;
      ?????????*)  _sum_ok=0 ;;
      *)           _p_sum=$(( _p_sum + 10#$_c )) ;;
    esac
  done
  # `10#` on every operand, for block 1's reason: bash infers the base from a leading zero, so
  # `critical: 08` makes $(( )) fail with "value too great for base" and, under `set -e`, takes the
  # whole advisory step down -- strictly worse than the stale count this check exists to prevent.
  if [ -n "$REVIEW_TOTAL" ]; then
    _t=$(( 10#$REVIEW_TOTAL ))
    if [ "$_sum_ok" = "1" ]; then
      # All three known: the sum must match exactly.
      if [ "$_p_sum" -ne "$_t" ]; then REVIEW_TOTAL=""; fi
    elif [ "$_p_sum" -gt "$_t" ]; then
      # Not all known: only an OVERSHOOT is provable. An undershoot is the absent count's job.
      REVIEW_TOTAL=""
    fi
  fi
fi
# Skip a clean/skipped/absent review ONLY when there is nothing to reconcile AT ALL. An EXISTING
# ledger is still brought up to date -- freezing it would leave findings showing open that the
# review no longer reports, and an unconditional skip would make the reconciliation path
# unreachable on exactly the run that needs it.
# A FIX REPORT IS THE SECOND REASON TO PROCEED: a direct `/code-review N --auto` writes no gate
# ledger and a converged loop leaves `status: clean`, so a fully fixed phase recorded nothing.
_fix_any=0
[ -f "${_pd}/${PADDED}-REVIEW-FIX.md" ] && _fix_any=1
# Backups count too -- a converged loop's earlier iterations live only there. An unmatched glob
# expands to the literal pattern, which `-f` rejects.
# $(printf '%s' "$PADDED") per lint-workflow-shellcheck's remedy: a bare $VAR in a `for x in`
# splits differently under bash and zsh.
for _f in "${_pd}/$(printf '%s' "$PADDED")-REVIEW-FIX.iter"*.md; do [ -f "$_f" ] && _fix_any=1; done
# The word for an empty status names WHICH empty it is, for the same reason block 1 does: a
# review that was read and could not be parsed is 'unparsed', an absent one is 'none'.
_st="${REVIEW_STATUS:-none}"; [ -z "$REVIEW_STATUS" ] && [ "$REVIEW_READ" = "1" ] && _st="unparsed"
case "$REVIEW_STATUS" in
  ''|clean|skipped)
    if [ ! -f "$DISPOSITION_FILE" ] && [ "$_fix_any" = "0" ]; then
      echo "Code review disposition skipped (status: ${_st})"
      return 0 2>/dev/null || exit 0
    fi
    echo "Code review status ${_st}; reconciling the fix report and any existing disposition ledger."
    ;;
esac
_engineer_identity_ok() {
  [ -f "$1" ] || return 1
  [ "$(sh "$1" query runtime-identity --pick packageName --raw 2>/dev/null)" = "engineer-runtime" ]
}
_engineer_select() {
  for _engineer_candidate do
    if _engineer_identity_ok "$_engineer_candidate"; then
      ENGINEER_RUN="$_engineer_candidate"
      return 0
    fi
  done
  return 1
}
if [ -n "${ENGINEER_RUN:-}" ]; then
  _engineer_identity_ok "$ENGINEER_RUN" || {
    printf '%s\n' "ERROR: ENGINEER_RUN does not identify engineer-runtime: $ENGINEER_RUN" >&2
    exit 1
  }
else
  _engineer_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
  _engineer_runtime_root=${RUNTIME_DIR:-$_engineer_root}
  _engineer_path_candidate=$(command -v engineer_run 2>/dev/null || true)
  _engineer_select \
    "$_engineer_root/engineer/bin/engineer_run" \
    "$_engineer_runtime_root/engineer/bin/engineer_run" \
    "$_engineer_root/.claude/engineer/bin/engineer_run" \
    "$_engineer_root/.codex/engineer/bin/engineer_run" \
    "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/engineer/bin/engineer_run" \
    "${CODEX_HOME:-$HOME/.codex}/engineer/bin/engineer_run" \
    "$_engineer_path_candidate" || {
    printf '%s\n' 'ERROR: No engineer-runtime launcher was found. Install the Claude or Codex workflow runtime or set ENGINEER_RUN.' >&2
    exit 1
  }
fi
export ENGINEER_RUN
engineer_run() {
  sh "$ENGINEER_RUN" "$@"
}
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  _engineer_path_escaped=$(printf '%s' "${ENGINEER_RUN%/*}" | sed 's/[\\`"$]/\\&/g')
  printf 'export PATH="%s:$PATH"\n' "$_engineer_path_escaped" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true
fi
# Built before the command for READABILITY, not as a fix. ShellCheck's SC2097/SC2098 here is a FALSE
# POSITIVE: prefix assignments take effect left to right (driven, bash and dash).
FIX_REPORT_FILE="${_pd}/${PADDED}-REVIEW-FIX.md"
# The installed adapter owns the ledger parser, validation, evidence reconciliation, and atomic write.
# It is advisory: preserve the workflow's non-blocking review behavior on any adapter failure.
engineer_run query review.reconcile \
  --phase "$PHASE_NUMBER" \
  --review-file "$REVIEW_FILE" \
  --disposition-file "$DISPOSITION_FILE" \
  --fix-report-file "$FIX_REPORT_FILE" \
  || echo "Code review disposition record skipped (non-blocking)."

COMMIT_DOCS=$(engineer_run query config-get commit_docs --raw 2>/dev/null || echo "true")
# `-f` FOLLOWS a symlink, so this could hand the commit helper a link the script above just
# refused to write through -- the guard and its consumer disagreeing about the same path.
if [ "$COMMIT_DOCS" = "true" ] && [ -f "${DISPOSITION_FILE}" ] && [ ! -L "${DISPOSITION_FILE}" ]; then
  engineer_run query commit "docs(${PADDED}): record code review disposition" --files "${DISPOSITION_FILE}" || true
fi
```
