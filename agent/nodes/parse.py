"""File for parse node"""

# Import External Libraries
import logging

# Import Internal Packages
from agent.state import ComplianceState
from services.document_parser import DocumentParser

# Setup logging
logger = logging.getLogger(__name__)

# DocumentParser instance
parser = DocumentParser()


def parse_node(state: ComplianceState) -> dict:
    """
    Segments raw contract text into individual clauses.
    Reads: raw_text, filename
    Writes: clauses
    """

    logger.info("[parse] Parsing contract into clauses")

    raw_text = state.get("raw_text", "")
    filename = state.get("filename", "contract.md")

    if not raw_text:
        logger.warning("[parse] No raw text found in state - skipping")
        return {
            "clauses": [],
        }

    try:
        clauses = parser.parse(filename=filename, text=raw_text)

        logger.info(f"[parse] Successfully parsed {len(clauses)} clauses")

        # Logging each title for visibility during development phase
        for clause in clauses:
            logger.info(f"[parse] -> {clause["clause_id"]}: {clause["title"]}")

        return {"clauses": clauses}

    except Exception as e:
        logger.error(f"[parse] Failed to parse contract: {e}")
        return {"clauses": [], "error": f"Parse failed: {str(e)}"}
