"""File for web search node"""

# Import External Libraries
import logging

# Import Internal Packages
from agent.state import ComplianceState

# Setup logging
logger = logging.getLogger(__name__)


def web_search_node(state: ComplianceState) -> dict:
    """
    Searches for relevant external regulations and standards.
    """

    logger.info("[web_search] Searching for external regulations")

    return {
        "web_results": [],
    }
