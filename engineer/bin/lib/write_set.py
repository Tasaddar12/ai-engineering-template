"""Shared fail-loud parse ``Result`` and per-surface write-set contracts.

Ported from upstream gsd-core ``src/write-set.cts`` at pinned commit
d37ff11b47258b560f0cf8f1132b42ecd90e0c79 (MIT, Copyright (c) 2026 Open GSD).
Pure, stdlib only, no I/O.

Shapes (JSON-compatible dicts, same field names as upstream):
- ``Result``: ``{"ok": True, "value": value}`` or ``{"ok": False, "reason": str}``.
  A parse operation returns a typed Result, never a bare ``None`` a caller could
  mistake for "empty but fine".
- ``WriteOutcome``: ``{"surface": str, "applied": bool}`` with an optional
  ``"requirement"`` naming the entity the outcome belongs to.
- ``WriteSet``: a list of WriteOutcome. A command mutating more than one surface
  reports one outcome per surface; "did it fully succeed" is true only if every
  surface applied (never OR the surfaces into one flag).

Deviations:
- Upstream exports TypeScript types (``Result``, ``WriteOutcome``, ``WriteSet``)
  erased at compile time; Python has no counterpart, so only ``write_set_complete``
  exists at runtime and the shapes above are the documented contract.
"""
from __future__ import annotations

__all__ = ["write_set_complete"]


def write_set_complete(ws):
    """True only if the write-set is non-empty AND every surface in it applied.

    An empty write-set is never complete: treating it as vacuously true would let a
    no-op masquerade as a full success.
    """
    return len(ws) > 0 and all(bool(outcome["applied"]) for outcome in ws)
