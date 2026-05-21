import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-reranker-v2-m3")
model = AutoModelForSequenceClassification.from_pretrained("BAAI/bge-reranker-v2-m3")
model.eval()


def sigmoid(x):
    return float(1 / (1 + np.exp(-x)))


pairs = [
    ["what is panda?", "hi"],
    [
        "what is panda?",
        "The giant panda (Ailuropoda melanoleuca), sometimes called a panda bear or simply panda, is a bear species endemic to China.",
    ],
]
with torch.no_grad():
    inputs = tokenizer(
        pairs, padding=True, truncation=True, return_tensors="pt", max_length=512
    )
    scores = (
        model(**inputs, return_dict=True)
        .logits.view(
            -1,
        )
        .float()
    )
    all_scores = [sigmoid(score) for score in scores]
    print(all_scores)
