import time

from fastapi import APIRouter, status

from app.models import DocumentUploadRequest, DocumentUploadResponse
from app.services.embedding import (
    chunk_text,
    create_document_id,
    create_record_id,
    encode_chunks_async,
)
from app.services.retrieval import insert_documents, list_collections

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_document(request: DocumentUploadRequest):
    try:
        start_time = time.time()

        if "frxx" not in await list_collections():
            return {
                "code": "COLLECTION_NOT_FOUND",
                "message": "Collection 'frxx' does not exist",
            }, status.HTTP_404_NOT_FOUND

        max_characters = request.chunking.max_characters or 1000
        overlap = request.chunking.overlap or 50

        chunks = chunk_text(request.content, max_characters, overlap)

        dense_embeddings, sparse_embeddings = await encode_chunks_async(
            chunks, batch_size=32
        )

        document_id = create_document_id()

        documents = []
        for idx, (chunk, dense_embed, sparse_embed) in enumerate(
            zip(chunks, dense_embeddings, sparse_embeddings)
        ):
            documents.append(
                {
                    "id": create_record_id(),
                    "element_id": f"{document_id}_{idx}",
                    "record_id": document_id,
                    "dense_embed": dense_embed.tolist(),
                    "sparse_embed": {
                        int(k): float(v)
                        for k, v in zip(sparse_embed.indices, sparse_embed.data)
                    },
                    "text": chunk,
                    "metadata": request.metadata.model_dump()
                    if request.metadata
                    else None,
                }
            )

        await insert_documents("frxx", documents)

        indexing_latency_ms = (time.time() - start_time) * 1000

        return DocumentUploadResponse(
            document_id=document_id,
            chunk_count=len(chunks),
            indexing_latency_ms=indexing_latency_ms,
            status="success",
        )

    except Exception as e:
        return {
            "code": "INTERNAL_ERROR",
            "message": str(e),
        }, status.HTTP_500_INTERNAL_SERVER_ERROR
