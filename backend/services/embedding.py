import os
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384
INDEX_PATH = os.path.join(os.path.dirname(__file__), "..", "faiss_index.bin")
ID_MAP_PATH = os.path.join(os.path.dirname(__file__), "..", "faiss_id_map.pkl")

# Lazy-loaded globals
_model = None
_index = None
_id_map = None  # maps FAISS internal position → job_id


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def get_index() -> tuple[faiss.IndexFlatIP, list[int]]:
    """Returns (FAISS index, id_map list). Creates new if none exists."""
    global _index, _id_map
    if _index is None:
        if os.path.exists(INDEX_PATH) and os.path.exists(ID_MAP_PATH):
            _index = faiss.read_index(INDEX_PATH)
            with open(ID_MAP_PATH, "rb") as f:
                _id_map = pickle.load(f)
        else:
            _index = faiss.IndexFlatIP(EMBEDDING_DIM)  # Inner Product (cosine after normalization)
            _id_map = []
    return _index, _id_map


def save_index():
    """Persist FAISS index and ID map to disk."""
    index, id_map = get_index()
    faiss.write_index(index, INDEX_PATH)
    with open(ID_MAP_PATH, "wb") as f:
        pickle.dump(id_map, f)


def embed_text(text: str) -> np.ndarray:
    """Embed a single text string. Returns normalized vector."""
    model = get_model()
    vec = model.encode(text, normalize_embeddings=True)
    return vec.astype(np.float32)


def add_to_index(job_id: int, embedding: np.ndarray):
    """Add a job embedding to the FAISS index."""
    index, id_map = get_index()
    vec = embedding.reshape(1, -1).astype(np.float32)
    index.add(vec)
    id_map.append(job_id)
    save_index()


def search_similar(query_embedding: np.ndarray, top_k: int = 50) -> list[tuple[int, float]]:
    """Search FAISS index for most similar jobs.

    Returns list of (job_id, similarity_score) sorted by score descending.
    """
    index, id_map = get_index()
    if index.ntotal == 0:
        return []

    k = min(top_k, index.ntotal)
    query = query_embedding.reshape(1, -1).astype(np.float32)
    scores, indices = index.search(query, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < len(id_map):
            results.append((id_map[idx], float(score)))
    return results
