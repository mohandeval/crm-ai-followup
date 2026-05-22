"""
src/vector/pinecone_client.py
──────────────────────────────
Pinecone Serverless client for the AI CRM project.

Handles:
  - Index creation (serverless on AWS us-east-1)
  - Upsert vectors (nurture content + testimonials)
  - Query / semantic search
  - Namespace separation (nurture vs testimonials)

SETUP STEPS (one-time):
  1. Go to https://www.pinecone.io/ → Sign up for free
  2. Create a new project → copy your API key
  3. Add PINECONE_API_KEY=pcsk_... to your .env file
  4. Run scripts/setup_pinecone.py to create indexes
  5. Run scripts/embed_and_upsert.py to load data

Pinecone Serverless vs Pods:
  - Serverless = pay per query, no provisioned infra, scales to zero
  - Perfect for this project (no running cost when idle)
"""

from pinecone import Pinecone, ServerlessSpec
from typing import Optional
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ── Namespaces ────────────────────────────────────────────────────────────────
NAMESPACE_NURTURE = "nurture-content"
NAMESPACE_TESTIMONIALS = "testimonials"


# ── Client singleton ──────────────────────────────────────────────────────────
_pc_client: Optional[Pinecone] = None


def get_pinecone_client() -> Pinecone:
    """
    Returns a cached Pinecone client instance.
    Raises ValueError if PINECONE_API_KEY is not set.
    """
    global _pc_client
    if _pc_client is None:
        if not settings.pinecone_api_key:
            raise ValueError(
                "PINECONE_API_KEY is not set. "
                "Get your key at https://www.pinecone.io/ and add it to .env"
            )
        _pc_client = Pinecone(api_key=settings.pinecone_api_key)
        logger.info("Pinecone client initialized")
    return _pc_client


# ── Index management ──────────────────────────────────────────────────────────
def create_index_if_not_exists(index_name: str) -> None:
    """
    Creates a Pinecone Serverless index if it doesn't already exist.
    Uses AWS us-east-1 (free tier compatible).

    Args:
        index_name: e.g. "crm-nurture-content" or "crm-testimonials"
    """
    pc = get_pinecone_client()
    existing = [idx.name for idx in pc.list_indexes()]

    if index_name in existing:
        logger.info(f"Pinecone index '{index_name}' already exists — skipping creation")
        return

    logger.info(f"Creating Pinecone serverless index: '{index_name}'")
    pc.create_index(
        name=index_name,
        dimension=settings.pinecone_embed_dimension,  # 1536 for text-embedding-3-small
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region=settings.pinecone_environment,  # us-east-1
        ),
    )
    logger.info(f"Index '{index_name}' created successfully")


def get_index(index_name: str):
    """Returns a connected Pinecone Index object."""
    pc = get_pinecone_client()
    return pc.Index(index_name)


# ── Upsert (write vectors) ────────────────────────────────────────────────────
def upsert_vectors(
    index_name: str,
    vectors: list[dict],
    namespace: str,
    batch_size: int = 100,
) -> None:
    """
    Upsert vectors into a Pinecone index in batches.

    Args:
        index_name: Target index name
        vectors: List of dicts with keys: id, values (embedding), metadata
        namespace: "nurture-content" or "testimonials"
        batch_size: How many vectors to upsert per API call

    Example vector dict:
        {
            "id": "nurture_001",
            "values": [0.12, -0.34, ...],  # 1536-dim embedding
            "metadata": {
                "title": "Success Story: Career Change at 40",
                "category": "testimonial",
                "objection_tags": ["age", "risk"],
            }
        }
    """
    index = get_index(index_name)
    total = len(vectors)
    logger.info(f"Upserting {total} vectors to '{index_name}/{namespace}'")

    for i in range(0, total, batch_size):
        batch = vectors[i : i + batch_size]
        index.upsert(vectors=batch, namespace=namespace)
        logger.debug(f"Upserted batch {i // batch_size + 1} ({len(batch)} vectors)")

    logger.info(f"Upsert complete: {total} vectors in '{namespace}'")


# ── Query (semantic search) ───────────────────────────────────────────────────
def query_index(
    index_name: str,
    query_embedding: list[float],
    namespace: str,
    top_k: int = 10,
    filter: Optional[dict] = None,
) -> list[dict]:
    """
    Semantic search against a Pinecone index.

    Args:
        index_name: Index to search
        query_embedding: The query vector (same dimension as stored vectors)
        namespace: "nurture-content" or "testimonials"
        top_k: Number of results to return
        filter: Optional metadata filter, e.g. {"category": {"$eq": "testimonial"}}

    Returns:
        List of match dicts: [{id, score, metadata}, ...]
    """
    if not query_embedding:
        logger.warning("Empty query embedding received — skipping Pinecone query")
        return []

    index = get_index(index_name)

    query_kwargs = dict(
        vector=query_embedding,
        top_k=top_k,
        namespace=namespace,
        include_metadata=True,
    )
    if filter:
        query_kwargs["filter"] = filter

    response = index.query(**query_kwargs)
    matches = response.get("matches", [])

    logger.info(
        f"Pinecone query returned {len(matches)} matches "
        f"from '{index_name}/{namespace}'"
    )
    return [
        {"id": m["id"], "score": m["score"], "metadata": m.get("metadata", {})}
        for m in matches
    ]


# ── Deduplication helper ──────────────────────────────────────────────────────
def deduplicate_results(results: list[dict], key: str = "id") -> list[dict]:
    """
    Remove duplicate matches by ID (can happen across multiple query calls).
    Keeps the highest-scoring duplicate.
    """
    seen = {}
    for item in results:
        item_id = item[key]
        if item_id not in seen or item["score"] > seen[item_id]["score"]:
            seen[item_id] = item
    deduped = sorted(seen.values(), key=lambda x: x["score"], reverse=True)
    logger.debug(f"Deduplicated {len(results)} → {len(deduped)} results")
    return deduped


# ── Health check ─────────────────────────────────────────────────────────────
def test_pinecone_connection() -> bool:
    """
    Verifies Pinecone API key is valid and lists available indexes.
    Returns True if connection works.
    """
    try:
        pc = get_pinecone_client()
        indexes = pc.list_indexes()
        names = [idx.name for idx in indexes]
        logger.info(f"Pinecone OK. Available indexes: {names}")
        return True
    except Exception as e:
        logger.error(f"Pinecone connection FAILED: {e}")
        return False
