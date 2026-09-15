"""Tenant-scoped document ingestion into Supabase + pgvector."""
from __future__ import annotations

import hashlib
from typing import Any, Iterable
from uuid import uuid4

from .embeddings import LocalEmbeddingProvider


def chunk_text(text: str, *, chunk_size: int = 1200, overlap: int = 150) -> list[str]:
    text = " ".join(text.split())
    if not text:
        return []
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks


class DocumentIngestor:
    def __init__(self, client: Any, embedder: LocalEmbeddingProvider | None = None) -> None:
        self.client = client
        self.embedder = embedder or LocalEmbeddingProvider()

    def ingest(self, *, tenant_id: str, subject_id: str, name: str, text: str,
               source_uri: str | None = None, mime_type: str | None = "text/plain",
               metadata: dict | None = None) -> str:
        chunks = chunk_text(text)
        if not chunks:
            raise ValueError("document text cannot be empty")
        document_id = str(uuid4())
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        self.client.table("ai_platform_documents").insert({
            "id": document_id, "tenant_id": tenant_id, "subject_id": subject_id,
            "name": name, "source_uri": source_uri, "mime_type": mime_type,
            "content_sha256": digest,
        }).execute()
        vectors = self.embedder.embed(chunks)
        rows = []
        for index, (content, vector) in enumerate(zip(chunks, vectors)):
            rows.append({
                "id": str(uuid4()), "tenant_id": tenant_id, "document_id": document_id,
                "chunk_index": index, "content": content, "embedding": vector,
                "metadata": metadata or {},
            })
        self.client.table("ai_platform_document_chunks").insert(rows).execute()
        return document_id
