import faiss
import pickle
import numpy as np

from src.services.embedding import get_embedding

index = faiss.read_index("index/faiss.index")

with open("index/metadata.pkl", "rb") as f:
    metadata = pickle.load(f)

questions = metadata["questions"]
answers = metadata["answers"]

RELEVANCE_THRESHOLD = 0.75  # L2 distance; tuned for manufacturing domain
TOP_K = 3

def retrieve(query, top_k=TOP_K):
    query_vector = get_embedding([query])

    k = min(top_k, len(answers))
    D, I = index.search(
        np.array(query_vector).astype("float32"),
        k
    )

    results = []
    for i in range(k):
        dist = D[0][i]
        idx = I[0][i]
        if dist <= RELEVANCE_THRESHOLD and idx >= 0:
            results.append({
                "answer": answers[idx],
                "question": questions[idx],
                "score": float(dist),
                "index": int(idx),
            })

    return results
