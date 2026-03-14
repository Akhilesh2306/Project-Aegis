"""File for policy retrieval node"""

# Import External Libraries
import logging

# Import Internal Packages
from services.vector_store import VectorStore
from agent.state import ComplianceState, PolicyChunk

# Setup logging
logger = logging.getLogger(__name__)

# Single Instance - vector store connection is expensive to create
vector_store = VectorStore()


def policy_retrieval_node(state: ComplianceState) -> dict:
    """
    Retrieves relevant policy chunks for each parsed clause from vector store.
    Reads: clauses
    Writes: policy_chunks
    """

    clauses = state.get("clauses", [])

    if not clauses:
        logger.warning("[policy_retrieval] No clauses found in state - skipping")
        return {"policy_chunks": []}

    # Search for relevant policies for each clause
    # Use set data structure to track policy IDs already retrieved - avoid duplicates
    seen_policy_ids: set[str] = set()
    all_chunks: list[PolicyChunk] = []

    for clause in clauses:
        # Build search query from title + first 200 chars of content
        query = f"{clause["title"]} {clause["content"][:200]}"

        results = vector_store.search(
            query,
            top_k=2,
        )

        for chunk in results:
            if chunk["policy_id"] not in seen_policy_ids:
                seen_policy_ids.add(chunk["policy_id"])
                all_chunks.append(chunk)

                logger.info(
                    f"[policy_retrieval] Clause: '{clause["title"]}' -> "
                    f"Policy {chunk["policy_id"]} "
                    f"(score: {chunk["relevance_score"]})"
                )

    logger.info(f"[policy_retrieval] Retrieved {len(all_chunks)} unique policy chunks")

    return {
        "policy_chunks": all_chunks,
    }
