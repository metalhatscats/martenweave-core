"""Domain packs for optional modeling rules and validation."""

from __future__ import annotations

from modelops_core.domain_packs.base import DomainPack, ValidationRule
from modelops_core.domain_packs.sap import SAPDomainPack

__all__ = ["DomainPack", "ValidationRule", "SAPDomainPack", "get_domain_packs"]


_REGISTERED_PACKS: dict[str, type[DomainPack]] = {
    "sap": SAPDomainPack,
}


def get_domain_packs(enabled: list[str] | None = None) -> list[DomainPack]:
    """Instantiate enabled domain packs.

    Args:
        enabled: List of pack identifiers to enable. If None or empty,
            no packs are loaded.

    Returns:
        List of instantiated domain packs.
    """
    if not enabled:
        return []
    packs: list[DomainPack] = []
    for key in enabled:
        pack_cls = _REGISTERED_PACKS.get(key.lower())
        if pack_cls is not None:
            packs.append(pack_cls())
    return packs
