"""Actionable failures at framework boundaries."""


class FrameworkError(Exception):
    """The operation could not safely complete."""


class PolicyError(FrameworkError):
    """Project constraints prohibit the requested operation."""
