"""
One-time script — ingests company policies into the vector store.
Run this before starting the agent for the first time, and
whenever policies change.

Usage:
    uv run python scripts/ingest_policies.py
"""

# Import external libraries
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import internal modules
from config.logging import setup_logging

# Setup logging
setup_logging()

import logging

logger = logging.getLogger(__name__)


def parse_policy_file(filepath: str) -> list[dict]:
    """
    Parses company_policy.md into individual policy chunks.
    Each ## section becomes one chunk.

    Returns list of dicts with: id, text, policy_id, title
    """
    text = open(filepath).read()
    chunks = []

    # Split on ## headings
    sections = re.split(r"\n(?=## )", text)

    for section in sections:
        section = section.strip()
        if not section or not section.startswith("## "):
            continue

        lines = section.split("\n")
        heading = lines[0].strip()
        content = "\n".join(lines[1:]).strip()

        if not content:
            continue

        # Extract policy ID and title from heading
        # Pattern: "## P-001: Termination Notice"
        heading_clean = re.sub(r"^##\s*", "", heading)
        match = re.match(r"^(P-\d+):\s*(.+)$", heading_clean)

        if match:
            policy_id = match.group(1)
            title = match.group(2).strip()
        else:
            # Fallback for headings without P-XXX format
            policy_id = f"P-{len(chunks):03d}"
            title = heading_clean

        chunk = {
            "id": policy_id,
            "policy_id": policy_id,
            "title": title,
            "text": f"{title}\n\n{content}",
        }
        chunks.append(chunk)
        logger.info(f"Parsed policy: {policy_id} — {title}")

    return chunks


def main():
    from services.vector_store import VectorStore

    policy_file = "tests/fixtures/policies/company_policy.md"

    if not os.path.exists(policy_file):
        logger.error(f"Policy file not found: {policy_file}")
        sys.exit(1)

    logger.info(f"Reading policies from: {policy_file}")
    chunks = parse_policy_file(policy_file)
    logger.info(f"Parsed {len(chunks)} policy chunks")

    store = VectorStore()
    store.add_policies(chunks)

    logger.info(
        f"✅ Ingestion complete — " f"{store.count} policies now in vector store"
    )

    # Quick verification — test a sample search
    logger.info("\n🔍 Running verification search...")
    results = store.search("termination notice period", top_k=2)
    for r in results:
        logger.info(
            f"   [{r['policy_id']}] {r['title']} " f"(score: {r['relevance_score']})"
        )


if __name__ == "__main__":
    main()
