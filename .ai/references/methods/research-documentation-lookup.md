# Documentation lookup

1. Read repository manifests, lockfiles and source to identify the exact library
   and version. A current web page can describe a different version.
2. If the host exposes Context7, resolve the library identity before querying
   its documentation. Use only tools that are actually available.
3. Otherwise read the official versioned documentation and release notes with
   the host's available browser, search or fetch tools. Follow search results
   to primary source pages; snippets are discovery, not sufficient evidence.
4. When documentation is unclear, inspect the tagged upstream source or a
   bounded reproduction when execution is authorized. Record contradictions.
5. Record URL/path, applicable version, access date and the supported claim.
   If access fails, state that evidence is unavailable; never treat failure to
   fetch as evidence that a capability does not exist.

Do not install a CLI or SDK just to obtain workflow instructions. These methods
are already bundled. Subject-matter research can still require network access;
if unavailable, report the specific unknown and continue independent local work.
Do not execute packages downloaded from a registry merely to look up docs.
