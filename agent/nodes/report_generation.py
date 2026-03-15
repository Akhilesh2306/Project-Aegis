"""File for report generation node"""

# Import External Libraries
import logging
from datetime import datetime, timezone

# Import Internal Packages
from agent.state import ComplianceState

# Setup logging
logger = logging.getLogger(__name__)


# =========================
# Report Generation Node
# =========================
def report_generation_node(state: ComplianceState) -> dict:
    """
    Assembles all findings and drafted clauses into a structured compliance report.
    Reads: clauses, findings, drafted_clauses
    Writes: report
    """

    findings = state.get("findings", [])
    drafted = state.get("drafted_clauses", [])
    clauses = state.get("clauses", [])

    logger.info(
        f"[report_generation] Generating report - {len(findings)} findings, {len(drafted)} drafted clauses"
    )

    # Build lookup of drafted clauses by clause_id so we can link findings to them
    drafted_by_id = {d["clause_id"]: d for d in drafted}

    # Enrich findings with their drafted replacements
    enriched_findings = []

    for finding in findings:
        enriched = dict(finding)
        draft = drafted_by_id.get(finding["clause_id"])
        if draft:
            enriched["suggested_text"] = draft["suggested_text"]
            enriched["changes_summary"] = draft["changes_summary"]
        enriched_findings.append(enriched)

    # Severity summary counts
    severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in findings:
        severity = f.get("severity", "LOW")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    # Build report
    report = {
        "contract_id": state["contract_id"],
        "filename": state["filename"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_clauses": len(clauses),
            "non_compliant_clauses": len(findings),
            "compliant_clauses": len(clauses) - len(findings),
            "severity_breakdown": severity_counts,
            "overall_status": ("COMPLIANT" if not findings else "NON-COMPLIANT"),
        },
        "findings": enriched_findings,
        "drafted_clauses": drafted,
        "status": "completed",
    }

    logger.info(
        f"[report_generation] REPORT COMPLETED - "
        f"status: {report["summary"]["overall_status"]}, "
        f"HIGH: {severity_counts["HIGH"]}, "
        f"MEDIUM: {severity_counts["MEDIUM"]}, "
        f"LOW: {severity_counts["LOW"]}"
    )

    return {
        "report": report,
    }
