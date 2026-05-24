"""SAP domain pack with SAP-specific validation rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from modelops_core.domain_packs.base import DomainPack


@dataclass(frozen=True)
class SAPContextRule:
    """SAP table → required EntityContext context_category."""

    sap_table: str
    required_context_category: str
    error_code: str


_SAP_CONTEXT_RULES: tuple[SAPContextRule, ...] = (
    SAPContextRule(
        "KNVV", "customer_sales_area", "SAP_CONTEXT_KNVV_REQUIRES_SALES_AREA"
    ),
    SAPContextRule(
        "KNB1", "customer_company_code", "SAP_CONTEXT_KNB1_REQUIRES_COMPANY_CODE"
    ),
    SAPContextRule(
        "KNVP",
        "customer_partner_function",
        "SAP_CONTEXT_KNVP_REQUIRES_PARTNER_FUNCTION",
    ),
    SAPContextRule("BUT000", "bp_central", "SAP_CONTEXT_BUT000_REQUIRES_BP_CENTRAL"),
)


class SAPDomainPack(DomainPack):
    """SAP-specific validation and modeling rules."""

    name = "sap"
    description = (
        "SAP context validation for FieldEndpoint objects with "
        "endpoint_type=sap_table_field."
    )

    def validate(
        self,
        objects: list[Any],
        registry: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Validate SAP context rules for FieldEndpoint objects."""
        results: list[dict[str, Any]] = []
        rules = {r.sap_table: r for r in _SAP_CONTEXT_RULES}

        for obj in objects:
            frontmatter = obj.frontmatter or {}
            if frontmatter.get("type") != "FieldEndpoint":
                continue

            endpoint_type = frontmatter.get("endpoint_type")
            sap_table = frontmatter.get("sap_table")
            if endpoint_type != "sap_table_field" or not sap_table:
                continue

            rule = rules.get(sap_table)
            if rule is None:
                continue

            entity_context_id = frontmatter.get("entity_context")
            context_category = None
            if entity_context_id:
                for candidate in objects:
                    if (
                        candidate.frontmatter
                        and candidate.frontmatter.get("id") == entity_context_id
                    ):
                        context_category = candidate.frontmatter.get("context_category")
                        break

            if context_category is None:
                results.append(
                    {
                        "severity": "ERROR",
                        "code": rule.error_code,
                        "message": (
                            f"SAP table '{sap_table}' requires an EntityContext "
                            f"with context_category '{rule.required_context_category}'."
                        ),
                        "object_id": frontmatter.get("id"),
                        "suggested_fix": (
                            f"Set entity_context to an EntityContext with "
                            f"context_category='{rule.required_context_category}'."
                        ),
                    }
                )
            elif context_category != rule.required_context_category:
                results.append(
                    {
                        "severity": "ERROR",
                        "code": rule.error_code,
                        "message": (
                            f"SAP table '{sap_table}' requires context_category "
                            f"'{rule.required_context_category}', got "
                            f"'{context_category}'."
                        ),
                        "object_id": frontmatter.get("id"),
                        "suggested_fix": (
                            f"Change context_category to "
                            f"'{rule.required_context_category}'."
                        ),
                    }
                )

        return results
