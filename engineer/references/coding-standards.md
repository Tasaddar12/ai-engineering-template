# Task-scoped coding standards

Before planning, implementing, fixing, investigating, verifying or reviewing code,
read the [standards index](../standards/README.md), then the matching routing
sections of its domain indexes. Use each index's heading outline to skip unrelated
tables in a large index.
Select and read only the files matching the task's language, framework and design
concerns before doing that work. Domains may combine; unrelated languages and
topics are not required reading.

## Bounded reads

1. Select a routing ID and the applicable targets in its index row. IDs are stable
   reading aliases, not runtime queries. A row listing several sections offers
   choices; it does not require every section. An unfragmented link identifies a
   document: use its section selectors for broad references; read focused rules
   marked **whole** with their complete instructions, bad/good examples and notes.
2. Locate the selected heading and its boundary using a heading-only search or
   outline. Ignore apparent headings inside fenced code examples. Resolve actual
   heading text and levels; do not load the entire broad document to find them.
3. Use the existing file reader's offset/limit or a shell line range calculated
   from the current file. Read from the selected heading through the line before
   the next actual heading of equal or higher level, or EOF. Include all nested
   subsections and complete examples; an anchor alone does not bound a read.
4. Include document applicability and any enclosing introductory rules needed to
   interpret the selection. Follow prerequisite/reference sections when the task
   needs their instructions. Expand the selection when new concerns arise; do not
   truncate instructions to meet a token target.
5. Reuse sections already available and current in your own context; merge
   overlapping reads. Record useful routing IDs in handoffs rather than copying
   whole standards into every prompt. Each independent agent reads its own
   applicable sections.

Line offsets are discovered at read time, never maintained in indexes. In the
legacy Python style guide, 12.11–12.15 are level-two headings, although 12.1–12.10
are level three: select those later topics individually, not as children of §12.
Missing or ambiguous headings are routing gaps to report, not reasons to silently
read an entire unrelated document.

Apply the selected references within the assigned scope and project instructions.
If coverage is missing or conflicts with an explicit project decision, report the
gap or conflict instead of inventing a standard. These files are references, not
skills; do not register or invoke them as skills.
