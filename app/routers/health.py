import time
from typing import Dict

from fastapi import APIRouter, status

from app.config import Settings, get_settings
from app.models import ComponentHealth, HealthResponse
from app.services.embedding import get_embedding_func
from app.services.llm import check_health as llm_check_health
from app.services.retrieval import check_health as milvus_check_health

router = APIRouter(prefix="/health", tags=["Health"])
settings: Settings = get_settings()


@router.get("", status_code=status.HTTP_200_OK)
async def health_check():
    components: Dict[str, ComponentHealth] = {}

    start = time.time()
    milvus_healthy = await milvus_check_health()
    components["milvus"] = ComponentHealth(
        status="healthy" if milvus_healthy else "unhealthy",
        latency_ms=(time.time() - start) * 1000,
    )

    start = time.time()
    try:
        get_embedding_func()
        embedding_healthy = True
    except Exception:
        embedding_healthy = False
    components["embedding_model"] = ComponentHealth(
        status="healthy" if embedding_healthy else "unhealthy",
        latency_ms=(time.time() - start) * 1000,
    )

    start = time.time()
    llm_healthy = await llm_check_health()
    components["llm_api"] = ComponentHealth(
        status="healthy" if llm_healthy else "unhealthy",
        latency_ms=(time.time() - start) * 1000,
    )

    all_healthy = all(c.status == "healthy" for c in components.values())
    overall_status = "healthy" if all_healthy else "unhealthy"

    return HealthResponse(
        status=overall_status,
        components=components,
        version="1.0.0",
    )
