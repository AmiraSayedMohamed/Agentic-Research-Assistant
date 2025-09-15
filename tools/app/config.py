# app/config.py
SIMILARITY_THRESHOLD = 0.70   # >= this will be considered "plagiarized"
TOP_K = 5
SBERT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
PARAPHRASER_MODEL = "t5-base"   # change to a bigger model if you have GPU and need higher quality
MAX_INPUT_LENGTH = 512
