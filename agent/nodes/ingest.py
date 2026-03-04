"""File for ingest node"""

# Import External Libraries
import logging

# Import Internal Packages
from agent.state import ComplianceState

# Setup logging
logger = logging.getLogger(__name__)


def ingest_node(state: ComplianceState) -> dict:
    """
    Retrieves contract from storage and extracts raw text.
    """

    logger.info(f"[ingest] Processing contract: {state["contract_id"]}")

    return {
        "raw_text": state.get("raw_text", ""),
    }
