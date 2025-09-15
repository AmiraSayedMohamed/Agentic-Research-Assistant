# app/plagiarism.py
import os
import numpy as np
from sentence_transformers import SentenceTransformer, util
from .config import SBERT_MODEL, SIMILARITY_THRESHOLD, TOP_K

# Try to import faiss for fast nearest-neighbor search (optional).
try:
    import faiss
    _FAISS_AVAILABLE = True
except Exception:
    faiss = None
    _FAISS_AVAILABLE = False

class PlagiarismChecker:
    def __init__(self, model_name=SBERT_MODEL):
        self.model = SentenceTransformer(model_name)
        self.texts = []            # list of strings (DB)
        self.embeddings = None     # numpy array of embeddings
        self.index = None

    def ingest_texts(self, texts: list):
        """
        Ingest (or re-ingest) the full list of DB texts.
        For large datasets use batching.
        """
        if not texts:
            return
        self.texts = texts
        emb = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        self.embeddings = emb.astype("float32")
        if _FAISS_AVAILABLE:
            dim = self.embeddings.shape[1]
            faiss.normalize_L2(self.embeddings)
            self.index = faiss.IndexFlatIP(dim)
            self.index.add(self.embeddings)
        else:
            # index remains None; we'll use cosine similarity with sentence-transformers util
            self.index = None

    def add_texts(self, texts: list):
        """Append new texts and update embeddings/index (small-scale append)."""
        if not texts:
            return
        if not self.texts:
            self.ingest_texts(texts)
            return
        new_emb = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False).astype("float32")
        self.texts.extend(texts)
        if self.embeddings is None:
            self.embeddings = new_emb
        else:
            self.embeddings = np.vstack([self.embeddings, new_emb])
        if _FAISS_AVAILABLE:
            faiss.normalize_L2(new_emb)
            self.index.add(new_emb)

    def is_plagiarized(self, query: str, threshold=SIMILARITY_THRESHOLD, top_k=TOP_K):
        """
        Returns a list of matches with similarity scores (descending).
        Each match: {"id": idx, "text": text, "score": float}
        """
        if not self.texts:
            return []

        q_emb = self.model.encode([query], convert_to_numpy=True).astype("float32")
        if _FAISS_AVAILABLE and self.index is not None:
            faiss.normalize_L2(q_emb)
            D, I = self.index.search(q_emb, top_k)
            matches = []
            for score, idx in zip(D[0], I[0]):
                matches.append({"id": int(idx), "text": self.texts[idx], "score": float(score)})
        else:
            # compute cosine similarities via sentence-transformers util
            db_embs = self.embeddings
            scores = util.cos_sim(q_emb, db_embs)[0].cpu().numpy()
            top_idx = np.argsort(-scores)[:top_k]
            matches = [{"id": int(i), "text": self.texts[i], "score": float(scores[i])} for i in top_idx]

        # filter by threshold
        filtered = [m for m in matches if m["score"] >= threshold]
        return filtered
