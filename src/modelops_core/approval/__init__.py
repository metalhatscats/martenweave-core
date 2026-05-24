"""Approval gates and risk assessment for model changes."""

from __future__ import annotations

from modelops_core.approval.risk_service import (
    RiskAssessment,
    assess_change_request,
    compute_proposal_risk,
)

__all__ = [
    "RiskAssessment",
    "compute_proposal_risk",
    "assess_change_request",
]
