"""Typed errors so the CLI can print a clean message instead of a traceback.

Anything raised from this module is an expected failure: a missing binary, a bad
video, a failed pipeline step. Unexpected bugs keep their normal traceback so we
do not hide them behind a friendly one liner.
"""


class OrbisError(Exception):
    """Base class for expected, user facing failures."""


class MissingToolError(OrbisError):
    """A binary required by the pipeline is not on PATH."""


class CaptureValidationError(OrbisError):
    """The input video cannot be used as a capture."""


class WorkspaceNameError(OrbisError):
    """The workspace name is not safe to use as a directory name."""


class PipelineError(OrbisError):
    """An external pipeline command failed or produced no output."""
