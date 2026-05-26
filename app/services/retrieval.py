from typing import Any, Dict, List, Literal, Optional

from pymilvus import AnnSearchRequest, RRFRanker

from app.services.embedding import get_reranker
from app.utils.clients import get_milvus_client


async def search(
    query: str,
    collection_name: str,
    top_k: int = 3,
    mode: Literal["hybrid", "dense", "sparse"] = "dense",
    ranker: Optional[Any] = None,
    output_fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    from app.services.embedding import encode_text

    if output_fields is None:
        output_fields = ["id", "text", "metadata"]

    client = get_milvus_client()
    embedding = await encode_text(query)

    # 召回并粗排
    if mode == "hybrid":
        if ranker is None:
            ranker = RRFRanker()

        dense_req = AnnSearchRequest(
            embedding["dense"], "dense_embed", param={"metric_type": "IP"}, limit=top_k
        )
        sparse_req = AnnSearchRequest(
            [
                {k: v for k, v in zip(sparse.indices, sparse.data)}
                for sparse in embedding["sparse"]
            ],
            "sparse_embed",
            param={"metric_type": "IP"},
            limit=top_k,
        )
        res = client.hybrid_search(
            collection_name,
            [dense_req, sparse_req],
            ranker=ranker,
            output_fields=output_fields,
        )
    elif mode == "dense":
        res = client.search(
            collection_name=collection_name,
            data=[embedding["dense"][0]],
            anns_field="dense_embed",
            search_params={"metric_type": "IP"},
            limit=top_k,
            output_fields=output_fields,
        )
    else:  # sparse
        sparse_vec = [
            {
                k: v
                for k, v in zip(
                    embedding["sparse"][0].indices, embedding["sparse"][0].data
                )
            }
        ]
        res = client.search(
            collection_name=collection_name,
            data=sparse_vec,
            anns_field="sparse_embed",
            param={"metric_type": "IP"},
            limit=top_k,
            output_fields=output_fields,
        )

    results = []
    for hits in res:
        for hit in hits:
            result = {
                "id": hit["id"],
                "text": hit.get("text", ""),
                "score": hit.get("distance", 0.0),
                "metadata": hit.get("metadata", {}),
            }
            results.append(result)

    # 精排
    reranker = get_reranker()
    rerank_results = []
    rerank_result = await reranker(query, [res["text"] for res in results], top_k)
    for rerank_res in rerank_result:
        results[rerank_res.index]["score"] = rerank_res.score
        rerank_results.append(results[rerank_res.index])

    return rerank_results


async def insert_documents(
    collection_name: str,
    documents: List[Dict[str, Any]],
) -> None:
    client = get_milvus_client()
    client.insert(collection_name, documents)


async def check_health() -> bool:
    try:
        client = get_milvus_client()
        client.list_collections()
        return True
    except Exception:
        return False


async def get_collection_stats(collection_name: str) -> Dict[str, Any]:
    client = get_milvus_client()
    stats = client.get_collection_stats(collection_name)
    return stats


async def list_collections() -> List[str]:
    client = get_milvus_client()
    return client.list_collections()
