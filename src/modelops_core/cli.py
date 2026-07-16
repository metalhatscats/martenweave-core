"""Typer CLI for Martenweave Core."""

from __future__ import annotations

from modelops_core.commands import (  # noqa: F401
    dataset,
    exchange,
    health_reports,
    impact_trace,
    migrate_audit,
    query_search,
    run_commands,
    scaffold,
    serve_mcp,
    standalone,
    validate_index,
)
from modelops_core.commands._common import app
from modelops_core.commands.ai_provider import ai_provider_app
from modelops_core.commands.assessment import (
    agent_app,
    assessment_app,
    assessment_review_app,
    demo_bundle_app,
    draft_app,
    evidence_app,
)
from modelops_core.commands.change_request import cr_app
from modelops_core.commands.health_reports import review_pack_app
from modelops_core.commands.proposal import proposal_app
from modelops_core.commands.run_commands import run_app
from modelops_core.commands.workflow import decisions_app, notifications_app

app.add_typer(ai_provider_app, name="ai-provider")
app.add_typer(review_pack_app, name="review-pack")
app.add_typer(proposal_app, name="proposal")
app.add_typer(cr_app, name="change-request")
app.add_typer(notifications_app, name="notifications")
app.add_typer(decisions_app, name="decisions")
app.add_typer(run_app, name="run")
app.add_typer(evidence_app, name="evidence")
app.add_typer(draft_app, name="issue-draft")
app.add_typer(assessment_review_app, name="assessment-review")
app.add_typer(demo_bundle_app, name="demo-bundle")
app.add_typer(assessment_app, name="assessment")
app.add_typer(agent_app, name="agent")

if __name__ == "__main__":
    app()
