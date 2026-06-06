import sys
import os

# sys.path.append(os.path.join(os.path.dirname(__file__), "..", "services"))

import pandas as pd
import faiss
import numpy as np
import pickle

from src.services.embedding import get_embedding

# LOAD DATASET
df = pd.read_csv("data/faq_epson_manufacturing.csv")

df.columns = df.columns.str.strip().str.lower()

if "anwer" in df.columns:
    df.rename(columns={"anwer": "answer"}, inplace=True)

questions = df["question"].astype(str).tolist()
answers = df["answer"].astype(str).tolist()

# EMBEDDING
embeddings = get_embedding(questions)

# BUILD FAISS
dimension = embeddings.shape[1]

index = faiss.IndexFlatL2(dimension)

index.add(np.array(embeddings).astype("float32"))

# SAVE INDEX
faiss.write_index(index, "index/faiss.index")

# SAVE METADATA
with open("index/metadata.pkl", "wb") as f:
    pickle.dump(
        {
            "questions": questions,
            "answers": answers
        },
        f
    )

print("Index berhasil dibuat!")