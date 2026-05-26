import uuid
from typing import Awaitable, Callable, Dict, List, Tuple

import httpx
import numpy as np
import torch
from pymilvus.model.base import RerankResult
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.config import Settings, get_settings

settings: Settings = get_settings()

_embed_func: Callable[[List[str]], Awaitable[Dict]] | None = None
_reranker: Callable[[str, List[str], int], Awaitable[List[RerankResult]]] | None = None


def sigmoid(x):
    return float(1 / (1 + np.exp(-x)))


class GLMEmbeddingFunction:
    async def __call__(self, texts: List[str]) -> Dict:
        assert settings.glm_api_key and settings.glm_base_url
        async with httpx.AsyncClient(
            base_url=settings.glm_base_url,
            headers={
                "Authorization": f"Bearer {settings.glm_api_key}",
                "Content-Type": "application/json",
            },
        ) as client:
            resp = await client.post(
                "/paas/v4/embeddings",
                json={"model": "embedding-3", "input": texts, "dimensions": 1024},
            )
            resp_json = resp.json()
            if "error" in resp_json:
                raise Exception(
                    f"Request GLM api fail: {resp_json['error']['message']}"
                )
            ranked_data = sorted(resp.json()["data"], key=lambda item: item["index"])
            return {"dense": [item["embedding"] for item in ranked_data]}


class GLMRerankFunction:
    async def __call__(
        self, query: str, documents: List[str], top_k: int = 5
    ) -> List[RerankResult]:
        assert settings.glm_base_url and settings.glm_api_key
        async with httpx.AsyncClient(
            base_url=settings.glm_base_url,
            headers={
                "Authorization": f"Bearer {settings.glm_api_key}",
                "Content-Type": "application/json",
            },
        ) as client:
            resp = await client.post(
                "/paas/v4/rerank",
                json={
                    "model": "rerank",
                    "query": query,
                    "documents": documents,
                    "top_n": top_k,
                },
            )
            resp_json = resp.json()
            if "error" in resp_json:
                raise Exception(
                    f"Request GLM api fail: {resp_json['error']['message']}"
                )

            ranked_order = sorted(
                resp_json["results"],
                key=lambda item: item["relevance_score"],
                reverse=True,
            )

            if top_k:
                ranked_order = ranked_order[:top_k]

            return [
                RerankResult(
                    text=documents[item["index"]],
                    score=item["relevance_score"],
                    index=item["index"],
                )
                for item in ranked_order
            ]


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


def get_embedding_func():
    global _embed_func
    if _embed_func is None:
        _embed_func = GLMEmbeddingFunction()
    return _embed_func


def get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = GLMRerankFunction()
    return _reranker


async def encode_text(text: str | List[str]) -> Dict:
    func = get_embedding_func()
    if isinstance(text, str):
        text = [text]
    return await func(text)


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
        encoded = await encode_text(batch)
        dense_embeddings.extend(encoded["dense"])
        sparse_embeddings.extend(encoded["sparse"])

    return dense_embeddings, sparse_embeddings


def create_document_id() -> str:
    return uuid.uuid4().hex


def create_record_id() -> str:
    return uuid.uuid4().hex
