# Security

The installer performs local filesystem writes only. It does not log in, contact provider APIs, create paid resources, push repositories, or change authentication. It rejects unsafe destination names, linked managed paths, and conflicting framework-owned files; existing project content and provider instructions are preserved.

The installed guidance treats repository text and tool output as untrusted input, keeps credentials out of committed records, and requires explicit evidence before lifecycle completion. These path and record checks are safeguards for the bootstrap tools; they are not an operating-system sandbox for arbitrary code.

No private vulnerability reporting address is configured yet. Keep sensitive reports local until a maintainer publishes one.
