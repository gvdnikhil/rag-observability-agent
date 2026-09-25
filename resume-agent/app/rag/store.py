import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class VectorStore:
    """In-memory FAISS index over sentence-transformer embeddings.
    Rebuilt on process start — fine at this content size, no external vector DB needed.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index: faiss.IndexFlatIP | None = None
        self.chunks: list[dict] = []

    def build(self, chunks: list[dict]) -> None:
        self.chunks = chunks
        embeddings = self.model.encode([c["text"] for c in chunks], normalize_embeddings=True)
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(np.asarray(embeddings, dtype="float32"))

    def search(self, query: str, k: int = 4) -> list[dict]:
        if self.index is None or not self.chunks:
            return []
        query_vec = self.model.encode([query], normalize_embeddings=True)
        scores, idxs = self.index.search(np.asarray(query_vec, dtype="float32"), min(k, len(self.chunks)))
        results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx == -1:
                continue
            results.append({**self.chunks[idx], "score": float(score)})
        return results
