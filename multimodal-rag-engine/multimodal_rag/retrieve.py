"""Retrieve: question -> BGE query vector -> Pinecone -> list[Hit].

Hit text comes from `chunks.jsonl`, the same file the live index was built from
(README, re-index step 4), not from Pinecone metadata.
"""

import json
import os
from pathlib import Path

from pinecone import Pinecone
from pinecone.errors import PineconeConnectionError, PineconeTimeoutError, ServiceError

from multimodal_rag.config import (
    CHUNKS_PATH,
    EMBED_MODEL,
    INDEX_NAME,
    NAMESPACE,
    PINECONE_TIMEOUT_S,
    QUERY_PREFIX,
    TOP_K,
)
from multimodal_rag.contracts import Chunk, Hit


class QueryError(Exception):
    """The query path failed: Pinecone unreachable, index and chunk file out of
    sync, or Claude stopped early or errored. The message says which."""


def load_chunks(path: Path = CHUNKS_PATH) -> dict[str, Chunk]:
    """chunk_id -> Chunk for every line of `chunks.jsonl`."""
    with path.open(encoding="utf-8") as f:
        chunks = (Chunk(**json.loads(line)) for line in f)
        return {c.chunk_id: c for c in chunks}


class Retriever:
    """Holds the BGE model, the Pinecone index handle and the chunk map.

    Build once per process; `search` is then one local embed + one Pinecone call.
    """

    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(EMBED_MODEL, device="cpu")
        self.chunks = load_chunks()
        pc = Pinecone(
            api_key=os.environ["PINECONE_API_KEY"], timeout=PINECONE_TIMEOUT_S
        )
        self.index = pc.Index(INDEX_NAME)

    def embed_query(self, question: str) -> list[float]:
        """Normalized BGE vector of QUERY_PREFIX + question (local, no network)."""
        vec = self.model.encode(QUERY_PREFIX + question, normalize_embeddings=True)
        return vec.tolist()

    def search(self, question: str, k: int = TOP_K) -> list[Hit]:
        """Top-k chunks by cosine similarity, best first.

        Raises QueryError if Pinecone times out, is unreachable or returns 5xx
        (the SDK has already retried), or returns an id missing from chunks.jsonl.
        """
        try:
            res = self.index.query(
                vector=self.embed_query(question),
                top_k=k,
                namespace=NAMESPACE,
                timeout=PINECONE_TIMEOUT_S,
            )
        except (PineconeTimeoutError, PineconeConnectionError, ServiceError) as e:
            raise QueryError(f"Pinecone unavailable: {type(e).__name__}: {e}") from e
        hits = []
        for m in res.matches:
            if m.id not in self.chunks:
                raise QueryError(f"{m.id} is in {INDEX_NAME} but not in chunks.jsonl")
            hits.append(Hit(self.chunks[m.id], float(m.score)))
        return hits
