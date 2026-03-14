"""File for vector store service"""

# Import External Libraries
import re
import logging
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

# Import Internal Packages
from config.settings import get_settings
from agent.state import ComplianceState, PolicyChunk

# Setup logging
logger = logging.getLogger(__name__)
settings = get_settings()


# === Vector Store ===
class VectorStore:
    """
    Wraps ChromaDB for policy storage and semantic retrieval.

    Lifecycle:
        1. ingest_policies.py calls add_policies() once at setup time
        2. policy_retrieval node calls search() at runtime per contract
    """

    COLLECTION_NAME = "aegis_policies"

    def __init__(self) -> None:
        # Persistent client = data survives between runs
        self._client = chromadb.PersistentClient(path=".chromadb")

        # OpenAI embeddings - same model used for storage and search
        self._embedding_fn = OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name="text-embedding-3-small",
        )

        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            embedding_function=self._embedding_fn,  # type: ignore
            metadata={"hsnw:space": "cosine"},  # cosine similarity
        )

        logger.info(
            f"Vector store initialized - {self._collection.count()} policies loaded"
        )

    def add_policies(self, chunks: list[dict]) -> None:
        """
        Adds policy chunks to vector store.
        Each chunk must have - id, text, policy_id, title
        """

        if not chunks:
            logger.warning("No policy chunks provided to add_policies")
            return

        # Only add chunks not already in the store
        existing = set(self._collection.get()["ids"])
        new_chunks = [c for c in chunks if c["id"] not in existing]

        if not new_chunks:
            logger.info(
                "All policy chunks already in vector store - skipping add_policies"
            )
            return

        self._collection.add(
            ids=[c["id"] for c in new_chunks],
            documents=[c["text"] for c in new_chunks],
            metadatas=[
                {
                    "policy_id": c["policy_id"],
                    "title": c["title"],
                }
                for c in new_chunks
            ],
        )
        logger.info(f"Added {len(new_chunks)} policy chunks to vector store")

    def search(self, query: str, top_k: int = 3) -> list[PolicyChunk]:
        """
        Searches and returns top_k semantically similar policy chunks to query.
        """
        if self._collection.count() == 0:
            logger.warning("Vector store is empty - skipping search")
            return []

        results = self._collection.query(
            query_texts=[query],
            n_results=min(top_k, self._collection.count()),
        )
        policy_chunks: list[PolicyChunk] = []

        for i, doc in enumerate(results["documents"][0]):  # type: ignore
            metadata = results["metadatas"][0][i]  # type: ignore
            distance = results["distances"][0][i]  # type: ignore

            relevance_score = round(1 - distance, 4)

            chunk: PolicyChunk = {
                "policy_id": metadata["policy_id"],
                "title": metadata["title"],
                "content": doc,
                "relevance_score": relevance_score,
            }  # type: ignore
            policy_chunks.append(chunk)

        return policy_chunks

    def clear(self) -> None:
        """Wipes all policies — useful for re-ingestion during development."""
        self._client.delete_collection(self.COLLECTION_NAME)
        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            embedding_function=self._embedding_fn,  # type: ignore
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("Vector store cleared")

    @property
    def count(self) -> int:
        return self._collection.count()
