"""File for error handler node"""

# Import External Libraries
import logging

# Import Internal Packages
from agent.state import ComplianceState

# Setup logging
logger = logging.getLogger(__name__)


def error_handler_node(state: ComplianceState) -> dict:
    """
    Handles errors from any node - logs and increments retry count
    """

    error = state.get("error", "Unknown error")
    retry_count = state.get("retry_count", 0)

    logger.info(
        f"[error_handler] Error encountered (attempt {retry_count + 1}/3): {error}"
    )

    return {
        "retry_count": retry_count + 1,
        "error": None,  # clear error so retry can proceed
    }
