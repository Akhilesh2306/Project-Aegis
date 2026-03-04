"""File for report generation node"""

# Import External Libraries
import logging

# Import Internal Packages
from agent.state import ComplianceState

# Setup logging
logger = logging.getLogger(__name__)


def report_generation_node(state: ComplianceState) -> dict:
    """
    Assembles all findings and drafted clauses into a structured compliance report.
    """

    findings = state.get("findings", [])
    drafted = state.get("drafted_clauses", [])

    logger.info(
        f"[report_generation] Generating report - {len(findings)} findings, {len(drafted)} drafted clauses"
    )

    report = {
        "contract_id": state["contract_id"],
        "filename": state["filename"],
        "total_clauses": len(state.get("clauses", [])),
        "non_compliant_clauses": len(findings),
        "findings": findings,
        "drafted_clauses": drafted,
        "status": "completed",
    }

    return {
        "report": report,
    }
