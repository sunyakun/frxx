import time

from fastapi import APIRouter, Response, status

from app.models import RetrievalRequest, RetrievalResponse, RetrievalResult
from app.services.retrieval import search
from app.utils.log import get_logger

router = APIRouter(prefix="/retrieval", tags=["Retrieval"])


@router.post("", status_code=status.HTTP_200_OK)
async def retrieval_endpoint(request: RetrievalRequest, response: Response):
    try:
        start_time = time.time()

        results = await search(
            query=request.query,
            collection_name="frxx",
            top_k=request.top_k,
            mode=request.mode,
        )

        retrieval_results = [
            RetrievalResult(
                id=r.get("id", ""),
                text=r.get("text", ""),
                score=float(r.get("score", 0.0)),
                metadata=r.get("metadata"),
            )
            for r in results
        ]

        latency_ms = (time.time() - start_time) * 1000

        return RetrievalResponse(
            results=retrieval_results,
            latency_ms=latency_ms,
            total_matches=len(retrieval_results),
        )

    except Exception as e:
        get_logger().error(f"Failed to run retrieval: {e}", exc_info=e)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {
            "code": "INTERNAL_ERROR",
            "message": str(e),
        }
