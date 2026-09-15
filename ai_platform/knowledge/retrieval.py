"""Tenant-isolated vector retrieval through a Postgres RPC."""
from __future__ import annotations

from typing import Any

from .embeddings import LocalEmbeddingProvider


class SupabaseVectorRetriever:
    def __init__(self, client: Any, embedder: LocalEmbeddingProvider | None = None) -> None:
        self.client = client
        self.embedder = embedder or LocalEmbeddingProvider()

    def search(self, *, tenant_id: str, query: str, limit: int = 8, min_similarity: float = 0.2) -> list[dict]:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        if not query.strip():
            return []
        vector = self.embedder.embed([query])[0]
        result = self.client.rpc("match_ai_platform_document_chunks", {
            "p_tenant_id": tenant_id,
            "p_query_embedding": vector,
            "p_match_count": max(1, min(limit, 50)),
            "p_min_similarity": max(0.0, min(1.0, min_similarity)),
        }).execute()
        return list(getattr(result, "data", None) or [])
