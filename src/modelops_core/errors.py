"""Domain exceptions for ModelOps MDM Core."""

from __future__ import annotations


class ModelOpsError(Exception):
    """Base domain error."""


class ValidationError(ModelOpsError):
    """Raised when deterministic validation fails."""


class PatchError(ModelOpsError):
    """Raised when a patch proposal is invalid or cannot be applied."""


class RepositoryError(ModelOpsError):
    """Raised when repository operations fail."""


class IndexError(ModelOpsError):
    """Raised when index building fails."""


class PathTraversalError(ModelOpsError):
    """Raised when a path escapes allowed boundaries."""
