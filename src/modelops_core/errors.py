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


class ResourceLimitExceeded(ModelOpsError):
    """Raised when an operation exceeds a configured resource limit.

    The *resource* field identifies which limit was hit (e.g. ``max_index_objects``).
    The *message* field contains a human-readable explanation with recovery hints.
    """

    def __init__(self, resource: str, message: str) -> None:
        self.resource = resource
        self.message = message
        super().__init__(message)
