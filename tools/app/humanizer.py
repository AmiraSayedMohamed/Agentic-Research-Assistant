# app/humanizer.py
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

class Humanizer:
    def __init__(self, model_name: str = "Vamsi/T5_Paraphrase_Paws"):
        print(f"Loading paraphrasing model (CPU only): {model_name}")
        self.device = torch.device("cpu")  # Force CPU
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(self.device)

    def humanize(self, text: str, num_return_sequences: int = 5) -> list:
        """
        Generate multiple paraphrases of input text.
        Returns a list of rewritten sentences.
        """
        input_text = f"paraphrase: {text} </s>"

        encoding = self.tokenizer(
            input_text,
            return_tensors="pt",
            max_length=128,       # lower for faster CPU processing
            truncation=True,
            padding="max_length"
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                input_ids=encoding["input_ids"],
                attention_mask=encoding["attention_mask"],
                max_length=128,          # reduce length for speed
                num_return_sequences=num_return_sequences,
                num_beams=5,             # smaller beam search → faster
                temperature=1.2,
                top_k=40,
                top_p=0.9,
                early_stopping=True
            )

        decoded = [
            self.tokenizer.decode(output, skip_special_tokens=True).strip()
            for output in outputs
        ]

        return list(set(decoded))  # remove duplicates
