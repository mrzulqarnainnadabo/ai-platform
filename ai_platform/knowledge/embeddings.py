"""Local sentence-transformers embeddings; no hosted embedding API required."""
from __future__ import annotations

from functools import lru_cache
from typing import Sequence


@lru_cache(maxsize=2)
def _model(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError("sentence-transformers is required for local embeddings") from exc
    return SentenceTransformer(model_name)


class LocalEmbeddingProvider:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name

    @property
    def dimension(self) -> int:
        return int(_model(self.model_name).get_sentence_embedding_dimension())

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = _model(self.model_name).encode(list(texts), normalize_embeddings=True)
        return [list(map(float, vector)) for vector in vectors]
