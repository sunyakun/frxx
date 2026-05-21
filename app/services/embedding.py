import uuid
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
from pymilvus.model.base import RerankResult
from pymilvus.model.hybrid import BGEM3EmbeddingFunction
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.config import Settings, get_settings

settings: Settings = get_settings()

_embed_func: Optional[BGEM3EmbeddingFunction] = None
_reranker: Optional["BGERerankFunction"] = None


def sigmoid(x):
    return float(1 / (1 + np.exp(-x)))


class BGERerankFunction:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-reranker-v2-m3")
        self.model = AutoModelForSequenceClassification.from_pretrained(
            "BAAI/bge-reranker-v2-m3"
        )
        self.model.eval()

    def __call__(
        self, query: str, documents: List[str], top_k: int = 5
    ) -> List[RerankResult]:
        pairs = [[query, doc] for doc in documents]
        with torch.no_grad():
            inputs = self.tokenizer(
                pairs,
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=512,
            )
            scores = (
                self.model(**inputs, return_dict=True)
                .logits.view(
                    -1,
                )
                .float()
            )
        scores = [sigmoid(score) for score in scores]
        ranked_order = sorted(
            list(range(len(scores))), key=lambda i: scores[i], reverse=True
        )[:top_k]

        if top_k:
            ranked_order = ranked_order[:top_k]

        return [
            RerankResult(text=documents[i], score=scores[i], index=i)
            for i in ranked_order
        ]


def get_embedding_func() -> BGEM3EmbeddingFunction:
    global _embed_func
    if _embed_func is None:
        _embed_func = BGEM3EmbeddingFunction()
    return _embed_func


def get_reranker() -> BGERerankFunction:
    global _reranker
    if _reranker is None:
        _reranker = BGERerankFunction()
    return _reranker


def encode_text(text: str | List[str]) -> Dict:
    func = get_embedding_func()
    if isinstance(text, str):
        text = [text]
    return func(text)


def chunk_text(
    content: str, max_characters: int = 1000, overlap: int = 50
) -> List[str]:
    chunks = []
    start = 0
    content_length = len(content)

    while start < content_length:
        end = start + max_characters
        if end > content_length:
            end = content_length
        chunk = content[start:end]
        chunks.append(chunk)
        start = end - overlap
        if start < 0:
            start = 0

    return chunks


async def encode_chunks_async(
    chunks: List[str], batch_size: int = 32
) -> Tuple[List[List[float]], List[List[Tuple[int, float]]]]:
    dense_embeddings = []
    sparse_embeddings = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        encoded = encode_text(batch)
        dense_embeddings.extend(encoded["dense"])
        sparse_embeddings.extend(encoded["sparse"])

    return dense_embeddings, sparse_embeddings


def create_document_id() -> str:
    return uuid.uuid4().hex


def create_record_id() -> str:
    return uuid.uuid4().hex
