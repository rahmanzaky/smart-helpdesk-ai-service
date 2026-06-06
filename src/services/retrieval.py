import faiss
import pickle
import numpy as np

from src.services.embedding import get_embedding

index = faiss.read_index("index/faiss.index")

with open("index/metadata.pkl", "rb") as f:
    metadata = pickle.load(f)

answers = metadata["answers"]

RELEVANCE_THRESHOLD = 0.95  # L2 distance; above this means no relevant match found

def retrieve(query, top_k=1):
    query_vector = get_embedding([query])

    D, I = index.search(
        np.array(query_vector).astype("float32"),
        top_k
    )

    if D[0][0] > RELEVANCE_THRESHOLD:
        return ""  # no relevant context found

    return answers[I[0][0]]