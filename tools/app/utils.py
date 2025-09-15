# app/utils.py
import re
import random

def clean_text(text: str) -> str:
    # basic cleaning
    return text.strip()

def rule_based_humanize(text: str) -> str:
    contractions = {
        "do not": "don't",
        "cannot": "can't",
        "will not": "won't",
        "I am": "I'm",
        "it is": "it's",
        "do n't": "don't"
    }
    # apply contractions (case-insensitive)
    for k, v in contractions.items():
        text = re.sub(rf"\b{k}\b", v, text, flags=re.IGNORECASE)

    # optionally add small fillers randomly to avoid robotic tone
    fillers = ["you know", "actually", "basically", "to be honest"]
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for i in range(len(sentences)):
        if random.random() > 0.8 and len(sentences[i].strip()) > 10:
            sentences[i] = sentences[i].rstrip() + ", " + random.choice(fillers)
    return " ".join(sentences)
