# ingest_db.py
import json
import os
from app.plagiarism import PlagiarismChecker

# Example: read a folder of .txt files (one document per file).
DATA_DIR = "reference_texts"

def load_texts_from_folder(folder):
    texts = []
    for fname in os.listdir(folder):
        if fname.endswith(".txt"):
            with open(os.path.join(folder, fname), "r", encoding="utf-8") as f:
                texts.append(f.read())
    return texts

if __name__ == "__main__":
    pc = PlagiarismChecker()
    texts = load_texts_from_folder(DATA_DIR)
    print(f"Ingesting {len(texts)} docs...")
    pc.ingest_texts(texts)
    # Optionally persist texts and embeddings to disk for fast load next time:
    # e.g. save texts as JSON and embeddings as .npy
    import numpy as np
    np.save("db_embeddings.npy", pc.embeddings)
    with open("db_texts.json", "w", encoding="utf-8") as f:
        json.dump(pc.texts, f, ensure_ascii=False, indent=2)
    print("Saved db_texts.json and db_embeddings.npy")
