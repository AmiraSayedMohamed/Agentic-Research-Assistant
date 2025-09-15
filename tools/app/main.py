# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from app.humanizer import Humanizer
from app.plagiarism import PlagiarismChecker
from app.config import SIMILARITY_THRESHOLD, TOP_K
import json, os, numpy as np

app = FastAPI(title="Humanizer + Plagiarism Checker")

humanizer = None
checker = None

class ProcessRequest(BaseModel):
    text: str
    threshold: float = SIMILARITY_THRESHOLD
    top_k: int = TOP_K
    rewrite: bool = True

@app.on_event("startup")
async def startup_event():
    global humanizer, checker
    print("🚀 Initializing models on CPU... please wait.")
    humanizer = Humanizer()
    checker = PlagiarismChecker()

    # Load saved DB if exists
    if os.path.exists("db_texts.json") and os.path.exists("db_embeddings.npy"):
        with open("db_texts.json", "r", encoding="utf-8") as f:
            texts = json.load(f)
        emb = np.load("db_embeddings.npy")
        checker.texts = texts
        checker.embeddings = emb.astype("float32")
    else:
        checker.ingest_texts([])

@app.post("/process")
async def process(req: ProcessRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty text")

    matches = checker.is_plagiarized(text, threshold=req.threshold, top_k=req.top_k)

    if matches and req.rewrite:
        # generate paraphrase candidates
        candidates = humanizer.humanize(text, num_return_sequences=3)  # smaller for CPU

        # pick best candidate with lowest plagiarism score
        best_candidate, best_score = None, 1.0
        for cand in candidates:
            cand_matches = checker.is_plagiarized(cand, threshold=req.threshold, top_k=req.top_k)
            avg_score = sum(m['score'] for m in cand_matches) / len(cand_matches) if cand_matches else 0
            if avg_score < best_score:
                best_score, best_candidate = avg_score, cand

        return {
            "status": "plagiarized",
            "original_text": text,
            "matches": matches,
            "rewritten": best_candidate if best_candidate else candidates[0],
            "rewritten_score": best_score
        }
    else:
        return {
            "status": "original" if not matches else "plagiarized_no_rewrite",
            "text": text,
            "matches": matches
        }

@app.post("/ingest")
async def ingest(documents: List[str]):
    checker.add_texts(documents)
    with open("db_texts.json", "w", encoding="utf-8") as f:
        json.dump(checker.texts, f, ensure_ascii=False, indent=2)
    np.save("db_embeddings.npy", checker.embeddings)
    return {"ingested": len(documents), "db_size": len(checker.texts)}

@app.get("/health")
async def health():
    return {"status": "ok"}
